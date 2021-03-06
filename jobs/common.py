import datetime
import argparse
import logging
import logging.handlers
import os


def init_logging(logger):
    """Configures logging to stdout and syslog."""
    logger.setLevel(logging.INFO)
    stream = logging.StreamHandler()
    stream.setFormatter(logging.Formatter("%(name)s: %(message)s"))
    logger.addHandler(stream)


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
    try:
        # Even if we get a partial read because the file was being written, it's still acceptable
        # because a partial ISO date will be even further in the past than the current datetime
        return datetime.datetime.fromisoformat(line)
    except ValueError:
        # Invalid file format
        return None
