"""
API routes for the wallet backend.
"""
import os
from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename
from services import (
    get_wallet_balance,
    get_active_address,
    sync_wallet,
    create_transaction,
    broadcast_transaction,
    import_keys_service,
    get_config,
    update_config
)
from utils.file_helpers import load_history, save_transaction
from utils.command import execute_wallet_command
from config import TX_FOLDER, UPLOAD_FOLDER, NOCK_TO_NICK
from logger import logger

# Create Blueprint
api = Blueprint('api', __name__, url_prefix='/api')


# ============================================================================
# BALANCE & WALLET INFO
# ============================================================================

@api.route('/balance', methods=['GET'])
def balance():
    """Get wallet balance."""
    result = get_wallet_balance()
    return jsonify(result)


@api.route('/active-address', methods=['GET'])
def active_address():
    """Get active wallet address."""
    result = get_active_address()
    
    if result.get('error'):
        return jsonify(result), 500
    
    return jsonify(result)


@api.route('/sync', methods=['POST'])
def sync():
    """Sync wallet with blockchain."""
    result = sync_wallet()
    
    if not result.get('success'):
        return jsonify(result), 500
    
    return jsonify(result)


# ============================================================================
# TRANSACTIONS
# ============================================================================

@api.route('/create-transaction', methods=['POST'])
def create_tx():
    """Create a new transaction."""
    data = request.json
    
    recipient = data.get('recipient')
    amount_nock = data.get('amount_nock')
    notes = data.get('notes')
    version = data.get('version', 1)
    
    if not recipient or amount_nock is None:
        return jsonify({
            "success": False,
            "error": "Missing recipient or amount_nock"
        }), 400
    
    result = create_transaction(recipient, amount_nock, notes, version)
    
    if not result.get('success'):
        return jsonify(result), 500
    
    return jsonify(result)


@api.route('/broadcast', methods=['POST'])
def broadcast():
    """Broadcast a transaction."""
    data = request.json
    tx_file = data.get('tx_file')
    
    if not tx_file:
        return jsonify({
            "success": False,
            "error": "Missing tx_file parameter"
        }), 400
    
    # Build full path
    tx_path = os.path.join(TX_FOLDER, tx_file)
    
    if not os.path.exists(tx_path):
        return jsonify({
            "success": False,
            "error": f"Transaction file not found: {tx_file}"
        }), 404
    
    result = broadcast_transaction(tx_path)
    
    if not result.get('success'):
        return jsonify(result), 500
    
    return jsonify(result)


