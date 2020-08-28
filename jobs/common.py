import datetime
import argparse
import logging
import logging.handlers
import os


def init_logging(logger):
    """Configures logging to stdout and syslog."""
    logger.setLevel(logging.INFO)
    stream = logging.StreamHandler()
    stream.setFormatter(
        logging.Formatter("%(asctime)s: %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")
    )
    logger.addHandler(stream)
    if os.path.exists("/dev/log"):
        syslog = logging.handlers.SysLogHandler(address="/dev/log")
        syslog.setFormatter(logging.Formatter("%(name)s: %(message)s"))
        logger.addHandler(syslog)


def init_local_data_path(data_path):
    """Expands and prepares the local data path."""
    data_path = os.path.expanduser(data_path)
    os.makedirs(data_path, exist_ok=True)
    return data_path


def init_argparser(description):
    """Creates an argument parser with common options."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--data-path",
        default="~/.honey.data/",
        help="Local data cache",
    )
    return parser


def write_marker(path, dt):
    """Writes a datetime at hour resolution to a marker file."""
    dt_hour = f"{dt:%Y-%m-%d-%H}"
    with open(os.path.join(path, "MARKER"), "w") as f:
        f.write(dt_hour)
    return dt_hour


def read_marker(path):
    """Reads a datetime from a marker file."""
    filename = os.path.join(path, "MARKER")
    if not os.path.exists(filename):
        return None
    with open(filename) as f:
        line = f.read()
    return datetime.datetime.fromisoformat(line)
