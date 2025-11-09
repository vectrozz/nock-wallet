import os
import subprocess
import json
import tempfile
import re
import time
from datetime import datetime
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['TX_FOLDER'] = os.path.join(os.path.dirname(__file__), 'txs')
app.config['HISTORY_FILE'] = os.path.join(os.path.dirname(__file__), 'wallet_history.json')
app.config['CONFIG_FILE'] = os.path.join(os.path.dirname(__file__), 'wallet_config.json')  # ← NOUVEAU

# Check if running in Docker
NOCKCHAIN_WALLET_HOST = os.getenv('NOCKCHAIN_WALLET_HOST')
if NOCKCHAIN_WALLET_HOST:
    WALLET_CMD_PREFIX = ['docker', 'exec', 'nockchain-wallet-service', 'nockchain-wallet']
    logger.info(f"Running in Docker mode - wallet container: {NOCKCHAIN_WALLET_HOST}")
else:
    WALLET_CMD_PREFIX = ['nockchain-wallet']
    logger.info("Running in local mode - using local nockchain-wallet")

# Create folders if they don't exist
os.makedirs(app.config['TX_FOLDER'], exist_ok=True)


def remove_ansi_codes(text):
    """Remove ANSI escape codes from text."""
    # Pattern pour tous les codes ANSI
    ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_pattern.sub('', text)

# ═══════════════════════════════════════════════════════════
# CONFIG FILE MANAGEMENT
# ═══════════════════════════════════════════════════════════

