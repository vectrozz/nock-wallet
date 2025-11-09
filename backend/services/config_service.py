"""
Configuration service - handles wallet configuration.
"""
from utils.file_helpers import load_config, save_config
from logger import logger


def get_config():
    """
    Get current wallet configuration.
    
    Returns:
        dict: Configuration dictionary
    """
    return load_config()


def update_config(new_config):
    """
    Update wallet configuration.
    
    Args:
        new_config: New configuration dict
    
    Returns:
        dict: {
            "success": bool,
            "config": dict (optional),
            "error": str (optional)
        }
    """
    try:
        # Load current config
        config = load_config()
        
        # Update with new values
        config.update(new_config)
        
        # Save
        save_config(config)
        
        logger.info("Configuration updated successfully")
        return {
            "success": True,
            "config": config
        }
        
    except Exception as e:
        logger.error(f"Error updating config: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }