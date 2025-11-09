"""
Utilities for executing wallet commands.
"""
import subprocess
from config import WALLET_CMD_PREFIX, COMMAND_TIMEOUT
from logger import logger
from .file_helpers import load_config


def get_grpc_args():
    """
    Get gRPC arguments from config.
    
    Returns:
        list: gRPC arguments for wallet command
    """
    config = load_config()
    
    args = []
    
    # Client type
    client_type = config.get('client_type', 'private')
    args.extend(['--client', client_type])
    
    # gRPC server host/port based on client type
    if client_type == 'private':
        if config.get('private_grpc_server_host'):
            args.extend(['--private-grpc-server-host', config['private_grpc_server_host']])
        if config.get('private_grpc_server_port'):
            args.extend(['--private-grpc-server-port', str(config['private_grpc_server_port'])])
    else:  # public
        if config.get('public_grpc_server_host'):
            args.extend(['--public-grpc-server-host', config['public_grpc_server_host']])
        if config.get('public_grpc_server_port'):
            args.extend(['--public-grpc-server-port', str(config['public_grpc_server_port'])])
    
    return args


def execute_wallet_command(command_args, timeout=COMMAND_TIMEOUT, capture_output=True):
    """
    Execute a wallet command.
    
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
    cmd.extend(get_grpc_args())
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