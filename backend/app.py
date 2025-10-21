from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import subprocess
import re
import os
import tempfile
import json
import time
from datetime import datetime
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['TX_FOLDER'] = os.path.join(os.path.dirname(__file__), 'txs')  # Use local txs folder
app.config['HISTORY_FILE'] = os.path.join(os.path.dirname(__file__), 'wallet_history.json')

# Check if running in Docker
NOCKCHAIN_WALLET_HOST = os.getenv('NOCKCHAIN_WALLET_HOST')
if NOCKCHAIN_WALLET_HOST:
    # Running in Docker - wallet commands will be executed in the wallet container
    WALLET_CMD_PREFIX = ['docker', 'exec', 'nockchain-wallet-service', 'nockchain-wallet']
    print(f"Running in Docker mode - wallet container: {NOCKCHAIN_WALLET_HOST}")
else:
    # Running locally - use local nockchain-wallet
    WALLET_CMD_PREFIX = ['nockchain-wallet']
    print("Running in local mode - using local nockchain-wallet")

# Create txs folder if it doesn't exist
os.makedirs(app.config['TX_FOLDER'], exist_ok=True)

def get_wallet_public_key():
    """Get the wallet's public key."""
    try:
        cmd = WALLET_CMD_PREFIX + ['show-key']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        output = result.stdout
        # Extract public key from output
        key_match = re.search(r"Public Key: ([^\n]+)", output)
        if key_match:
            public_key = key_match.group(1).strip()
            print(f"Wallet public key: {public_key}")
            return public_key
        
        print("Warning: Could not extract public key from show-key output")
        return None
        
    except subprocess.CalledProcessError as e:
        print(f"Error getting wallet public key: {e.stderr}")
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
    
    print(f"Verifying transaction file: {expected_filename}")
    
    while time.time() - start_time < timeout:
        current_files = get_tx_files_in_folder()
        
        # Check if the expected file exists and is new
        if expected_filename in current_files:
            # If it's a new file (not in old_files) or recently modified
            if expected_filename not in old_files or current_files[expected_filename] > old_files.get(expected_filename, 0):
                print(f"✓ Transaction file verified: {expected_filename}")
                return True
        
        time.sleep(0.1)
    
    print(f"✗ Transaction file verification failed: {expected_filename} not found")
    return False