def load_config():
    """Load wallet configuration from JSON file."""
    if os.path.exists(app.config['CONFIG_FILE']):
        try:
            with open(app.config['CONFIG_FILE'], 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Could not decode wallet_config.json, using defaults")
            return get_default_config()
    return get_default_config()

def save_config(config):
    """Save wallet configuration to JSON file."""
    with open(app.config['CONFIG_FILE'], 'w') as f:
        json.dump(config, indent=2, fp=f)
    logger.info(f"Configuration saved: {config}")

def get_default_config():
    """Get default configuration."""
    return {
        "grpc": {
            "type": "public",
            "customAddress": ""
        }
    }

def get_current_grpc_config():
    """Get current gRPC configuration from config file."""
    config = load_config()
    return config.get('grpc', get_default_config()['grpc'])

# ═══════════════════════════════════════════════════════════
# NEW CONFIG ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get current wallet configuration."""
    try:
        config = load_config()
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
def update_config():
    """Update wallet configuration."""
    try:
        data = request.get_json()
        
        # Load current config
        config = load_config()
        
        # Update gRPC config if provided
        if 'grpc' in data:
            config['grpc'] = data['grpc']
            logger.info(f"gRPC config updated: {data['grpc']}")
        
        # Save updated config
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

# ═══════════════════════════════════════════════════════════
# GRPC HELPERS (simplified)
# ═══════════════════════════════════════════════════════════

def get_grpc_args():
    """Build gRPC command arguments from config file."""
    grpc_config = get_current_grpc_config()
    args = []
    
    client_type = grpc_config.get('type', 'public')
    
    if client_type == 'public':
        args.extend(['--client', 'public'])
        
    elif client_type == 'private':
        args.extend(['--client', 'private'])
        args.extend(['--private-grpc-server-port', '5555'])
        
    elif client_type == 'custom':
        custom_address = grpc_config.get('customAddress', '')
        if custom_address:
            args.extend(['--client', 'private'])
            if ':' in custom_address:
                port = custom_address.split(':')[1]
                args.extend(['--private-grpc-server-port', port])
            else:
                args.extend(['--private-grpc-server-port', '5555'])
    
    return args

# ═══════════════════════════════════════════════════════════
# UPDATE ALL EXISTING ROUTES (remove grpc_config parameter)
# ═══════════════════════════════════════════════════════════

@app.route('/api/balance', methods=['GET', 'POST'])
def get_balance():
    """Get wallet balance."""
    try:
        balance_data = get_wallet_balance()  # ← Plus de paramètre grpc_config
        return jsonify(balance_data)
    except Exception as e:
        logger.error(f"Error in get_balance endpoint: {str(e)}")
        return jsonify({
            "notes": [],
            "notes_count": 0,
            "total_assets": 0,
            "error": "Internal Server Error",
            "error_details": str(e)
        }), 500

def get_wallet_balance():  # ← Plus de paramètre grpc_config
    """Get wallet balance by parsing list-notes output."""
    try:
        # Build command with gRPC args from config
        cmd = WALLET_CMD_PREFIX.copy()
        cmd.extend(get_grpc_args())
        cmd.append("list-notes")
        
        logger.info(f"Executing command: {' '.join(cmd)}")
        
        # Execute list-notes command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
            bufsize=-1
        )
        
        output = result.stdout
        error_output = result.stderr
        
        logger.info(f"list-notes command executed - return code: {result.returncode}, output length: {len(output)} characters")
        
        # Check if command failed
        if result.returncode != 0:
            logger.error(f"list-notes command failed with exit code {result.returncode}")
            logger.error(f"STDOUT: {output}")
            logger.error(f"STDERR: {error_output}")
            
            full_output = output + "\n" + error_output
            is_rpc_error = "gRPC" in full_output or "service is currently unavailable" in full_output or "upstream request timeout" in full_output
            
            error_message = "RPC Service Unavailable" if is_rpc_error else "Command Failed"
            
            return {
                "notes": [],
                "notes_count": 0,
                "total_assets": 0,
                "error": error_message,
                "error_details": full_output,
                "is_rpc_error": is_rpc_error
            }
        
        # Parse the output to extract notes
        notes = []
        
        if "Wallet Notes" not in output:
            logger.warning("No 'Wallet Notes' section found in output")
            return {"notes": [], "notes_count": 0, "total_assets": 0}
        
        # ✅ SIMPLE: Split par "Details" OU "Note Information"
        wallet_notes_idx = output.find("Wallet Notes")
        notes_text = output[wallet_notes_idx:]
        
        # Split en gardant le délimiteur
        import re
        sections = re.split(r'(?=^(?:Details|Note Information)$)', notes_text, flags=re.MULTILINE)
        
        logger.debug(f"Found {len(sections)} sections after split")
        
        note_number = 0
        for i, section in enumerate(sections):
            section = section.strip()
            
            # Skip empty sections and header
            if not section or "Wallet Notes" in section or len(section) < 50:
                continue
            
            # Detect version
            is_v1 = section.startswith("Note Information")
            is_v0 = section.startswith("Details")
            
            if not is_v0 and not is_v1:
                continue
            
            note_number += 1
            
            try:
                # Extract name
                name_match = re.search(r'- Name:\s*\[(.*?)\]', section, re.DOTALL)
                name = name_match.group(1).strip().replace('\n', ' ') if name_match else "Unknown"
                
                # Extract version
                version_match = re.search(r'- Version:\s*(\d+)', section)
                version = int(version_match.group(1)) if version_match else 0
                
                # Extract assets
                if is_v1:
                    assets_match = re.search(r'- Assets \(nicks\):\s*(\d+)', section)
                else:
                    assets_match = re.search(r'- Assets:\s*(\d+)', section)
                value = int(assets_match.group(1)) if assets_match else 0
                
                # Extract block height
                block_match = re.search(r'- Block Height:\s*(\d+)', section)
                block_height = int(block_match.group(1)) if block_match else 0
                
                # Extract source (only v0)
                source = None
                if is_v0:
                    source_match = re.search(r'- Source:\s*(\S+)', section)
                    source = source_match.group(1) if source_match else "Unknown"
                
                # ✅ SIMPLE: Extract signer - juste chercher "Signers:" dans la section
                signer = "Unknown"
                
                # Check for N/A first
                if "Lock Information: N/A" in section or re.search(r'Lock Information:\s*N/A', section):
                    signer = "N/A"
                else:
                    # Trouver "Signers:" dans la section
                    signers_idx = section.find('Signers:')
                    if signers_idx != -1:
                        # Prendre tout après "Signers:"
                        after_signers = section[signers_idx + len('Signers:'):]
                        
                        # Trouver la première adresse (50+ caractères alphanumériques)
                        # On cherche sur les 500 premiers caractères pour éviter de déborder
                        search_area = after_signers[:500]
                        signer_match = re.search(r'([A-Za-z0-9]{50,})', search_area)
                        
                        if signer_match:
                            signer = signer_match.group(1).strip()
                            logger.debug(f"Signer found in section: {signer[:50]}...")
                        else:
                            logger.warning(f"Signer not found after 'Signers:'. Search area: {repr(search_area[:200])}")
                
                note = {
                    'number': note_number,
                    'name': name,
                    'value': value,
                    'block_height': block_height,
                    'version': version,
                    'signer': signer
                }
                
                if source:
                    note['source'] = source
                
                notes.append(note)
                
                format_type = "v1" if is_v1 else "v0"
                logger.debug(f"Note {note_number} ({format_type}): {name[:50]}... = {value} nick (block {block_height}, signer: {signer[:30]}...)")
                
            except Exception as e:
                logger.error(f"Error parsing section {i}: {str(e)}")
                logger.debug(f"Section content (first 400 chars): {section[:400]}")
                import traceback
                logger.error(traceback.format_exc())
                continue
        
        total_assets = sum(note["value"] for note in notes)
        
        logger.info(f"Balance parsed: {len(notes)} notes, total: {total_assets} nick")
        
        return {
            "notes": notes,
            "notes_count": len(notes),
            "total_assets": total_assets
        }
        
    except subprocess.TimeoutExpired:
        logger.error("list-notes command timeout")
        return {
            "notes": [], 
            "notes_count": 0, 
            "total_assets": 0, 
            "error": "Command Timeout",
            "error_details": "The list-notes command took too long to respond (>120s)",
            "is_rpc_error": False
        }
    except Exception as e:
        logger.error(f"Unexpected error in get_wallet_balance: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "notes": [], 
            "notes_count": 0, 
            "total_assets": 0, 
            "error": "Unexpected Error",
            "error_details": str(e) + "\n" + traceback.format_exc(),
            "is_rpc_error": False
        }

