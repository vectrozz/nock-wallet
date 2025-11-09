"""
Transaction service - handles transaction creation, signing, and broadcasting.
"""
import os
import subprocess
import re
import time
from datetime import datetime
from utils.grpc import get_grpc_args
from utils.file_helpers import (
    get_tx_files_in_folder,
    verify_transaction_file,
    add_transaction_to_history,
    update_transaction_status,
    load_transaction_history
)
from logger import logger

# Check if running in Docker
NOCKCHAIN_WALLET_HOST = os.getenv('NOCKCHAIN_WALLET_HOST')
if NOCKCHAIN_WALLET_HOST:
    WALLET_CMD_PREFIX = ['docker', 'exec', 'nockchain-wallet-service', 'nockchain-wallet']
    logger.info(f"Running in Docker mode - wallet container: {NOCKCHAIN_WALLET_HOST}")
else:
    WALLET_CMD_PREFIX = ['nockchain-wallet']
    logger.info("Running in local mode - using local nockchain-wallet")


def get_wallet_public_key():
    """Get wallet's public key for transaction history."""
    try:
        cmd = WALLET_CMD_PREFIX.copy()
        cmd.extend(get_grpc_args())
        cmd.append("list-active-addresses")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            bufsize=-1
        )
        
        if result.returncode != 0:
            return None
        
        output = result.stdout
        
        signing_section = re.search(
            r'Addresses -- Signing(.*?)(?:Addresses -- Watch only|$)',
            output,
            re.DOTALL
        )
        
        if signing_section:
            address_match = re.search(r'- Address:\s*([^\n]+)', signing_section.group(1))
            if address_match:
                return address_match.group(1).strip()
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting wallet public key: {str(e)}")
        return None


