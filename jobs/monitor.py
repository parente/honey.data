#!/usr/bin/env python3
"""
Counts the number of times a hall effect sensor detects a magnetic field
every minute and writes those counts to a hourly CSVs on local disk.
"""
import datetime
import logging
import math
import os
import signal
import threading

from gpiozero import LineSensor

from . import common

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


def on_magnet():
    """Increases the counter by one."""
    global count
    semaphore.acquire()
    count += 1
    semaphore.release()


def on_save(path):
    """Appends the count for the last minute to a file on disk."""
    global count
    now = datetime.datetime.utcnow()

    marker = common.write_marker(path, now)
    logger.debug("Updated local cache marker to %s", marker)

    if count == 0:
        logger.debug("Skipping save: no rotations in the last minute")
        return

    with open(os.path.join(path, f"{marker}.csv"), "a") as f:
        f.writelines(f"{now:%Y-%m-%dT%H:%M:%SZ},{count}\n")

    logger.info("Stored %s rotations per minute in local cache", count)
    semaphore.acquire()
    count = 0
    semaphore.release()


def main():
    common.init_logging(logger)

    parser = common.init_argparser("Data collection for honey.fitness")
    parser.add_argument("--gpio-pin", default=4, help="Sensor pin number")
    args = parser.parse_args()

    data_path = common.init_local_data_path(args.data_path)
    logger.info(f"Using {data_path} for local data storage")

    minute_timer = RepeatingTimer(60, on_save, args=(data_path,))
    minute_timer.start()

    sensor = LineSensor(args.gpio_pin)
    sensor.when_line = on_magnet
    logger.info(f"Monitoring GPIO {args.gpio_pin} for rotation counts")

    logger.info("Starting monitor")
    try:
        signal.pause()
    except KeyboardInterrupt:
        pass
    minute_timer.cancel()
    logger.info("Stopped monitor")


if __name__ == "__main__":
    main()
