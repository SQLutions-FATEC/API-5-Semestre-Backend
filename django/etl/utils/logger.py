import logging
import os
from datetime import datetime


def get_logger(name: str) -> logging.Logger:
    os.makedirs("logs", exist_ok=True)
    log_file = f"logs/etl_{datetime.now().strftime('%Y%m%d')}.log"

    logger = logging.getLogger(name)

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger