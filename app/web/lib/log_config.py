import logging.config

def setup_logging():
    logging.config.fileConfig('logging.conf')
    logging.debug("Logging has been configured")