def load_transaction_history():
    """Load transaction history from JSON file."""
    if os.path.exists(app.config['HISTORY_FILE']):
        try:
            with open(app.config['HISTORY_FILE'], 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Warning: Could not decode wallet_history.json, starting fresh")
            return []
    return []

def save_transaction_history(history):
    """Save transaction history to JSON file."""
    with open(app.config['HISTORY_FILE'], 'w') as f:
        json.dump(history, indent=2, fp=f)
    print(f"Transaction history saved: {len(history)} transactions")

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
    
    print(f"Transaction added to history: {tx_hash} - Status: {status} - Signer: {signer}")
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
            print(f"Transaction status updated: {tx_hash} -> {new_status}")
            break
    
    if updated:
        save_transaction_history(history)
    else:
        print(f"Warning: Transaction {tx_hash} not found in history")
    
    return updated

def get_wallet_balance():
    """Execute CLI command and calculate total assets sum."""
    try:
        print("Fetching wallet balance...")
        # Execute CLI command
        cmd = WALLET_CMD_PREFIX + ['list-notes']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        output = result.stdout

        print("Extracting notes from output...")
        
        # Split by the separator line
        notes_raw = output.split("――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――――")
        
        notes = []
        total_assets = 0
        
        for note_text in notes_raw:
            if not note_text.strip():
                continue
                
            # Extract information using regex
            name_match = re.search(r"- Name: \[(.*?)\]", note_text, re.DOTALL)
            assets_match = re.search(r"- Assets: (\d+)", note_text)
            block_height_match = re.search(r"- Block Height: (\d+)", note_text)
            source_match = re.search(r"- Source: ([^\n]+)", note_text)
            required_sigs_match = re.search(r"- Required Signatures: (\d+)", note_text)
            signers_match = re.search(r"- Signers:\s*\n(.*?)(?=\n\n|$)", note_text, re.DOTALL)
            
            if assets_match:
                assets = int(assets_match.group(1))
                total_assets += assets
                
                note = {
                    "name": name_match.group(1).replace("\n", "").strip() if name_match else "Unknown",
                    "assets": assets,
                    "block_height": int(block_height_match.group(1)) if block_height_match else 0,
                    "source": source_match.group(1).strip() if source_match else "Unknown",
                    "required_signatures": int(required_sigs_match.group(1)) if required_sigs_match else 0,
                    "signers": signers_match.group(1).strip().split("\n") if signers_match else []
                }
                
                notes.append(note)
        
        return {
            "total_assets": total_assets,
            "notes_count": len(notes),
            "notes": notes
        }

    except subprocess.CalledProcessError as e:
        return {
            "error": "Error executing command.",
            "details": e.stderr
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
            print("Warning: Could not get wallet public key, using 'Unknown'")
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
                    accumulated += note['assets']
            
            if not selected_notes:
                return jsonify({"error": "No valid notes found from selection."}), 400
            
            if use_all_funds:
                # When using selected notes, send all funds minus fee
                amount_nick = accumulated - fee_nick
                if amount_nick <= 0:
                    return jsonify({
                        "error": f"Selected notes ({accumulated} nick) don't have enough to cover the fee ({fee_nick} nick)."
                    }, 400)
                print(f"Using all funds from selected notes: {accumulated} nick - {fee_nick} fee = {amount_nick} nick to send")
        else:
            # Auto-select notes - Sort by assets descending to minimize number of inputs
            total_needed = amount_nick + fee_nick
            sorted_notes = sorted(notes, key=lambda x: x['assets'], reverse=True)
            
            for note in sorted_notes:
                if accumulated >= total_needed:
                    break
                selected_notes.append(note)
                accumulated += note['assets']
            
            if accumulated < total_needed:
                return jsonify({
                    "error": f"Insufficient funds. Need {total_needed} nick, have {accumulated} nick."
                }), 400
        
        # Build the names parameter - Format: [note1],[note2],[note3]
        names_parts = [f"[{note['name']}]" for note in selected_notes]
        names_string = ",".join(names_parts)
        
        print(f"Selected {len(selected_notes)} notes:")
        for i, note in enumerate(selected_notes):
            note_nock = note['assets'] / 65536
            print(f"  - Note #{i+1}: {note_nock:.4f} NOCK ({note['assets']} NICK)")
        print(f"Total: {accumulated} NICK")
        print(f"Names string: {names_string}")
        
        # Get current tx files before creating transaction
        old_tx_files = get_tx_files_in_folder()
        print(f"Existing transaction files before creation: {len(old_tx_files)}")
        
        # Execute create-tx command
        cmd = WALLET_CMD_PREFIX + [
            "create-tx",
            "--names", names_string,
            "--recipients", f"[1 {data['recipient']}]",
            "--gifts", str(amount_nick),
            "--fee", str(fee_nick)
        ]
        print("Creating transaction with command:", " ".join(cmd))

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse output to extract transaction name (which is the hash)
        output = result.stdout
        print("Transaction creation output:", output)
        tx_name_match = re.search(r"Name: ([^\n]+)", output)
        tx_name = tx_name_match.group(1).strip() if tx_name_match else None
        
        if not tx_name:
            return jsonify({"error": "Failed to extract transaction name from output."}), 500
        
        print(f"Transaction name extracted from output: {tx_name}")
        
        # Verify that the transaction file was created with the correct name
        file_verified = verify_transaction_file(tx_name, old_tx_files)
        
        if not file_verified:
            print(f"Warning: Transaction file {tx_name}.tx not found or not recent")
            return jsonify({
                "error": "Transaction was created but file verification failed.",
                "transaction_name": tx_name
            }), 500
        
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
        print("Sign transaction output:", result.stdout)
        
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
        print("Send transaction output:", result.stdout)
        
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
    """Get transaction history filtered by current wallet's signer."""
    try:
        history = load_transaction_history()
        
        # Get current wallet's public key
        current_signer = get_wallet_public_key()
        
        if not current_signer:
            return jsonify({
                "success": False,
                "error": "Could not determine current wallet's public key"
            }), 500
        
        # Filter history to only show transactions from current wallet
        filtered_history = [tx for tx in history if tx.get('signer') == current_signer]
        
        print(f"Transaction history filtered: {len(filtered_history)} out of {len(history)} transactions for signer: {current_signer[:20]}...")
        
        return jsonify({
            "success": True,
            "transactions": filtered_history,
            "count": len(filtered_history),
            "signer": current_signer
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

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
        return jsonify({"error": "Error exporting keys.", "details": str(e)}), 500

@app.route("/api/import-keys", methods=['POST'])
def import_keys():
    """Import keys from uploaded file."""
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided."}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected."}), 400
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Execute import command
        cmd = WALLET_CMD_PREFIX + ["import-keys", "--file", filepath]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        # Delete temporary file
        os.remove(filepath)
        
        return jsonify({"success": True, "message": "Keys imported successfully."})
    
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Error importing keys.", "details": e.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5007))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)
