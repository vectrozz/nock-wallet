"""
File helper utilities for wallet operations.
"""
import os
import json
import time
from datetime import datetime
from logger import logger

# Configuration file path
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'wallet_config.json')
HISTORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'wallet_history.json')
TXS_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'txs')


def load_config():
    """Load wallet configuration from JSON file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Could not decode wallet_config.json, using defaults")
            return get_default_config()
    return get_default_config()


def get_default_config():
    """Get default configuration."""
    return {
        "grpc": {
            "type": "public",
            "customAddress": ""
        }
    }


def save_config(config):
    """Save wallet configuration to JSON file."""
    # ← UTILISE CONFIG_FILE au lieu de get_config_file_path()
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, fp=f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        
        logger.info(f"Configuration saved to {CONFIG_FILE}")
        logger.info(f"Configuration content: {config}")
        
        # Vérifie immédiatement
        with open(CONFIG_FILE, 'r') as f:
            saved = json.load(f)
            logger.info(f"Verification - file contains: {saved}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def get_tx_files_in_folder():
    """
    Get all .tx files in the txs folder with their modification times.
    
    Returns:
        dict: Dictionary mapping filename (without .tx) to modification timestamp
    """
    if not os.path.exists(TXS_FOLDER):
        logger.warning(f"Transaction folder not found: {TXS_FOLDER}")
        return {}
    
    tx_files = {}
    try:
        for filename in os.listdir(TXS_FOLDER):
            if filename.endswith('.tx'):
                filepath = os.path.join(TXS_FOLDER, filename)
                mtime = os.path.getmtime(filepath)
                # Store without .tx extension
                tx_name = filename[:-3]
                tx_files[tx_name] = mtime
                logger.debug(f"Found tx file: {tx_name} (modified: {mtime})")
    except Exception as e:
        logger.error(f"Error reading tx folder: {str(e)}")
    
    return tx_files


def verify_transaction_file(tx_name, old_tx_files):
    """
    Verify that a transaction file was created and is recent.
    
    Args:
        tx_name: Name of the transaction (without .tx extension)
        old_tx_files: Dictionary of tx files before creation
    
    Returns:
        bool: True if file exists and is new/recent
    """
    current_tx_files = get_tx_files_in_folder()
    
    # Check if file exists
    if tx_name not in current_tx_files:
        logger.warning(f"Transaction file not found: {tx_name}.tx")
        return False
    
    # Check if it's a new file (wasn't in old_tx_files)
    if tx_name not in old_tx_files:
        logger.info(f"Transaction file verified as new: {tx_name}.tx")
        return True
    
    # Check if file was modified (timestamp changed)
    if current_tx_files[tx_name] > old_tx_files[tx_name]:
        logger.info(f"Transaction file verified as updated: {tx_name}.tx")
        return True
    
    logger.warning(f"Transaction file exists but wasn't modified: {tx_name}.tx")
    return False


def load_transaction_history():
    """Load transaction history from JSON file."""
    if not os.path.exists(HISTORY_FILE):
        logger.info(f"Transaction history file not found: {HISTORY_FILE}")
        return []
    
    try:
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
        logger.info(f"Loaded {len(history)} transactions from history file")
        return history
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing transaction history JSON: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error loading transaction history: {str(e)}")
        return []


def save_transaction_history(history):
    """Save transaction history to JSON file."""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
        logger.info(f"Transaction history saved: {len(history)} transactions")
        return True
    except Exception as e:
        logger.error(f"Error saving transaction history: {str(e)}")
        return False


def add_transaction_to_history(tx_hash, recipient, amount_nock, amount_nick, fee_nick, notes_used, signer, status='created'):
    """
    Add a transaction to the history file.
    
    Args:
        tx_hash: Transaction hash/name
        recipient: Recipient address
        amount_nock: Amount in NOCK
        amount_nick: Amount in NICK
        fee_nick: Fee in NICK
        notes_used: Number of notes used
        signer: Signer's public key
        status: Transaction status (created, signed, sent)
    
    Returns:
        dict: The transaction entry that was added
    """
    history = load_transaction_history()
    
    transaction = {
        "tx_hash": tx_hash,
        "recipient": recipient,
        "amount_nock": amount_nock,
        "amount_nick": amount_nick,
        "fee_nick": fee_nick,
        "notes_used": notes_used,
        "signer": signer,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    history.append(transaction)
    save_transaction_history(history)
    
    logger.info(f"Transaction added to history: {tx_hash[:20]}... status={status}")
    
    return transaction


def update_transaction_status(tx_hash, new_status):
    """
    Update the status of a transaction in the history.
    
    Args:
        tx_hash: Transaction hash/name
        new_status: New status (signed, sent, confirmed, etc.)
    
    Returns:
        bool: True if updated successfully
    """
    history = load_transaction_history()
    
    updated = False
    for tx in history:
        if tx.get('tx_hash') == tx_hash:
            tx['status'] = new_status
            tx['last_updated'] = datetime.now().isoformat()
            updated = True
            logger.info(f"Transaction status updated: {tx_hash[:20]}... -> {new_status}")
            break
    
    if updated:
        save_transaction_history(history)
        return True
    else:
        logger.warning(f"Transaction not found in history: {tx_hash}")
        return False


def ensure_folder_exists(folder_path):
    """Ensure a folder exists, create it if it doesn't."""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        logger.info(f"Created folder: {folder_path}")
    return folder_path


# Ensure txs folder exists
ensure_folder_exists(TXS_FOLDER)