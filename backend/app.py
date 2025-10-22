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
CORS(app, resources={r"/api/*": {"origins": "*"}})  # Permet toutes les origines en développement
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['TX_FOLDER'] = os.path.join(os.path.dirname(__file__), 'txs')  # Use local txs folder
app.config['HISTORY_FILE'] = os.path.join(os.path.dirname(__file__), 'wallet_history.json')

# Check if running in Docker
NOCKCHAIN_WALLET_HOST = os.getenv('NOCKCHAIN_WALLET_HOST')
if NOCKCHAIN_WALLET_HOST:
    # Running in Docker - wallet commands will be executed in the wallet container
    WALLET_CMD_PREFIX = ['docker', 'exec', 'nockchain-wallet-service', 'nockchain-wallet']
    logger.info(f"Running in Docker mode - wallet container: {NOCKCHAIN_WALLET_HOST}")
else:
    # Running locally - use local nockchain-wallet
    WALLET_CMD_PREFIX = ['nockchain-wallet']
    logger.info("Running in local mode - using local nockchain-wallet")

# Create txs folder if it doesn't exist
os.makedirs(app.config['TX_FOLDER'], exist_ok=True)

def get_wallet_public_key():
    """Get the wallet's public key using show-master-pubkey."""
    try:
        cmd = WALLET_CMD_PREFIX + ['show-master-pubkey']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=60
        )
        
        output = result.stdout
        logger.info(f"Master pubkey command output received: {len(output)} chars")
        
        # Extract the Corresponding Address
        address_match = re.search(r'- Corresponding Address:\s*\n\s*([^\n]+)', output, re.MULTILINE)
        if address_match:
            address = address_match.group(1).strip()
            logger.info(f"Wallet address extracted: {address[:50]}...")
            return address
        
        # Fallback: try to find any long address-like string
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            # Look for long alphanumeric strings that look like addresses
            if len(line) > 80 and line.isalnum():
                logger.info(f"Wallet address (fallback): {line[:50]}...")
                return line
        
        logger.warning("Could not extract wallet address from output")
        return None
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting wallet master pubkey: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting wallet pubkey: {str(e)}")
        return None

def get_tx_files_in_folder():
    """Get all .tx files in the txs folder with their modification times."""
    tx_files = {}
    if os.path.exists(app.config['TX_FOLDER']):
        for filename in os.listdir(app.config['TX_FOLDER']):
            if filename.endswith('.tx'):
                filepath = os.path.join(app.config['TX_FOLDER'], filename)
                tx_files[filename] = os.path.getmtime(filepath)
    return tx_files

def verify_transaction_file(tx_name, old_files, timeout=5):
    """Verify that the transaction file was created and matches the transaction name."""
    expected_filename = f"{tx_name}.tx"
    start_time = time.time()
    
    logger.info(f"Verifying transaction file: {expected_filename}")
    
    while time.time() - start_time < timeout:
        current_files = get_tx_files_in_folder()
        
        # Check if the expected file exists and is new
        if expected_filename in current_files:
            # If it's a new file (not in old_files) or recently modified
            if expected_filename not in old_files or current_files[expected_filename] > old_files.get(expected_filename, 0):
                logger.info(f"✓ Transaction file verified: {expected_filename}")
                return True
        
        time.sleep(0.1)
    
    logger.warning(f"Transaction file verification failed: {expected_filename} not found")
    return False

