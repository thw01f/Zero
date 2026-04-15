"""Structured logging utilities."""
import logging
import json
import time

class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'ts': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'level': record.levelname,
            'module': record.module,
            'msg': record.getMessage(),
        }
        if record.exc_info:
            log_entry['exc'] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(StructuredFormatter())
        logger.addHandler(h)
        logger.setLevel(logging.INFO)
    return logger
