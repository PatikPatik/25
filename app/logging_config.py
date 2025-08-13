from __future__ import annotations
import logging, os
from pythonjsonlogger import jsonlogger

def setup_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    root = logging.getLogger()
    root.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s'))
    root.handlers.clear()
    root.addHandler(handler)