def load_transaction_history():
    """Load transaction history from JSON file."""
    if os.path.exists(app.config['HISTORY_FILE']):
        try:
            with open(app.config['HISTORY_FILE'], 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Could not decode wallet_history.json, starting fresh")
            return []
    return []

def save_transaction_history(history):
    """Save transaction history to JSON file."""
    with open(app.config['HISTORY_FILE'], 'w') as f:
        json.dump(history, indent=2, fp=f)
    logger.info(f"Transaction history saved: {len(history)} transactions")

def add_transaction_to_history(tx_hash, recipient, amount_nock, amount_nick, fee_nick, notes_used, signer, status='created'):
    """Add a new transaction to history."""
    history = load_transaction_history()
    
    transaction = {
        'hash': tx_hash,
        'recipient': recipient,
        'amount_nock': amount_nock,
        'amount_nick': amount_nick,
        'fee_nick': fee_nick,
        'notes_used': notes_used,
        'signer': signer,
        'status': status,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    history.append(transaction)
    save_transaction_history(history)
    
    logger.info(f"Transaction added to history: {tx_hash} - Status: {status} - Signer: {signer}")
    return transaction

def update_transaction_status(tx_hash, new_status):
    """Update the status of a transaction in history."""
    history = load_transaction_history()
    updated = False
    
    for tx in history:
        if tx['hash'] == tx_hash:
            tx['status'] = new_status
            tx['updated_at'] = datetime.now().isoformat()
            if new_status == 'sent':
                tx['sent_at'] = datetime.now().isoformat()
            updated = True
            logger.info(f"Transaction status updated: {tx_hash} -> {new_status}")
            break
    
    if updated:
        save_transaction_history(history)
    else:
        logger.warning(f"Transaction {tx_hash} not found in history")
    
    return updated

def get_wallet_balance():
    """Get wallet balance by parsing list-notes output."""
    try:
        # Execute list-notes command
        result = subprocess.run(
            WALLET_CMD_PREFIX + ["list-notes"],
            capture_output=True,
            text=True,
            check=True,
            timeout=120,
            bufsize=-1
        )
        
        output = result.stdout
        print(f"=== RAW OUTPUT LENGTH: {len(output)} characters ===")
        
        # Parse the output to extract notes
        notes = []
        
        # Find the "Wallet Notes" section
        if "Wallet Notes" not in output:
            print("=== No 'Wallet Notes' section found ===")
            return {"notes": [], "notes_count": 0, "total_assets": 0}
        
        # Split by the separator line (unicode em-dash character)
        sections = re.split(r'[―\-]{50,}', output)
        
        print(f"=== FOUND {len(sections)} sections after split ===")
        
        note_number = 0
        for i, section in enumerate(sections):
            section = section.strip()
            
            # Skip empty sections and header
            if not section or "Wallet Notes" in section:
                continue
            
            # Check if this section contains note details
            if "Details" not in section and "- Name:" not in section:
                continue
            
            note_number += 1
            
            try:
                # Extract name (can be multiline, between brackets)
                name_match = re.search(r'- Name:\s*\[(.*?)\]', section, re.DOTALL)
                if name_match:
                    name = name_match.group(1).strip().replace('\n', '')
                else:
                    name = "Unknown"
                
                # Extract assets/value
                assets_match = re.search(r'- Assets:\s*(\d+)', section)
                value = int(assets_match.group(1)) if assets_match else 0
                
                # Extract block height
                block_match = re.search(r'- Block Height:\s*(\d+)', section)
                block_height = int(block_match.group(1)) if block_match else 0
                
                # Extract source address
                source_match = re.search(r'- Source:\s*(\S+)', section)
                source = source_match.group(1) if source_match else "Unknown"
                
                # Extract signer address (in Lock section, after "- Signers:")
                signer_match = re.search(r'- Signers:\s*\n\s*(\S+)', section, re.MULTILINE)
                if not signer_match:
                    # Try alternative format
                    signer_match = re.search(r'- Signers:\s*(\S+)', section)
                signer = signer_match.group(1).strip() if signer_match else "Unknown"
                
                note = {
                    'number': note_number,
                    'name': name,
                    'value': value,
                    'block_height': block_height,
                    'source': source,
                    'signer': signer
                }
                
                notes.append(note)
                
                print(f"=== Note {note_number}: {name[:30]}... = {value} nick (block {block_height}) ===")
                
            except Exception as e:
                print(f"=== Error parsing section {i}: {str(e)} ===")
                print(f"=== Section content (first 200 chars): {section[:200]} ===")
                import traceback
                traceback.print_exc()
                continue
        
        total_assets = sum(note["value"] for note in notes)
        
        print(f"=== FINAL: {len(notes)} notes parsed, total: {total_assets} nick ===")
        
        return {
            "notes": notes,
            "notes_count": len(notes),
            "total_assets": total_assets
        }
        
    except subprocess.TimeoutExpired:
        print("=== ERROR: Command timeout ===")
        return {"notes": [], "notes_count": 0, "total_assets": 0, "error": "Command timeout"}
    except subprocess.CalledProcessError as e:
        print(f"=== ERROR: Command failed: {e.stderr} ===")
        return {"notes": [], "notes_count": 0, "total_assets": 0, "error": str(e)}
    except Exception as e:
        print(f"=== ERROR: Unexpected error: {str(e)} ===")
        import traceback
        traceback.print_exc()
        return {"notes": [], "notes_count": 0, "total_assets": 0, "error": str(e)}

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
                }), 400

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

if __name__ == "__main__":
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5007))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)
