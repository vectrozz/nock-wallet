"""
gRPC configuration utilities.
"""
import json
import os
import subprocess
from config import WALLET_CMD_PREFIX, COMMAND_TIMEOUT
from logger import logger


# Configuration file path
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'wallet_config.json')


def load_config():
    """Load wallet configuration from JSON file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("Could not decode wallet_config.json, using defaults")
            return get_default_config()
    return get_default_config()


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


def get_grpc_args():
    """
    Build gRPC command arguments from config file.
    
    Returns:
        list: gRPC arguments for wallet command
    """
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
    
    logger.debug(f"gRPC args: {args} (type: {client_type})")
    
    return args


def execute_wallet_command(command_args, timeout=COMMAND_TIMEOUT, capture_output=True):
    """
    Execute a wallet command with gRPC configuration.
    
    Args:
        command_args: List of command arguments (without wallet prefix)
        timeout: Command timeout in seconds
        capture_output: Whether to capture stdout/stderr
    
    Returns:
        subprocess.CompletedProcess: Result of the command
    
    Raises:
        subprocess.TimeoutExpired: If command times out
    """
    # Build full command
    cmd = WALLET_CMD_PREFIX.copy()
    cmd.extend(get_grpc_args())  # ← Ajoute les args gRPC depuis config
    cmd.extend(command_args)
    
    logger.info(f"Executing command: {' '.join(cmd)}")
    
    # Execute command
    result = subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
        check=False,
        timeout=timeout,
        bufsize=-1
    )
    
    logger.info(f"Command executed - return code: {result.returncode}")
    
    if result.returncode != 0:
        logger.error(f"Command failed with exit code {result.returncode}")
        if capture_output:
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
    
    return result