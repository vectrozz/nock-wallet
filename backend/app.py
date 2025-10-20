from flask import Flask, jsonify, send_file, request
from flask_cors import CORS
import subprocess
import re
import os
import tempfile
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()
app.config['TX_FOLDER'] = os.path.join(tempfile.gettempdir(), 'txs')

# Create txs folder if it doesn't exist
os.makedirs(app.config['TX_FOLDER'], exist_ok=True)

def get_wallet_balance():
    """Execute CLI command and calculate total assets sum."""
    try:
        print("Fetching wallet balance...")
        # Execute CLI command
        result = subprocess.run(
            ["nockchain-wallet", "list-notes"],
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
                    }), 400
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
        
        # Build the names parameter - IMPORTANT: Format like [note1],[note2],[note3]
        # Each note is wrapped in brackets and separated by commas
        names_parts = [f"[{note['name']}]" for note in selected_notes]
        names_string = ",".join(names_parts)
        
        print(f"Selected {len(selected_notes)} notes:")
        for i, note in enumerate(selected_notes):
            note_nock = note['assets'] / 65536
            print(f"  - Note #{i+1}: {note_nock:.4f} NOCK ({note['assets']} NICK)")
        print(f"Total: {accumulated} NICK")
        print(f"Names string: {names_string}")
        
        # Execute create-tx command
        cmd = [
            "nockchain-wallet", "create-tx",
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
        
        # Parse output to extract transaction name
        output = result.stdout
        print("Transaction creation output:", output)
        tx_name_match = re.search(r"Name: ([^\n]+)", output)
        tx_name = tx_name_match.group(1).strip() if tx_name_match else None
        
        if not tx_name:
            return jsonify({"error": "Failed to extract transaction name from output."}), 500
        
        return jsonify({
            "success": True,
            "transaction_name": tx_name,
            "output": output,
            "notes_used": len(selected_notes),
            "amount_nick": amount_nick,
            "fee_nick": fee_nick
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
        result = subprocess.run(
            ["nockchain-wallet", "show-tx", f"txs/{tx_name}.tx"],
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
        result = subprocess.run(
            ["nockchain-wallet", "sign-tx", f"txs/{tx_name}.tx"],
            capture_output=True,
            text=True,
            check=True
        )
        print("Sign transaction output:", result.stdout)

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
        result = subprocess.run(
            ["nockchain-wallet", "send-tx", f"txs/{tx_name}.tx"],
            capture_output=True,
            text=True,
            check=True
        )
        print("Send transaction output:", result.stdout)
        
        return jsonify({
            "success": True,
            "message": "Transaction sent successfully!",
            "output": result.stdout
        })
    
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "Error sending transaction.", "details": e.stderr}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/export-keys")
def export_keys():
    """Export keys and return the file."""
    try:
        # Create temporary file for export
        export_file = os.path.join(app.config['UPLOAD_FOLDER'], 'keys.export')
        
        result = subprocess.run(
            ["nockchain-wallet", "export-keys"],
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
        result = subprocess.run(
            ["nockchain-wallet", "import-keys", "--file", filepath],
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
