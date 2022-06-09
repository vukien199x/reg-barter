import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
from coloredlogs import ColoredFormatter

from src import config
from src.verify import VerifyBarter


def setup_logging(module: str, level: str, log_dir: str = config.LOG_DIR):
    logger = logging.getLogger(module)
    logger.setLevel(level)
    handler = RotatingFileHandler(f'{log_dir}/.{module}.log', maxBytes=20 * 1024 * 1024, backupCount=10)
    fmt_str = '[%(asctime)s] %(levelname)s [%(name)s.%(module)s.%(funcName)s:%(lineno)d] %(message)s'
    date_fmt_str = '%Y-%m-%dT%H:%M:%S'
    formatter = logging.Formatter(fmt_str, datefmt=date_fmt_str)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    formatter = ColoredFormatter(fmt_str, date_fmt_str)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Verify acc barter')
    parser.add_argument('--level', type=str, default='DEBUG', help='logging level')
    parser.add_argument('--folder', type=str, required=True, help="Path of folder image,video, json config")
    args = parser.parse_args()
    setup_logging("bt", args.level)
    VerifyBarter(args.folder).verify()
