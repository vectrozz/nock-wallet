"""
Transaction service - handles transaction creation and broadcasting.
"""
import os
import subprocess
from datetime import datetime
from werkzeug.utils import secure_filename
from utils.command import execute_wallet_command
from utils.file_helpers import save_transaction, load_history, save_history
from config import TX_FOLDER, UPLOAD_FOLDER
from logger import logger


def create_transaction(recipient, amount_nock, notes=None, version=1):
    """
    Create a new transaction.
    
    Args:
        recipient: Recipient address
        amount_nock: Amount in nock
        notes: Optional list of note numbers to use
        version: Transaction version (0 or 1)
    
    Returns:
        dict: {
            "success": bool,
            "tx_file": str (optional),
            "output": str (optional),
            "error": str (optional)
        }
    """
    try:
        logger.info(f"Creating transaction: {amount_nock} nock to {recipient[:50]}... (version {version})")
        
        # Build command
        cmd = ['create-transaction', recipient, str(amount_nock), '--version', str(version)]
        
        # Add notes if specified
        if notes and len(notes) > 0:
            notes_str = ','.join(str(n) for n in notes)
            cmd.extend(['--notes', notes_str])
            logger.info(f"Using notes: {notes_str}")
        
        # Execute command
        result = execute_wallet_command(cmd)
        
        if result.returncode != 0:
            logger.error(f"Transaction creation failed: {result.stderr}")
            return {
                "success": False,
                "error": result.stderr or "Transaction creation failed"
            }
        
        # Find the transaction file
        tx_files = sorted(
            [f for f in os.listdir(TX_FOLDER) if f.startswith('tx_') and f.endswith('.json')],
            key=lambda x: os.path.getmtime(os.path.join(TX_FOLDER, x)),
            reverse=True
        )
        
        if not tx_files:
            logger.error("Transaction file not found after creation")
            return {
                "success": False,
                "error": "Transaction file not found"
            }
        
        tx_file = tx_files[0]
        logger.info(f"Transaction created: {tx_file}")
        
        # Save to history
        history = load_history()
        history.append({
            "timestamp": datetime.now().isoformat(),
            "type": "create",
            "recipient": recipient,
            "amount_nock": amount_nock,
            "version": version,
            "notes": notes,
            "tx_file": tx_file,
            "status": "created"
        })
        save_history(history)
        
        return {
            "success": True,
            "tx_file": tx_file,
            "output": result.stdout
        }
        
    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


def broadcast_transaction(tx_file):
    """
    Broadcast a transaction.
    
    Args:
        tx_file: Path to transaction file
    
    Returns:
        dict: {
            "success": bool,
            "output": str (optional),
            "error": str (optional)
        }
    """
    try:
        logger.info(f"Broadcasting transaction: {tx_file}")
        
        # Execute broadcast command
        result = execute_wallet_command(['broadcast', tx_file])
        
        if result.returncode != 0:
            logger.error(f"Broadcast failed: {result.stderr}")
            return {
                "success": False,
                "error": result.stderr or "Broadcast failed"
            }
        
        logger.info("Transaction broadcasted successfully")
        
        # Update history
        history = load_history()
        for item in history:
            if item.get('tx_file') == os.path.basename(tx_file):
                item['status'] = 'broadcasted'
                item['broadcast_timestamp'] = datetime.now().isoformat()
                break
        save_history(history)
        
        return {
            "success": True,
            "output": result.stdout
        }
        
    except Exception as e:
        logger.error(f"Error broadcasting transaction: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


def import_keys_service(file_path=None, seedphrase=None, version=None):
    """
    Import keys from file or seedphrase.
    
    Args:
        file_path: Path to keys file (for file import)
        seedphrase: Seedphrase string (for seedphrase import)
        version: Version for seedphrase import
    
    Returns:
        dict: {
            "success": bool,
            "output": str (optional),
            "error": str (optional)
        }
    """
    try:
        if file_path:
            # Import from file
            logger.info(f"Importing keys from file: {file_path}")
            
            result = execute_wallet_command(['import-keys', file_path])
            
            if result.returncode != 0:
                logger.error(f"Import failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr or "Import failed"
                }
            
            logger.info("Keys imported successfully from file")
            return {
                "success": True,
                "output": result.stdout
            }
            
        elif seedphrase and version is not None:
            # Import from seedphrase
            logger.info(f"Importing keys from seedphrase (version {version})")
            
            result = execute_wallet_command([
                'import-from-seedphrase',
                seedphrase,
                '--version',
                str(version)
            ])
            
            if result.returncode != 0:
                logger.error(f"Import from seedphrase failed: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr or "Import from seedphrase failed"
                }
            
            logger.info("Keys imported successfully from seedphrase")
            return {
                "success": True,
                "output": result.stdout
            }
        else:
            return {
                "success": False,
                "error": "Either file_path or (seedphrase + version) must be provided"
            }
        
    except Exception as e:
        logger.error(f"Error importing keys: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }