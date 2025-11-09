"""
Logging configuration for the wallet backend.
"""
import logging
import sys

def setup_logger(name='__main__', level=logging.DEBUG):
    """
    Configure and return a logger instance.
    
    Args:
        name: Logger name
        level: Logging level (default: DEBUG)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    
    return logger

# Default logger instance
logger = setup_logger()