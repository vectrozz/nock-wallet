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