def create_transaction(recipient, amount_nock, fee_nick=10, selected_note_names=None, use_all_funds=False):
    """Create a new transaction."""
    try:
        # Get wallet public key for history
        signer_public_key = get_wallet_public_key()
        if not signer_public_key:
            logger.warning("Could not get wallet public key, using 'Unknown'")
            signer_public_key = "Unknown"
        
        # Convert Nock to Nick
        amount_nock = float(amount_nock)
        amount_nick = int(amount_nock * 65536)
        fee_nick = int(fee_nick)
        
        # Get all notes
        from services.wallet_service import get_wallet_balance
        balance_data = get_wallet_balance()
        
        if balance_data.get('error'):
            return {"success": False, "error": balance_data.get('error')}
        
        notes = balance_data['notes']
        
        # Select notes
        selected_notes = []
        accumulated = 0
        
        if selected_note_names:
            for note in notes:
                if note['name'] in selected_note_names:
                    selected_notes.append(note)
                    accumulated += note['value']
            
            if not selected_notes:
                return {"success": False, "error": "No valid notes found from selection."}
            
            if use_all_funds:
                amount_nick = accumulated - fee_nick
                if amount_nick <= 0:
                    return {
                        "success": False,
                        "error": f"Selected notes ({accumulated} nick) don't have enough to cover the fee ({fee_nick} nick)."
                    }
                logger.info(f"Using all funds from selected notes: {accumulated} nick - {fee_nick} fee = {amount_nick} nick to send")
                amount_nock = amount_nick / 65536
                logger.info(f"Adjusted amount: {amount_nock:.4f} NOCK ({amount_nick} nick)")
        else:
            total_needed = amount_nick + fee_nick
            sorted_notes = sorted(notes, key=lambda x: x['value'], reverse=True)
            
            for note in sorted_notes:
                if accumulated >= total_needed:
                    break
                selected_notes.append(note)
                accumulated += note['value']
            
            if accumulated < total_needed:
                return {
                    "success": False,
                    "error": f"Insufficient funds. Need {total_needed} nick, have {accumulated} nick."
                }
        
        # Build names parameter
        names_parts = []
        for note in selected_notes:
            note_name = note['name']
            names_parts.append(f"[{note_name}]")
        
        names_string = ",".join(names_parts)
        
        logger.info(f"Selected {len(selected_notes)} notes:")
        for i, note in enumerate(selected_notes):
            note_nock = note['value'] / 65536
            logger.info(f"  - Note #{i+1}: {note_nock:.4f} NOCK ({note['value']} NICK)")
            logger.info(f"    Name: {note['name'][:50]}...")
        logger.info(f"Total notes value: {accumulated} NICK")
        logger.info(f"Amount to send: {amount_nick} NICK (after {fee_nick} fee)")
        logger.info(f"Names string: {names_string[:200]}...")
        
        # Get old tx files before creating
        old_tx_files = get_tx_files_in_folder()
        logger.info(f"Existing transaction files before creation: {len(old_tx_files)}")
        
        # Build command with gRPC args from config
        cmd = WALLET_CMD_PREFIX.copy()
        cmd.extend(get_grpc_args())
        cmd.extend([
            "create-tx",
            "--names", names_string,
            "--recipients", f"[1 {recipient}]",
            "--gifts", str(amount_nick),
            "--fee", str(fee_nick)
        ])
        
        logger.info("Creating transaction...")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
            bufsize=-1
        )
        
        output = result.stdout
        logger.info("=== FULL CREATE-TX OUTPUT ===")
        logger.info(output)
        logger.info("=== END OUTPUT ===")
        
        if result.stderr:
            logger.info("=== CREATE-TX STDERR ===")
            logger.info(result.stderr)
            logger.info("=== END STDERR ===")
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": f"Transaction creation failed: {result.stderr or result.stdout}",
                "return_code": result.returncode
            }
        
        # Check what files exist after command
        current_tx_files = get_tx_files_in_folder()
        logger.info(f"TX files after create-tx: {list(current_tx_files.keys())}")
        
        # Extract transaction name
        patterns = [
            r"Name: ([^\n]+)",
            r"Transaction: ([^\n]+)",
            r"Hash: ([^\n]+)",
            r"Created: ([^\n]+)",
            r"File: ([^\n]+)",
            r"([A-Za-z0-9]{50,})"
        ]
        
        tx_name = None
        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                tx_name = match.group(1).strip()
                logger.info(f"Found tx name with pattern '{pattern}': {tx_name}")
                break
        
        if not tx_name:
            logger.error("Could not extract transaction name")
            return {
                "success": False,
                "error": "Failed to extract transaction name from output.",
                "debug_output": output,
                "debug_stderr": result.stderr,
                "tx_files_after": list(current_tx_files.keys())
            }
        
        logger.info(f"Transaction name extracted: {tx_name}")
        
        # Verify file
        file_verified = verify_transaction_file(tx_name, old_tx_files)
        
        if not file_verified:
            logger.warning(f"Transaction file {tx_name}.tx not found or not recent")
            return {
                "success": False,
                "error": "Transaction was created but file verification failed.",
                "transaction_name": tx_name
            }
        
        # Add to history
        transaction = add_transaction_to_history(
            tx_hash=tx_name,
            recipient=recipient,
            amount_nock=amount_nock,
            amount_nick=amount_nick,
            fee_nick=fee_nick,
            notes_used=len(selected_notes),
            signer=signer_public_key,
            status='created'
        )
        
        return {
            "success": True,
            "transaction_hash": tx_name,
            "transaction_name": tx_name,
            "output": output,
            "notes_used": len(selected_notes),
            "amount_nick": amount_nick,
            "fee_nick": fee_nick,
            "file_verified": file_verified,
            "history_entry": transaction
        }
        
    except Exception as e:
        logger.error(f"Error creating transaction: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


def show_transaction(tx_name):
    """Show transaction details."""
    try:
        # Build command with gRPC args from config
        cmd = WALLET_CMD_PREFIX.copy()
        cmd.extend(get_grpc_args())
        cmd.extend(["show-tx", f"txs/{tx_name}.tx"])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            bufsize=-1
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": "Error showing transaction.",
                "details": result.stderr
            }
        
        return {
            "success": True,
            "details": result.stdout
        }
        
    except Exception as e:
        logger.error(f"Error showing transaction: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def sign_transaction(tx_name):
    """Sign a transaction."""
    try:
        # Build command with gRPC args from config
        cmd = WALLET_CMD_PREFIX.copy()
        cmd.extend(get_grpc_args())
        cmd.extend(["sign-tx", f"txs/{tx_name}.tx"])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            bufsize=-1
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": "Error signing transaction.",
                "details": result.stderr
            }
        
        logger.info("Sign transaction output: %s", result.stdout)
        
        # Update status in history
        update_transaction_status(tx_name, 'signed')
        
        return {
            "success": True,
            "message": "Transaction signed successfully.",
            "output": result.stdout
        }
        
    except Exception as e:
        logger.error(f"Error signing transaction: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def send_transaction(tx_name):
    """Send a transaction."""
    try:
        # Build command with gRPC args from config
        cmd = WALLET_CMD_PREFIX.copy()
        cmd.extend(get_grpc_args())
        cmd.extend(["send-tx", f"txs/{tx_name}.tx"])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            bufsize=-1
        )
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": "Error sending transaction.",
                "details": result.stderr
            }
        
        logger.info("Send transaction output: %s", result.stdout)
        
        # Update status in history
        update_transaction_status(tx_name, 'sent')
        
        return {
            "success": True,
            "message": "Transaction sent successfully!",
            "transaction_hash": tx_name,
            "output": result.stdout
        }
        
    except Exception as e:
        logger.error(f"Error sending transaction: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def get_transaction_history():
    """Get transaction history filtered by current wallet's address."""
    try:
        # Load transaction history from file
        history = load_transaction_history()
        
        # Get current wallet's address
        current_address = get_wallet_public_key()
        
        if not current_address:
            logger.warning("Could not determine current wallet address, returning all transactions")
            return {
                "success": True,
                "transactions": history,
                "count": len(history),
                "wallet_address": "Unknown",
                "note": "Could not filter by wallet - showing all transactions"
            }
        
        # Filter history to only show transactions from current wallet
        filtered_history = []
        for tx in history:
            tx_signer = tx.get('signer', '')
            if tx_signer == current_address:
                filtered_history.append(tx)
        
        logger.info(f"Transaction history: {len(filtered_history)} transactions found for current wallet out of {len(history)} total")
        logger.info(f"Current wallet address: {current_address[:50]}...")
        
        return {
            "success": True,
            "transactions": filtered_history,
            "count": len(filtered_history),
            "total_in_file": len(history),
            "wallet_address": current_address
        }
        
    except FileNotFoundError:
        logger.info("No transaction history file found")
        return {
            "success": True,
            "transactions": [],
            "count": 0,
            "note": "No transaction history file found"
        }
    except Exception as e:
        logger.error(f"Transaction history error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }