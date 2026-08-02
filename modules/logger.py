import logging
import sys
from pathlib import Path

Path("data").mkdir(exist_ok=True)

logger = logging.getLogger("herbokolog")
logger.setLevel(logging.DEBUG)

if not logger.handlers:

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(
        "data/herbokolog.log",
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)