@app.route("/api/balance")
def api_balance():
    """Return balance data in JSON format."""
    return jsonify(get_wallet_balance())

@app.route("/api/wallet-info")
def api_wallet_info():
    """Return wallet information including public key."""
    try:
        public_key = get_wallet_public_key()
        return jsonify({
            "success": True,
            "public_key": public_key,
            "mode": "docker" if NOCKCHAIN_WALLET_HOST else "local"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/api/create-transaction", methods=['POST'])
def create_transaction():
    """Create a transaction."""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('recipient'):
            return jsonify({"error": "Recipient public key is required."}), 400
        if not data.get('amount_nock'):
            return jsonify({"error": "Amount is required."}), 400
        
        # Get wallet public key for history tracking
        signer_public_key = get_wallet_public_key()
        if not signer_public_key:
            logger.warning("Could not get wallet public key, using 'Unknown'")
            signer_public_key = "Unknown"
        
        # Convert Nock to Nick
        amount_nock = float(data['amount_nock'])
        amount_nick = int(amount_nock * 65536)
        fee_nick = int(data.get('fee', 10))
        
        # Get all notes to select which ones to use
        balance_data = get_wallet_balance()
        if balance_data.get('error'):
            return jsonify(balance_data), 500
        
        notes = balance_data['notes']
        
        # Check if user provided specific notes to use
        selected_note_names = data.get('selected_notes')
        # If selected_notes is provided, use_all_funds should be True by default
        use_all_funds = data.get('use_all_funds', selected_note_names is not None)
        
        selected_notes = []
        accumulated = 0
        
        if selected_note_names:
            # Use user-selected notes
            for note in notes:
                if note['name'] in selected_note_names:
                    selected_notes.append(note)
                    accumulated += note['value']  # Changed from note['assets']
            
            if not selected_notes:
                return jsonify({"error": "No valid notes found from selection."}), 400
            
            if use_all_funds:
                # When using selected notes, send all funds minus fee
                amount_nick = accumulated - fee_nick
                if amount_nick <= 0:
                    return jsonify({
                        "error": f"Selected notes ({accumulated} nick) don't have enough to cover the fee ({fee_nick} nick)."
                    }), 400
                logger.info(f"Using all funds from selected notes: {accumulated} nick - {fee_nick} fee = {amount_nick} nick to send")
                
                # UPDATE: Recalculate amount_nock for display purposes
                amount_nock = amount_nick / 65536
                logger.info(f"Adjusted amount: {amount_nock:.4f} NOCK ({amount_nick} nick)")
                
        else:
            # Auto-select notes - Sort by value descending to minimize number of inputs
            total_needed = amount_nick + fee_nick
            sorted_notes = sorted(notes, key=lambda x: x['value'], reverse=True)  # Changed from x['assets']
            
            for note in sorted_notes:
                if accumulated >= total_needed:
                    break
                selected_notes.append(note)
                accumulated += note['value']  # Changed from note['assets']
            
            if accumulated < total_needed:
                return jsonify({
                    "error": f"Insufficient funds. Need {total_needed} nick, have {accumulated} nick."
                }, 400)

        # Build the names parameter like in the working script
        # Format: "[note1],[note2],[note3]" (each note in brackets, separated by commas)
        names_parts = []
        for note in selected_notes:
            note_name = note['name']
            # Add brackets around each note name
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

        # Get current transaction files before creating new one
        old_tx_files = get_tx_files_in_folder()
        logger.info(f"Existing transaction files before creation: {len(old_tx_files)}")
        
        
        # Execute create-tx command 
        cmd = WALLET_CMD_PREFIX + [
            "create-tx",
            "--names", names_string,
            "--recipients", f"[1 {data['recipient']}]",
            "--gifts", str(amount_nick),
            "--fee", str(fee_nick)
        ]
        logger.info("Creating transaction with command: %s", " ".join(cmd))

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=120  # Add timeout
            )
            
            # Parse output to extract transaction name (which is the hash)
            output = result.stdout
            logger.info("=== FULL CREATE-TX OUTPUT ===")
            logger.info(output)
            logger.info("=== END OUTPUT ===")
            
            # Let's also check stderr
            if result.stderr:
                logger.info("=== CREATE-TX STDERR ===")
                logger.info(result.stderr)
                logger.info("=== END STDERR ===")
            
            # Check what files exist in txs folder after command
            current_tx_files = get_tx_files_in_folder()
            logger.info(f"TX files after create-tx: {list(current_tx_files.keys())}")
            
            # Try different patterns to extract transaction name
            patterns = [
                r"Name: ([^\n]+)",
                r"Transaction: ([^\n]+)", 
                r"Hash: ([^\n]+)",
                r"Created: ([^\n]+)",
                r"File: ([^\n]+)",
                r"([A-Za-z0-9]{50,})"  # Any long alphanumeric string
            ]
            
            tx_name = None
            for pattern in patterns:
                match = re.search(pattern, output)
                if match:
                    tx_name = match.group(1).strip()
                    logger.info(f"Found potential tx name with pattern '{pattern}': {tx_name}")
                    break
            
            if not tx_name:
                logger.error("Could not extract transaction name from any pattern")
                # Return the full output for debugging
                return jsonify({
                    "error": "Failed to extract transaction name from output.",
                    "debug_output": output,
                    "debug_stderr": result.stderr,
                    "tx_files_after": list(current_tx_files.keys())
                }), 500
            
        except subprocess.TimeoutExpired:
            logger.error("CREATE-TX TIMEOUT after 60 seconds")
            return jsonify({"error": "Transaction creation timed out"}), 500
            
        except subprocess.CalledProcessError as e:
            logger.error(f"CREATE-TX FAILED: return code {e.returncode}")
            logger.error(f"STDOUT: {e.stdout}")
            logger.error(f"STDERR: {e.stderr}")
            return jsonify({
                "error": f"Transaction creation failed: {e.stderr or e.stdout}",
                "return_code": e.returncode
            }), 500
            
        except Exception as e:
            logger.error(f"UNEXPECTED ERROR in create-tx: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "error": f"Unexpected error: {str(e)}"
            }), 500

        # Continue with the rest if successful...
        logger.info(f"Transaction name extracted: {tx_name}")
        
        # Verify that the transaction file was created with the correct name
        file_verified = verify_transaction_file(tx_name, old_tx_files)
        
        if not file_verified:
            logger.warning(f"Transaction file {tx_name}.tx not found or not recent")
            return jsonify({
                "error": "Transaction was created but file verification failed.",
                "transaction_name": tx_name
            }, 500)
        
        # Add transaction to history with signer information
        transaction = add_transaction_to_history(
            tx_hash=tx_name,
            recipient=data['recipient'],
            amount_nock=amount_nock,
            amount_nick=amount_nick,
            fee_nick=fee_nick,
            notes_used=len(selected_notes),
            signer=signer_public_key,
            status='created'
        )
        
        return jsonify({
            "success": True,
            "transaction_hash": tx_name,
            "transaction_name": tx_name,
            "output": output,
            "notes_used": len(selected_notes),
            "amount_nick": amount_nick,
            "fee_nick": fee_nick,
            "file_verified": file_verified,
            "history_entry": transaction
        })
    
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Error creating transaction.", "details": e.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/show-transaction", methods=['POST'])
def show_transaction():
    """Show transaction details."""
    try:
        data = request.json
        tx_name = data.get('transaction_name')
        
        if not tx_name:
            return jsonify({"error": "Transaction name is required."}), 400
        
        # Execute show-tx command
        cmd = WALLET_CMD_PREFIX + ["show-tx", f"txs/{tx_name}.tx"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        return jsonify({
            "success": True,
            "details": result.stdout
        })
    
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Error showing transaction.", "details": e.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sign-transaction", methods=['POST'])
def sign_transaction():
    """Sign a transaction."""
    try:
        data = request.json
        tx_name = data.get('transaction_name')
        
        if not tx_name:
            return jsonify({"error": "Transaction name is required."}), 400
        
        # Execute sign-tx command
        cmd = WALLET_CMD_PREFIX + ["sign-tx", f"txs/{tx_name}.tx"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Sign transaction output: %s", result.stdout)
        
        # Update transaction status in history
        update_transaction_status(tx_name, 'signed')

        return jsonify({
            "success": True,
            "message": "Transaction signed successfully.",
            "output": result.stdout
        })
    
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Error signing transaction.", "details": e.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/send-transaction", methods=['POST'])
def send_transaction():
    """Send a transaction."""
    try:
        data = request.json
        tx_name = data.get('transaction_name')
        
        if not tx_name:
            return jsonify({"error": "Transaction name is required."}), 400
        
        # Execute send-tx command
        cmd = WALLET_CMD_PREFIX + ["send-tx", f"txs/{tx_name}.tx"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        logger.info("Send transaction output: %s", result.stdout)
        
        # Update transaction status in history
        update_transaction_status(tx_name, 'sent')
        
        return jsonify({
            "success": True,
            "message": "Transaction sent successfully!",
            "transaction_hash": tx_name,
            "output": result.stdout
        })
    
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Error sending transaction.", "details": e.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/transaction-history")
def get_transaction_history():
    """Get transaction history filtered by current wallet's address."""
    try:
        # Load transaction history from file
        history = load_transaction_history()
        
        # Get current wallet's address
        current_address = get_wallet_public_key()
        
        if not current_address:
            logger.warning("Could not determine current wallet address, returning all transactions")
            return jsonify({
                "success": True,
                "transactions": history,
                "count": len(history),
                "wallet_address": "Unknown",
                "note": "Could not filter by wallet - showing all transactions"
            })
        
        # Filter history to only show transactions from current wallet
        # The transaction should have 'signer' field matching our wallet address
        filtered_history = []
        for tx in history:
            tx_signer = tx.get('signer', '')
            if tx_signer == current_address:
                filtered_history.append(tx)
        
        logger.info(f"Transaction history: {len(filtered_history)} transactions found for current wallet out of {len(history)} total")
        logger.info(f"Current wallet address: {current_address[:50]}...")
        
        return jsonify({
            "success": True,
            "transactions": filtered_history,
            "count": len(filtered_history),
            "total_in_file": len(history),
            "wallet_address": current_address
        })
        
    except FileNotFoundError:
        logger.info("No transaction history file found")
        return jsonify({
            "success": True,
            "transactions": [],
            "count": 0,
            "note": "No transaction history file found"
        })
    except Exception as e:
        logger.error(f"Transaction history error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def load_transaction_history():
    """Load transaction history from JSON file."""
    history_file = os.path.join(os.path.dirname(__file__), 'wallet_history.json')
    
    if not os.path.exists(history_file):
        logger.info(f"Transaction history file not found: {history_file}")
        return []
    
    try:
        with open(history_file, 'r') as f:
            history = json.load(f)
        
        logger.info(f"Loaded {len(history)} transactions from history file")
        return history
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing transaction history JSON: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error loading transaction history: {str(e)}")
        return []

@app.route("/api/export-keys")
def export_keys():
    """Export keys and return the file."""
    try:
        # Create temporary file for export
        export_file = os.path.join(app.config['UPLOAD_FOLDER'], 'keys.export')
        
        cmd = WALLET_CMD_PREFIX + ["export-keys"]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Save output to file
        with open(export_file, 'w') as f:
            f.write(result.stdout)
        
        return send_file(export_file, as_attachment=True, download_name='keys.export')
    
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Error exporting keys.", "details": e.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/import-keys", methods=['POST'])
def import_keys():
    """Import keys from uploaded file."""
    filepath = None
    try:
        logger.info("=== Import keys from file endpoint called ===")
        
        if 'file' not in request.files:
            logger.error("No file in request")
            return jsonify({"error": "No file provided."}), 400
        
        file = request.files['file']
        logger.info(f"File received: {file.filename}")
        
        if file.filename == '':
            logger.error("Empty filename")
            return jsonify({"error": "No file selected."}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        
        # In Docker mode, save to shared txs folder so wallet container can access it
        if NOCKCHAIN_WALLET_HOST:
            logger.info("Running in Docker mode")
            filepath = os.path.join(app.config['TX_FOLDER'], filename)
            file.save(filepath)
            container_filepath = f"/root/.nockchain-wallet/txs/{filename}"
        else:
            logger.info("Running in local mode")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            container_filepath = filepath
        
        logger.info(f"Import keys file saved: {filepath}")
        logger.info(f"Container will access: {container_filepath}")
        
        # Execute import command
        cmd = WALLET_CMD_PREFIX + ["import-keys", "--file", container_filepath]
        logger.info(f"Executing command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"Import successful: {result.stdout}")
        
        # Delete temporary file
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Temporary file removed: {filepath}")
        
        # Force wallet sync by calling list-notes
        logger.info("Forcing wallet synchronization...")
        sync_cmd = WALLET_CMD_PREFIX + ["list-notes"]
        sync_result = subprocess.run(
            sync_cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        logger.info(f"Sync completed")
        
        return jsonify({
            "success": True,
            "message": "Keys imported and wallet synchronized successfully.",
            "output": result.stdout
        })
    
    except subprocess.TimeoutExpired:
        logger.error("Wallet synchronization timeout")
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({
            "error": "Keys imported but synchronization took too long.",
            "details": "Please wait a moment and refresh balance manually"
        }), 500
    except subprocess.CalledProcessError as e:
        logger.error(f"Import keys CalledProcessError: {e.stderr}")
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({
            "error": "Error importing keys.",
            "details": e.stderr if e.stderr else str(e)
        }), 500
    except Exception as e:
        logger.error(f"Import keys Exception: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
        return jsonify({
            "error": f"Error importing keys: {type(e).__name__}",
            "details": str(e)
        }), 500

@app.route("/api/import-seedphrase", methods=['POST'])
def import_seedphrase():
    """Import keys from seed phrase."""
    try:
        logger.info("=== Import keys from seedphrase endpoint called ===")
        
        data = request.json
        seedphrase = data.get('seedphrase', '').strip()
        version = data.get('version')
        
        if not seedphrase:
            logger.error("No seedphrase provided")
            return jsonify({"error": "Seed phrase is required."}), 400
        
        if version not in [0, 1]:
            logger.error(f"Invalid version: {version}")
            return jsonify({"error": "Version must be 0 or 1."}), 400
        
        logger.info(f"Importing seedphrase with version: {version}")
        
        # Execute import-keys command with seedphrase
        cmd = WALLET_CMD_PREFIX + [
            "import-keys",
            "--seedphrase", seedphrase,
            "--version", str(version)
        ]
        logger.info(f"Executing command: {' '.join([cmd[0], cmd[1], '--seedphrase', '[REDACTED]', '--version', str(version)])}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"Import successful: {result.stdout}")
        
        # Force wallet sync by calling list-notes
        logger.info("Forcing wallet synchronization...")
        sync_cmd = WALLET_CMD_PREFIX + ["list-notes"]
        sync_result = subprocess.run(
            sync_cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        logger.info(f"Sync completed")
        
        return jsonify({
            "success": True,
            "message": f"Keys imported from seed phrase (version {version}) and wallet synchronized successfully.",
            "output": result.stdout
        })
    
    except subprocess.TimeoutExpired:
        logger.error("Wallet synchronization timeout")
        return jsonify({
            "error": "Keys imported but synchronization took too long.",
            "details": "Please wait a moment and refresh balance manually"
        }), 500
    except subprocess.CalledProcessError as e:
        logger.error(f"Import seedphrase CalledProcessError: {e.stderr}")
        return jsonify({
            "error": "Error importing keys from seed phrase.",
            "details": e.stderr if e.stderr else str(e)
        }), 500
    except Exception as e:
        logger.error(f"Import seedphrase Exception: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Error importing keys from seed phrase: {type(e).__name__}",
            "details": str(e)
        }), 500

@app.route("/api/show-seedphrase")
def show_seedphrase():
    """Show wallet seed phrase."""
    try:
        logger.info("=== Show seedphrase endpoint called ===")
        
        # Execute show-seedphrase command
        cmd = WALLET_CMD_PREFIX + ["show-seedphrase"]
        logger.info(f"Executing command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Extract seedphrase from output
        output = result.stdout
        logger.info("Seedphrase retrieved successfully")
        
        # The output might contain ANSI codes and other info, extract the seedphrase
        # Usually it's on a line by itself or after "Seed Phrase:"
        seedphrase = output.strip()
        
        # Try to extract if there's a label
        if "Seed Phrase:" in output:
            seedphrase = output.split("Seed Phrase:")[1].strip()
        
        return jsonify({
            "success": True,
            "seedphrase": seedphrase,
            "raw_output": output
        })
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Show seedphrase CalledProcessError: {e.stderr}")
        return jsonify({
            "error": "Error retrieving seed phrase.",
            "details": e.stderr if e.stderr else str(e)
        }), 500
    except Exception as e:
        logger.error(f"Show seedphrase Exception: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Error retrieving seed phrase: {type(e).__name__}",
            "details": str(e)
        }), 500

@app.route('/api/active-address', methods=['GET'])
def get_active_address():
    """Get the currently active address"""
    try:
        cmd = WALLET_CMD_PREFIX.copy()
        cmd.extend(get_grpc_args())  # ← Lit depuis le config file
        cmd.append("list-active-addresses")
        
        logger.info("Getting active address with command: %s", " ".join(cmd))
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        
        output = result.stdout
        logger.info("Active address output: %s", output)
        
        # Parse the output to extract active signing address
        active_address = None
        active_version = None
        
        # Look for address in "Addresses -- Signing" section
        signing_section = re.search(r'Addresses -- Signing(.*?)(?:Addresses -- Watch only|$)', output, re.DOTALL)
        if signing_section:
            address_match = re.search(r'- Address:\s*([^\n]+)', signing_section.group(1))
            version_match = re.search(r'- Version:\s*(\d+)', signing_section.group(1))
            
            if address_match:
                active_address = address_match.group(1).strip()
            if version_match:
                active_version = int(version_match.group(1))
        
        if not active_address:
            return jsonify({
                "success": False,
                "error": "No active address found"
            }), 404
        
        return jsonify({
            "success": True,
            "active_address": active_address,
            "version": active_version
        })
        
    except subprocess.TimeoutExpired:
        logger.error("Command timed out")
        return jsonify({"success": False, "error": "Command timed out"}), 500
    except subprocess.CalledProcessError as e:
        logger.error("Command failed with error: %s", e.stderr)
        return jsonify({"success": False, "error": e.stderr}), 500
    except Exception as e:
        logger.error("Error getting active address: %s", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/list-master-addresses', methods=['GET', 'POST'])
def list_master_addresses():
    """List all master addresses"""
    try:
        # Plus besoin de récupérer grpc_config de la requête !
        cmd = WALLET_CMD_PREFIX.copy()
        cmd.extend(get_grpc_args())  # ← Lit depuis le config file
        cmd.append("list-master-addresses")
        
        logger.info("Listing master addresses with command: %s", " ".join(cmd))
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        
        output = result.stdout
        logger.info("Master addresses output: %s", output)
        
        # Parse the output to extract all addresses
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
        
    except subprocess.TimeoutExpired:
        logger.error("Command timed out")
        return jsonify({"success": False, "error": "Command timed out"}), 500
    except subprocess.CalledProcessError as e:
        logger.error("Command failed with error: %s", e.stderr)
        return jsonify({"success": False, "error": e.stderr}), 500
    except Exception as e:
        logger.error("Error listing master addresses: %s", str(e))
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/set-active-address', methods=['POST'])
def set_active_address():
    """Set an address as the active master address"""
    try:
        data = request.get_json()
        address = data.get('address')
        # Plus besoin de grpc_config dans la requête !
        
        cmd = WALLET_CMD_PREFIX.copy()
        cmd.extend(get_grpc_args())  # ← Lit depuis le config file
        cmd.extend(["set-active-master-address", address])
        
        logger.info("Setting active address with command: %s", " ".join(cmd))
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )
        
        output = result.stdout
        logger.info("Set active address output: %s", output)
        
        # Force wallet sync after changing address
        logger.info("Forcing wallet synchronization after address change...")
        sync_cmd = WALLET_CMD_PREFIX + ["list-notes"]
        sync_result = subprocess.run(
            sync_cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        logger.info("Wallet synchronized after address change")
        
        # Get updated balance for the new active address
        logger.info("Getting balance for new active address...")
        balance_data = get_wallet_balance()
        
        return jsonify({
            "success": True,
            "message": f"Address set as active successfully",
            "output": output,
            "balance": balance_data,
            "active_address": address
        })
        
    except subprocess.TimeoutExpired:
        logger.error("Command timed out")
        return jsonify({"success": False, "error": "Command timed out"}), 500
    except subprocess.CalledProcessError as e:
        logger.error("Command failed with error: %s", e.stderr)
        return jsonify({"success": False, "error": e.stderr}), 500
    except Exception as e:
        logger.error("Error setting active address: %s", str(e))
        return jsonify({"success": False, "error": str(e)}), 500



if __name__ == "__main__":
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5007))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)
