import logging
import sys
from config import config

from .text_messages import EngMsg
from .llm_exceptions import InvalidCollectionName, PdfFileInvalidFormat, DatabaseError, InvalidCollection
from .custom_error import CustomError


level = logging.DEBUG if config.DEBUG else logging.INFO

logging.basicConfig(
    stream=sys.stdout,
    level=level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

root_logger = logging.getLogger()
for handler in root_logger.handlers:
    handler.setLevel(level)

__all__ = [
    'EngMsg',
    'InvalidCollectionName',
    'PdfFileInvalidFormat',
    'DatabaseError',
    'InvalidCollection',
    'CustomError'
]