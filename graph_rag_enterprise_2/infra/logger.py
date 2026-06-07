import logging
import json
import sys

class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {
            'ts': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'name': record.name,
            'msg': record.getMessage()
        }
        if record.exc_info:
            data['exc'] = self.formatException(record.exc_info)
        return json.dumps(data)

def setup(level=logging.INFO):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        root.addHandler(handler)
# infra/logger.py
import logging

logging.basicConfig(level=logging.INFO)

def log(msg):
    logging.info(msg)