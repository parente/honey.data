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
import time

import boto3

from botocore.exceptions import ClientError

from . import common

logger = logging.getLogger("honey.upload")


def on_upload(path, bucket, prefix, s3_client):
    marker = common.read_marker(path)
    if marker is None:
        logger.warning("Skipping upload: no local cache marker")
        return

    logger.info("Starting file upload job")
    for filepath in glob.glob(os.path.join(path, "*.csv")):
        filename = os.path.basename(filepath)
        str_dt, _ = filename.split(os.path.extsep)
        file_dt = datetime.datetime.fromisoformat(str_dt)
        if file_dt < marker:
            key = f"{prefix}/year={file_dt:%Y}/month={file_dt:%m}/day={file_dt:%d}/{filename}"
            try:
                response = s3_client.upload_file(filepath, bucket, key)
            except ClientError as e:
                logger.error(e)
            else:
                os.remove(filepath)
                logger.info("Migrated %s to s3://%s/%s", filename, bucket, key)
        else:
            logger.info("Skipped %s >= %s", filename, marker)
    logger.info("Completed file upload job")


def main():
    common.init_logging(logger)

    parser = common.init_argparser("Data upload to S3 for honey.fitness")
    parser.add_argument("--s3-bucket", default="honey-data", help="S3 bucket")
    parser.add_argument(
        "--s3-prefix", default="incoming-rotations", help="S3 key prefix"
    )
    args = parser.parse_args()

    s3_client = boto3.client("s3")
    data_path = common.init_local_data_path(args.data_path)
    logger.info(f"Using %s for local data storage", data_path)

    logger.info("Starting uploader")
    while 1:
        on_upload(data_path, args.s3_bucket, args.s3_prefix, s3_client)
        time.sleep(60 * 5)
    logger.info("Stopped uploader")


if __name__ == "__main__":
    main()
