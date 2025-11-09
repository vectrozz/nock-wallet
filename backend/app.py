"""
Nockchain Wallet Backend - Main application entry point.
"""
from flask import Flask
from flask_cors import CORS
#from api import *
from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, CORS_ORIGINS
from logger import setup_logger

# Setup logger
logger = setup_logger()

# Create Flask app
app = Flask(__name__)

# Configure CORS
CORS(app, origins=CORS_ORIGINS)

from api import register_routes
register_routes(app)



# Root endpoint
@app.route('/')
def index():
    return {
        "service": "Nockchain Wallet Backend",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == '__main__':
    logger.info(f"Starting Nockchain Wallet Backend on {FLASK_HOST}:{FLASK_PORT}")
    logger.info(f"Debug mode: {FLASK_DEBUG}")
    
    app.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=FLASK_DEBUG
    )