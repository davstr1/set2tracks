import logging
from logging.config import fileConfig
from config import Config
# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(Config.LOGGING_CONFIG_FILE)
logger = logging.getLogger('root')