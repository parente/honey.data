#!/usr/bin/env python3
"""
Counts the number of times a hall effect sensor detects a magnetic field
every minute.
"""
import argparse
import datetime
import logging
import logging.handlers
import math
import os
import signal
import threading

from gpiozero import LineSensor

logger = logging.getLogger("honey.monitor")
count = 0
semaphore = threading.BoundedSemaphore(1)


class RepeatingTimer(threading.Timer):
    """Extends the standard library Timer class to support repetition of the
    wait interval.
    """

    def run(self):
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)


def configure_logging():
    """Configures logging to stdout and syslog."""
    logger.setLevel(logging.INFO)
    syslog = logging.handlers.SysLogHandler(address="/dev/log")
    syslog.setFormatter(logging.Formatter("%(name)s: %(message)s"))
    stream = logging.StreamHandler()
    stream.setFormatter(
        logging.Formatter("%(asctime)s: %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")
    )
    logger.addHandler(stream)
    logger.addHandler(syslog)


def on_magnet():
    """Increases the counter by one."""
    global count
    semaphore.acquire()
    count += 1
    semaphore.release()


def on_minute(path):
    """Appends the count for the last minute to a file on disk."""
    global count
    if count == 0:
        logger.info("No rotations in the last minute")
        return
    now = datetime.datetime.utcnow()
    with open(os.path.join(path, f"{now:%Y-%m-%d-%H}.csv"), "a") as f:
        f.writelines(f"{now:%Y-%m-%dT%H:%M:%S},{count}\n")
    logger.info("Stored %s rotations per minute in local cache", count)
    semaphore.acquire()
    count = 0
    semaphore.release()


def on_hour():
    logger.info("TODO: Send files to S3", count)


def main():
    configure_logging()

    parser = argparse.ArgumentParser(
        description="Data collection and aggregation for honey.fitness"
    )
    parser.add_argument(
        "--data-path", default="~/.honey.data/", help="Local data cache",
    )
    parser.add_argument("--gpio-pin", default=4, help="Sensor pin number")
    args = parser.parse_args()

    data_path = os.path.expanduser(args.data_path)
    os.makedirs(data_path, exist_ok=True)
    logger.info(f"Using {data_path} for local data storage")

    minute_timer = RepeatingTimer(60, on_minute, args=(data_path,))
    hour_timer = RepeatingTimer(60 * 60.0, on_hour)
    minute_timer.start()
    hour_timer.start()

    sensor = LineSensor(args.gpio_pin)
    sensor.when_line = on_magnet
    logger.info(f"Monitoring GPIO {args.gpio_pin} for rotation counts")

    logger.info("Starting data pipeline")
    try:
        signal.pause()
    except KeyboardInterrupt:
        pass
    minute_timer.cancel()
    hour_timer.cancel()
    logger.info("Stopped data pipeline")


if __name__ == "__main__":
    main()
