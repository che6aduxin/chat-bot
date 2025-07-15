import logging
import sys
from pathlib import Path

LOG_FILE_PATH = Path("logs/bot.log")
LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)  # создаём папку logs/ если нет

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger  # не дублируем обработчики

    formatter = logging.Formatter(
        fmt="%(asctime)s | [%(levelname)s] | (%(name)s) - %(message)s\n",
        datefmt="%H:%M:%S %d.%m.%Y"
    )

    # Файл
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Консоль
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger
