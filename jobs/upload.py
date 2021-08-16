#!/usr/bin/env python3
"""
Uploads CSV files produced by jobs.monitor to an S3 bucket/prefix partitioned by year, month, and
day for later processing.

Assumes AWS credentials and region are configured in any standard, boto supported manner (e.g., env
vars, ~/.aws/credentials).
"""
import argparse
import datetime
import glob
import logging
import os
import tempfile
import time

import boto3
import safer

from botocore.exceptions import ClientError

from . import common

logger = logging.getLogger("honey.upload")


def fix_nulls(filepath):
    """Removes null characters from the given file and overwrites it atomically.

    When the device get unplugged mid-write to a CSV, null characters get introduced, corrupt
    the CSV, and cause later Athena queries to fail. This function makes a basic attempt at turning
    the CSV valid again.
    """
    with safer.open(filepath, "rb") as fr:
        content = fr.read().replace(b"\x00", b"")
        with safer.open(filepath, "wb") as fw:
            fw.write(content)
    return filepath


def on_upload(path, bucket, prefix, s3_client):
    """Uploads past hour CSV files to partition prefixes in the configured bucket."""
    marker = common.read_marker(path)
    if marker is None:
        logger.warning("Skipping upload: no local cache marker")
        return 0

    logger.info("Starting file upload")
    upload_count = 0
    for filepath in glob.glob(os.path.join(path, "*.csv")):
        filename = os.path.basename(filepath)
        str_dt, _ = filename.split(os.path.extsep)
        file_dt = datetime.datetime.fromisoformat(str_dt)
        if file_dt < marker:
            filepath = fix_nulls(filepath)
            key = f"{prefix}/year={file_dt:%Y}/month={file_dt:%m}/day={file_dt:%d}/{filename}"
            try:
                response = s3_client.upload_file(filepath, bucket, key)
            except ClientError as e:
                logger.error(e)
            else:
                upload_count += 1
                os.remove(filepath)
                logger.info("Migrated %s to s3://%s/%s", filename, bucket, key)
        else:
            logger.info("Skipped %s >= %s", filename, marker)
    logger.info("Completed file upload")
    return upload_count


def query(query, database, workgroup, athena_client, max_checks=30):
    """Executes an Athena query, waits for success or failure, and returns the first page
    of the query results.

    Waits up to max_checks * 10 seconds for the query to complete before raising.
    """
    resp = athena_client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": database},
        WorkGroup=workgroup,
    )
    qid = resp["QueryExecutionId"]
    for i in range(max_checks):
        resp = athena_client.get_query_execution(QueryExecutionId=qid)
        state = resp["QueryExecution"]["Status"]["State"]
        if state == "SUCCEEDED":
            return qid
        elif state == "FAILED":
            raise RuntimeError(f"Failed query execution: {query}")
        # Continue to wait
        time.sleep(10)
    else:
        raise TimeoutError("Reached max_checks")


def publish(
    results_bucket,
    results_prefix,
    results_id,
    public_bucket,
    public_key,
    s3_client,
):
    """Copies Athena results to the public bucket for client use."""
    return s3_client.copy_object(
        CopySource=f"{results_bucket}/{results_prefix}/{results_id}.csv",
        Bucket=public_bucket,
        Key=public_key,
        ACL="public-read",
    )


def on_aggregate(
    results_bucket,
    results_prefix,
    public_bucket,
    athena_database,
    athena_workgroup,
    s3_client,
    athena_client,
):
    """Executes Athena queries to aggregate raw data for web site display."""
    logger.info("Starting data aggregation")
    query(
        "msck repair table incoming_rotations",
        athena_database,
        athena_workgroup,
        athena_client,
    )
    logger.info("Repaired Athena partitions")

    # Total number of rotations since collection start
    results_id = query(
        "select sum(rotations) total from incoming_rotations",
        athena_database,
        athena_workgroup,
        athena_client,
    )
    publish(
        results_bucket,
        results_prefix,
        results_id,
        public_bucket,
        "total-rotations.csv",
        s3_client,
    )
    logger.info("Computed total rotations: %s", results_id)

    # Total rotations prior to this time 7 days ago
    results_id = query(
        """
        select sum(rotations) as prior_rotations
        from incoming_rotations
        where from_iso8601_timestamp(datetime) < (current_date - interval '7' day)
        """,
        athena_database,
        athena_workgroup,
        athena_client,
    )
    publish(
        results_bucket,
        results_prefix,
        results_id,
        public_bucket,
        "prior-7-day-window.csv",
        s3_client,
    )
    logger.info("Computed rotations prior to 7 days ago: %s", results_id)

    # Cumulative rotations per hour from this time 7 days ago til now
    results_id = query(
        """
        select
            sum(rotations) as sum_rotations,
            to_iso8601(date_trunc('hour', from_iso8601_timestamp(datetime))) as datetime_hour,
            sum(sum(rotations)) over (
                order by date_trunc('hour', from_iso8601_timestamp(datetime)) asc 
                rows between unbounded preceding and current row
            ) as cumsum_rotations
        from incoming_rotations
        where 
            year >= year(current_date)-1 and
            from_iso8601_timestamp(datetime) >= (current_date - interval '7' day)
        group by date_trunc('hour', from_iso8601_timestamp(datetime))
        order by datetime_hour
        """,
        athena_database,
        athena_workgroup,
        athena_client,
    )
    publish(
        results_bucket,
        results_prefix,
        results_id,
        public_bucket,
        "7-day-window.csv",
        s3_client,
    )
    logger.info("Computed hourly rotations for the past 7 days: %s", results_id)

    # Rotations per day for the last year
    results_id = query(
        """
        select
            sum(rotations) as value,
            date(date_trunc('day', from_iso8601_timestamp(datetime) - interval '16' hour)) + interval '1' day as day
        from incoming_rotations
        where year >= year(current_date)-1
        group by date_trunc('day', from_iso8601_timestamp(datetime) - interval '16' hour)
        order by day
        """,
        athena_database,
        athena_workgroup,
        athena_client,
    )
    publish(
        results_bucket,
        results_prefix,
        results_id,
        public_bucket,
        "1-year-window.csv",
        s3_client,
    )
    logger.info("Computed daily rotations for the past year: %s", results_id)
    logger.info("Completed data aggregation")


def main():
    common.init_logging(logger)

    parser = common.init_argparser("Data upload to S3 for honey.fitness")
    parser.add_argument("--s3-bucket", default="honey-data", help="S3 bucket")
    parser.add_argument(
        "--s3-public-bucket", default="honey-data-public", help="Public S3 bucket"
    )
    parser.add_argument(
        "--s3-incoming-prefix",
        default="incoming-rotations",
        help="S3 key prefix for raw data",
    )
    parser.add_argument(
        "--s3-results-prefix",
        default="athena-results",
        help="S3 key prefix for Athena results",
    )
    parser.add_argument(
        "--athena-database",
        default="honey_data",
        help="Athena database name",
    )
    parser.add_argument(
        "--athena-workgroup",
        default="honey-data",
        help="Athea query execution workgroup",
    )
    args = parser.parse_args()

    s3_client = boto3.client("s3")
    athena_client = boto3.client("athena")
    data_path = common.init_local_data_path(args.data_path)
    logger.info(f"Using %s for local data storage", data_path)

    # Always force aggregation on startup in case of prior error
    startup = True
    logger.info("Starting uploader")
    while 1:
        upload_count = on_upload(
            data_path,
            args.s3_bucket,
            args.s3_incoming_prefix,
            s3_client,
        )
        if (upload_count > 0) or startup:
            # Aggregate only when we send new data, otherwise it's a no-op
            on_aggregate(
                args.s3_bucket,
                args.s3_results_prefix,
                args.s3_public_bucket,
                args.athena_database,
                args.athena_workgroup,
                s3_client,
                athena_client,
            )
            startup = False
        time.sleep(60 * 10)
    logger.info("Stopped uploader")


if __name__ == "__main__":
    main()
