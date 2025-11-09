"""
Configuration and constants for the wallet backend.
"""
import os
import tempfile

# Flask configuration
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5007))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

# Docker detection
NOCKCHAIN_WALLET_HOST = os.getenv('NOCKCHAIN_WALLET_HOST')
IS_DOCKER = NOCKCHAIN_WALLET_HOST is not None

# Wallet command prefix
if IS_DOCKER:
    WALLET_CMD_PREFIX = ['docker', 'exec', 'nockchain-wallet-service', 'nockchain-wallet']
else:
    WALLET_CMD_PREFIX = ['nockchain-wallet']

# Folders
BASE_DIR = os.path.dirname(__file__)
UPLOAD_FOLDER = tempfile.gettempdir()
TX_FOLDER = os.path.join(BASE_DIR, 'txs')
HISTORY_FILE = os.path.join(BASE_DIR, 'wallet_history.json')
CONFIG_FILE = os.path.join(BASE_DIR, 'wallet_config.json')

# Create folders if they don't exist
os.makedirs(TX_FOLDER, exist_ok=True)

# CORS origins
CORS_ORIGINS = "*"

# Command timeouts (seconds)
COMMAND_TIMEOUT = 120
SYNC_TIMEOUT = 120

# Conversion constants
NOCK_TO_NICK = 65536