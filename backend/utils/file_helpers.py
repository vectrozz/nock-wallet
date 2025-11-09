"""
File management utilities.
"""
import json
import os
from datetime import datetime
from config import TX_FOLDER, HISTORY_FILE, CONFIG_FILE
from logger import logger


def save_transaction(tx_data, filename=None):
    """
    Save transaction data to a file.
    
    Args:
        tx_data: Transaction data dict
        filename: Optional filename (auto-generated if None)
    
    Returns:
        str: Path to saved file
    """
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"tx_{timestamp}.json"
    
    filepath = os.path.join(TX_FOLDER, filename)
    
    with open(filepath, 'w') as f:
        json.dump(tx_data, f, indent=2)
    
    logger.info(f"Transaction saved to {filepath}")
    return filepath


def load_history():
    """
    Load transaction history from file.
    
    Returns:
        list: Transaction history
    """
    if not os.path.exists(HISTORY_FILE):
        return []
    
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading history: {e}")
        return []


def save_history(history):
    """
    Save transaction history to file.
    
    Args:
        history: List of transactions
    """
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
        logger.info(f"History saved ({len(history)} transactions)")
    except Exception as e:
        logger.error(f"Error saving history: {e}")


def load_config():
    """
    Load wallet configuration from file.
    
    Returns:
        dict: Configuration dict
    """
    if not os.path.exists(CONFIG_FILE):
        # Default config
        return {
            'client_type': 'private',
            'private_grpc_server_port': 5555
        }
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {
            'client_type': 'private',
            'private_grpc_server_port': 5555
        }


def save_config(config):
    """
    Save wallet configuration to file.
    
    Args:
        config: Configuration dict
    """
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info("Configuration saved")
    except Exception as e:
        logger.error(f"Error saving config: {e}")