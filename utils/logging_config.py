"""
Centralized logging configuration for Stalker 2 Mod Manager
"""

import logging
import os
import sys
from pathlib import Path
import config


def setup_logging(log_level=None):
    """
    Setup centralized logging configuration
    
    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                  If None, uses INFO as default
    """
    # Determine log level
    if log_level is None:
        # Check environment variable first
        log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Validate log level
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if log_level not in valid_levels:
        log_level = 'INFO'
    
    # Create logs directory
    log_dir = Path(config.DEFAULT_LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Define log file path
    log_file = log_dir / "stalker2_mod_manager.log"
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Configure root logger
    root_logger.setLevel(getattr(logging, log_level))
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # File handler (detailed logging)
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler (configurable level)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # Log startup information
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")
    
    return logger


def get_logger(name):
    """
    Get a logger instance with the specified name
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Module-level setup for backward compatibility
def init_logging():
    """Initialize logging with default settings"""
    return setup_logging()