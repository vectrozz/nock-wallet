"""
API routes for the wallet backend.
"""
import os
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from logger import logger
import tempfile

from services.transaction_service import (
    create_transaction,
    show_transaction,
    sign_transaction,
    send_transaction,
    get_transaction_history
)


from services.wallet_service import (
    get_wallet_balance,
    get_active_address,
    list_master_addresses_service,
    set_active_address_service,
    #sync_wallet,
    import_seedphrase_service,
    show_seedphrase_service
)

from utils.file_helpers import load_config, save_config, get_default_config
from utils.grpc import get_current_grpc_config

# Configuration
UPLOAD_FOLDER = tempfile.gettempdir()
TX_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'txs')

# ============================================================================
# CONFIG
# ============================================================================
def register_routes(app):
    
    @app.route('/api/config', methods=['GET'])
    @app.route('/api/grpc-config', methods=['GET'])  # ← Alias
    def get_config():
        """Get current wallet configuration."""
        try:
            config = load_config()
            logger.info(f"📤 Returning config: {config}")
            return jsonify({
                "success": True,
                "config": config
            })
        except Exception as e:
            logger.error(f"Error getting config: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route('/api/config', methods=['POST'])
    @app.route('/api/grpc-config', methods=['POST'])  # ← Alias
    def update_config():
        """Update wallet configuration."""
        try:
            data = request.get_json()
            
            config = load_config()
            
            if 'grpc' in data:
                config['grpc'] = data['grpc']
                logger.info(f"gRPC config updated: {data['grpc']}")
            
            save_config(config)
            
            return jsonify({
                "success": True,
                "config": config,
                "message": "Configuration updated successfully"
            })
            
        except Exception as e:
            logger.error(f"Error updating config: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    # ============================================================================
    # WALLET
    # ============================================================================

    @app.route('/api/balance', methods=['GET'])
    def balance():
        """Get wallet balance."""
        result = get_wallet_balance()
        return jsonify(result)


    @app.route('/api/active-address', methods=['GET'])
    def active_address():
        """Get active wallet address."""
        result = get_active_address()
        
        if result.get('error'):
            return jsonify(result), 500
        
        return jsonify(result)


    @app.route('/api/list-master-addresses', methods=['GET', 'POST'])
    def list_master_addresses():
        """List master addresses."""
        try:
            result = list_master_addresses_service()
            
            if not result.get('success'):
                return jsonify(result), 500
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error in list_master_addresses endpoint: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route('/api/set-active-address', methods=['POST'])
    def set_address():
        """Set active address."""
        try:
            data = request.get_json()
            address = data.get('address')
            
            if not address:
                return jsonify({"success": False, "error": "Address is required"}), 400
            
            result = set_active_address_service(address)
            
            if not result.get('success'):
                return jsonify(result), 500
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error in set_address endpoint: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500
        

    @app.route('/api/sync', methods=['POST'])
    def sync():
        """Sync wallet with blockchain."""
        #result = sync_wallet()
        
        if not result.get('success'):
            return jsonify(result), 500
        
        return jsonify(result)


    # ============================================================================
    # TRANSACTIONS
    # ============================================================================

    @app.route('/api/create-transaction', methods=['POST'])
    def create_tx():
        """Create a new transaction."""
        try:
            data = request.json
            
            logger.info(f"📥 Received transaction request: {data}")
            
            # Validate required fields
            if not data.get('recipient'):
                return jsonify({"success": False, "error": "Recipient public key is required."}), 400
            if not data.get('amount_nock'):
                return jsonify({"success": False, "error": "Amount is required."}), 400
            
            recipient = data['recipient']
            amount_nock = float(data['amount_nock'])
            fee_nick = int(data.get('fee', 10))
            selected_notes = data.get('selected_notes')  # ← Liste des NOMS de notes
            use_all_funds = data.get('use_all_funds', False)
            
            logger.info(f"📋 Transaction params:")
            logger.info(f"  - Recipient: {recipient[:50]}...")
            logger.info(f"  - Amount: {amount_nock} NOCK")
            logger.info(f"  - Fee: {fee_nick} NICK")
            logger.info(f"  - Selected notes: {len(selected_notes) if selected_notes else 0}")
            logger.info(f"  - Use all funds: {use_all_funds}")
            
            if selected_notes:
                logger.info(f"  - First note name: {selected_notes[0][:50]}...")
        
            result = create_transaction(
                recipient=recipient,
                amount_nock=amount_nock,
                fee_nick=fee_nick,
                selected_note_names=selected_notes,
                use_all_funds=use_all_funds
            )
            
            if not result.get('success'):
                logger.error(f"❌ Transaction creation failed: {result.get('error')}")
                return jsonify(result), 500
            
            logger.info(f"✅ Transaction created: {result.get('transaction_name')}")
            return jsonify(result)
        
        except Exception as e:
            logger.error(f"Error in create_tx endpoint: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return jsonify({"success": False, "error": str(e)}), 500


    @app.route('/api/show-transaction', methods=['POST'])
    def show_tx():
        """Show transaction details."""
        try:
            data = request.json
            tx_name = data.get('transaction_name')
            
            if not tx_name:
                return jsonify({"error": "Transaction name is required."}), 400
            
            result = show_transaction(tx_name)
            
            if not result.get('success'):
                return jsonify(result), 500
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error in show_tx endpoint: {str(e)}")
            return jsonify({"error": str(e)}), 500


    @app.route('/api/sign-transaction', methods=['POST'])
    def sign_tx():
        """Sign a transaction."""
        try:
            data = request.json
            tx_name = data.get('transaction_name')
            
            if not tx_name:
                return jsonify({"error": "Transaction name is required."}), 400
            
            result = sign_transaction(tx_name)
            
            if not result.get('success'):
                return jsonify(result), 500
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error in sign_tx endpoint: {str(e)}")
            return jsonify({"error": str(e)}), 500


    @app.route('/api/send-transaction', methods=['POST'])
    def send_tx():
        """Send a transaction."""
        try:
            data = request.json
            tx_name = data.get('transaction_name')
            
            if not tx_name:
                return jsonify({"error": "Transaction name is required."}), 400
            
            result = send_transaction(tx_name)
            
            if not result.get('success'):
                return jsonify(result), 500
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error in send_tx endpoint: {str(e)}")
            return jsonify({"error": str(e)}), 500


    @app.route('/api/transaction-history', methods=['GET'])
    def tx_history():
        """Get transaction history."""
        try:
            result = get_transaction_history()
            
            if not result.get('success') and 'error' in result:
                return jsonify(result), 500
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error in tx_history endpoint: {str(e)}")
            return jsonify({"success": False, "error": str(e)}), 500




    @app.route('/api/transactions', methods=['GET'])
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


    @app.route('/api/transaction/<filename>', methods=['GET'])
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


    @app.route('/api/history', methods=['GET'])
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

    @app.route('/api/import-keys', methods=['POST'])
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


    @app.route('/api/import-seedphrase', methods=['POST'])
    def import_from_seedphrase():
        """Import keys from seedphrase."""
        try:
            data = request.json
            seedphrase = data.get('seedphrase')
            version = data.get('version')
            
            if not seedphrase or version is None:
                return jsonify({
                    "success": False,
                    "error": "Missing seedphrase or version"
                }), 400
            
            result = import_seedphrase_service(seedphrase, version)  # ← Fonction corrigée
            
            if not result.get('success'):
                return jsonify(result), 500
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error in import_from_seedphrase: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    @app.route('/api/show-seedphrase', methods=['GET'])
    def show_seedphrase():
        """Show seedphrase."""
        try:
            result = show_seedphrase_service()  # ← Utilise la bonne fonction
            
            if not result.get('success'):
                return jsonify(result), 500
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error in show_seedphrase: {str(e)}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    @app.route('/api/export-keys', methods=['POST'])
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

    @app.route('/api/set-active-address', methods=['POST'])
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


    @app.route('/api/list-addresses', methods=['GET'])
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

    @app.route('/api/config', methods=['GET'])
    def get_config_route():
        """Get wallet configuration."""
        config = get_config()
        return jsonify(config)


    @app.route('/api/config', methods=['POST'])
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

    @app.route('/api/convert', methods=['POST'])
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


    @app.route('/api/health', methods=['GET'])
    def health():
        """Health check endpoint."""
        return jsonify({
            "status": "ok",
            "service": "nockchain-wallet-backend"
        })