@api.route('/transactions', methods=['GET'])
def list_transactions():
    """List all transaction files."""
    try:
        tx_files = [f for f in os.listdir(TX_FOLDER) if f.endswith('.json')]
        tx_files.sort(key=lambda x: os.path.getmtime(os.path.join(TX_FOLDER, x)), reverse=True)
        
        return jsonify({
            "transactions": tx_files,
            "count": len(tx_files)
        })
    except Exception as e:
        logger.error(f"Error listing transactions: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500


@api.route('/transaction/<filename>', methods=['GET'])
def get_transaction(filename):
    """Get a specific transaction file."""
    try:
        filepath = os.path.join(TX_FOLDER, secure_filename(filename))
        
        if not os.path.exists(filepath):
            return jsonify({
                "error": "Transaction file not found"
            }), 404
        
        return send_file(filepath, mimetype='application/json')
    except Exception as e:
        logger.error(f"Error getting transaction: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500


@api.route('/history', methods=['GET'])
def get_history():
    """Get transaction history."""
    try:
        history = load_history()
        return jsonify({
            "history": history,
            "count": len(history)
        })
    except Exception as e:
        logger.error(f"Error getting history: {str(e)}")
        return jsonify({
            "error": str(e)
        }), 500


# ============================================================================
# KEYS MANAGEMENT
# ============================================================================

@api.route('/import-keys', methods=['POST'])
def import_keys():
    """Import keys from file."""
    if 'file' not in request.files:
        return jsonify({
            "success": False,
            "error": "No file provided"
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            "success": False,
            "error": "No file selected"
        }), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        logger.info(f"File uploaded: {filepath}")
        
        # Import keys
        result = import_keys_service(file_path=filepath)
        
        # Clean up uploaded file
        try:
            os.remove(filepath)
        except:
            pass
        
        if not result.get('success'):
            return jsonify(result), 500
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error importing keys: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api.route('/import-from-seedphrase', methods=['POST'])
def import_from_seedphrase():
    """Import keys from seedphrase."""
    data = request.json
    
    seedphrase = data.get('seedphrase')
    version = data.get('version')
    
    if not seedphrase or version is None:
        return jsonify({
            "success": False,
            "error": "Missing seedphrase or version"
        }), 400
    
    result = import_keys_service(seedphrase=seedphrase, version=version)
    
    if not result.get('success'):
        return jsonify(result), 500
    
    return jsonify(result)


@api.route('/export-keys', methods=['POST'])
def export_keys():
    """Export wallet keys."""
    data = request.json
    output_path = data.get('output_path', 'exported_keys.json')
    
    try:
        result = execute_wallet_command(['export-keys', output_path])
        
        if result.returncode != 0:
            logger.error(f"Export keys failed: {result.stderr}")
            return jsonify({
                "success": False,
                "error": result.stderr or "Export failed"
            }), 500
        
        logger.info(f"Keys exported to {output_path}")
        
        # Check if file exists and send it
        if os.path.exists(output_path):
            return send_file(
                output_path,
                as_attachment=True,
                download_name='wallet_keys.json',
                mimetype='application/json'
            )
        else:
            return jsonify({
                "success": True,
                "output": result.stdout
            })
        
    except Exception as e:
        logger.error(f"Error exporting keys: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# ADDRESSES
# ============================================================================

@api.route('/set-active-address', methods=['POST'])
def set_active_address():
    """Set active wallet address (set-active-master-address)."""
    data = request.json
    address = data.get('address')
    
    if not address:
        return jsonify({
            "success": False,
            "error": "Missing address parameter"
        }), 400
    
    try:
        # ✅ Utiliser set-active-master-address
        result = execute_wallet_command(['set-active-master-address', address])
        
        if result.returncode != 0:
            logger.error(f"Set active address failed: {result.stderr}")
            return jsonify({
                "success": False,
                "error": result.stderr or "Failed to set active address"
            }), 500
        
        logger.info(f"Active address set to {address[:50]}...")
        
        # ✅ Force wallet sync after changing address
        logger.info("Forcing wallet synchronization after address change...")
        sync_result = execute_wallet_command(['list-notes'], timeout=120)
        logger.info("Wallet synchronized after address change")
        
        # ✅ Get updated balance for the new active address
        logger.info("Getting balance for new active address...")
        from services import get_wallet_balance
        balance_data = get_wallet_balance()
        
        return jsonify({
            "success": True,
            "message": "Address set as active successfully",
            "output": result.stdout,
            "balance": balance_data,
            "active_address": address
        })
        
    except Exception as e:
        logger.error(f"Error setting active address: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api.route('/list-master-addresses', methods=['GET', 'POST'])
def list_master_addresses():
    """List all master addresses."""
    try:
        import re
        
        result = execute_wallet_command(['list-master-addresses'])
        
        if result.returncode != 0:
            logger.error(f"List master addresses failed: {result.stderr}")
            return jsonify({
                "success": False,
                "error": result.stderr or "Failed to list master addresses"
            }), 500
        
        output = result.stdout
        logger.info(f"Master addresses output: {output}")
        
        # ✅ Parse the output to extract all addresses
        addresses = []
        
        # Split by separator "―"
        sections = output.split('―')
        
        for section in sections:
            if 'Address:' in section:
                address_match = re.search(r'- Address:\s*([^\n]+?)(?:\s*\(active\))?$', section, re.MULTILINE)
                version_match = re.search(r'- Version:\s*(\d+)', section)
                is_active = '(active)' in section
                
                if address_match:
                    address = address_match.group(1).strip()
                    version = int(version_match.group(1)) if version_match else None
                    
                    addresses.append({
                        "address": address,
                        "version": version,
                        "is_active": is_active
                    })
        
        return jsonify({
            "success": True,
            "addresses": addresses
        })
        
    except Exception as e:
        logger.error(f"Error listing master addresses: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@api.route('/list-addresses', methods=['GET'])
def list_addresses():
    """List all wallet addresses."""
    try:
        result = execute_wallet_command(['list-addresses'])
        
        if result.returncode != 0:
            logger.error(f"List addresses failed: {result.stderr}")
            return jsonify({
                "addresses": [],
                "error": result.stderr
            }), 500
        
        # Parse addresses from output
        addresses = []
        for line in result.stdout.split('\n'):
            line = line.strip()
            # Look for address-like strings (50+ alphanumeric chars)
            if len(line) >= 50 and line.replace('-', '').replace('*', '').strip().isalnum():
                addresses.append(line)
        
        return jsonify({
            "addresses": addresses,
            "count": len(addresses)
        })
        
    except Exception as e:
        logger.error(f"Error listing addresses: {str(e)}")
        return jsonify({
            "addresses": [],
            "error": str(e)
        }), 500


# ============================================================================
# CONFIGURATION
# ============================================================================

@api.route('/config', methods=['GET'])
def get_config_route():
    """Get wallet configuration."""
    config = get_config()
    return jsonify(config)


@api.route('/config', methods=['POST'])
def update_config_route():
    """Update wallet configuration."""
    data = request.json
    
    result = update_config(data)
    
    if not result.get('success'):
        return jsonify(result), 500
    
    return jsonify(result)


# ============================================================================
# UTILITIES
# ============================================================================

@api.route('/convert', methods=['POST'])
def convert_currency():
    """Convert between nock and nick."""
    data = request.json
    
    amount = data.get('amount')
    from_unit = data.get('from', 'nock')  # 'nock' or 'nick'
    
    if amount is None:
        return jsonify({
            "error": "Missing amount parameter"
        }), 400
    
    try:
        amount = float(amount)
        
        if from_unit == 'nock':
            # nock to nick
            nick = int(amount * NOCK_TO_NICK)
            return jsonify({
                "nock": amount,
                "nick": nick
            })
        else:
            # nick to nock
            nock = amount / NOCK_TO_NICK
            return jsonify({
                "nick": int(amount),
                "nock": nock
            })
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 400


@api.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "nockchain-wallet-backend"
    })