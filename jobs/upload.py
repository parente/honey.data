#!/usr/bin/env python3
"""
Counts the number of times a hall effect sensor detects a magnetic field
every minute and writes those counts to a hourly CSVs on local disk.
"""
import argparse
import datetime
import logging
import os
import time

import boto3

from botocore.exceptions import ClientError

from . import common

logger = logging.getLogger("honey.upload")


def on_upload(path, bucket, s3_client):
    marker = common.read_marker(path)
    if marker is None:
        logger.info("Skipping upload: no local cache marker")
        return

    for filename in glob.glob(os.path.join(path, "*.csv")):
        datetime, _ = filename.split(os.path.extsep)
        file_dt = datetime.datetime.fromisoformat(datetime)
        if file_dt < marker:
            key = f"year={file_dt:%Y}/month={file_dt:%m}/day={file_dt:%d}/{filename}"
            try:
                response = s3_client.upload_file(filename, bucket, key)
            except ClientError as e:
                logger.error(e)
            else:
                os.remove(filename)
                logger.info("Migrated %s to s3://%s/%s", filename, bucket, key)
        else:
            logger.info("Skipped %s >= %s", filename, marker)


def main():
    common.init_logging(logger)

    parser = common.init_argparser("Data upload for honey.fitness")
    parser.add_argument("--s3-bucket", default="honey-data", help="Remote S3 bucket")
    args = parser.parse_args()

    s3_client = boto3.client("s3", region_name="us-east-1")
    data_path = common.init_local_data_path(args.data_path)
    logger.info(f"Using %s for local data storage", data_path)

    logger.info("Starting uploader")
    while 1:
        on_upload(data_path, args.s3_bucket, s3_client)
        time.sleep(60 * 5)
    logger.info("Stopped uploader")


if __name__ == "__main__":
    main()
