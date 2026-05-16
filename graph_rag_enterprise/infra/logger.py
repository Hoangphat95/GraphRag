# infra/logger.py
import logging

logging.basicConfig(level=logging.INFO)

def log(msg):
    logging.info(msg)