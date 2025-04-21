import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from .. import config # Use relative import within the package

# Ensure the log directory exists (config.py already does this, but belt and suspenders)
os.makedirs(config.LOG_PATH, exist_ok=True)

# --- Logger Configuration ---
log_formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)
log_level_console = getattr(logging, config.LOG_LEVEL_CONSOLE, logging.INFO)
log_level_file = getattr(logging, config.LOG_LEVEL_FILE, logging.DEBUG)

# --- Root Logger Setup ---
# Avoid configuring the root logger directly if possible,
# instead configure specific loggers for the application.
# However, for simplicity in this setup, we'll configure a main app logger.

def setup_logger(name: str = 'trading_system', log_file: str = config.LOG_FILE_PATH) -> logging.Logger:
    """Sets up and returns a logger instance."""

    logger = logging.getLogger(name)
    # Prevent adding multiple handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG) # Set logger level to the lowest (DEBUG) to allow handlers to filter

    # --- Console Handler ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(log_level_console)
    logger.addHandler(console_handler)

    # --- File Handler ---
    # Use RotatingFileHandler to prevent log files from growing indefinitely
    # Max size: 5MB, keep 3 backup files
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(log_level_file)
    logger.addHandler(file_handler)

    logger.info(f"Logger '{name}' initialized. Console Level: {config.LOG_LEVEL_CONSOLE}, File Level: {config.LOG_LEVEL_FILE}, Log File: {log_file}")

    return logger

# --- Get the main application logger ---
# Services should import this logger instance
log = setup_logger()

# Example usage (can be removed later):
# if __name__ == '__main__':
#     log.debug("This is a debug message.")
#     log.info("This is an info message.")
#     log.warning("This is a warning message.")
#     log.error("This is an error message.")
#     log.critical("This is a critical message.")
