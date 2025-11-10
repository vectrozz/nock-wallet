"""
Wallet service - handles balance, sync, and address operations.
"""
import re
import subprocess
import os
from utils.grpc import get_grpc_args
from utils.parser import parse_list_notes
from config import SYNC_TIMEOUT
from logger import logger

# Check if running in Docker
NOCKCHAIN_WALLET_HOST = os.getenv('NOCKCHAIN_WALLET_HOST')
if NOCKCHAIN_WALLET_HOST:
    WALLET_CMD_PREFIX = ['docker', 'exec', 'nockchain-wallet-service', 'nockchain-wallet']
    logger.info(f"Running in Docker mode - wallet container: {NOCKCHAIN_WALLET_HOST}")
else:
    WALLET_CMD_PREFIX = ['nockchain-wallet']
    logger.info("Running in local mode - using local nockchain-wallet")


def get_wallet_balance():
    """Get wallet balance by parsing list-notes output."""
    try:
        # Build command with gRPC args from config
        cmd = WALLET_CMD_PREFIX.copy()
        cmd.extend(get_grpc_args())  # ← Lit depuis le fichier config
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
        
        logger.info(f"list-notes executed - return code: {result.returncode}, output length: {len(output)} characters")
        
        # Check if command failed
        if result.returncode != 0:
            logger.error(f"list-notes failed with exit code {result.returncode}")
            
            full_output = output + "\n" + error_output
            is_rpc_error = (
                "gRPC" in full_output or 
                "service is currently unavailable" in full_output or 
                "upstream request timeout" in full_output
            )
            
            error_message = "RPC Service Unavailable" if is_rpc_error else "Command Failed"
            
            return {
                "notes": [],
                "notes_count": 0,
                "total_assets": 0,
                "error": error_message,
                "error_details": full_output,
                "is_rpc_error": is_rpc_error
            }
        
        # Parse the output
        return parse_list_notes(output)
        
    except subprocess.TimeoutExpired:
        logger.error("list-notes command timeout")
        return {
            "notes": [], 
            "notes_count": 0, 
            "total_assets": 0, 
            "error": "Command Timeout",
            "error_details": "The list-notes command took too long to respond",
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


def get_active_address():
    """Get the active wallet address."""
    try:
        # Build command with gRPC args from config
        cmd = WALLET_CMD_PREFIX.copy()
        cmd.extend(get_grpc_args())
        cmd.append("list-active-addresses")
        
        logger.info(f"Executing command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            bufsize=-1
        )
        
        if result.returncode != 0:
            logger.error(f"list-active-addresses failed: {result.stderr}")
            return {
                "success": False,
                "error": "Failed to get active address"
            }
        
        output = result.stdout
        logger.info(f"Active address output: {output}")
        
        # Parse output
        active_address = None
        active_version = None
        
        signing_section = re.search(
            r'Addresses -- Signing(.*?)(?:Addresses -- Watch only|$)', 
            output, 
            re.DOTALL
        )
        
        if signing_section:
            address_match = re.search(r'- Address:\s*([^\n]+)', signing_section.group(1))
            version_match = re.search(r'- Version:\s*(\d+)', signing_section.group(1))
            
            if address_match:
                active_address = address_match.group(1).strip()
            if version_match:
                active_version = int(version_match.group(1))
        
        if not active_address:
            logger.warning("No active address found")
            return {
                "success": False,
                "error": "No active address found"
            }
        
        logger.info(f"Active address: {active_address[:50]}... (version {active_version})")
        
        return {
            "success": True,
            "active_address": active_address,
            "version": active_version
        }
        
    except Exception as e:
        logger.error(f"Error getting active address: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def sync_wallet_NOT_USED():
    """Sync the wallet with the blockchain."""
    try:
        # Build command with gRPC args from config
        cmd = WALLET_CMD_PREFIX.copy()
        cmd.extend(get_grpc_args())
        cmd.append("sync")
        
        logger.info("Starting wallet sync...")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=SYNC_TIMEOUT,
            bufsize=-1
        )
        
        if result.returncode != 0:
            logger.error(f"Sync failed: {result.stderr}")
            return {
                "success": False,
                "output": result.stdout,
                "error": result.stderr
            }
        
        logger.info("Wallet sync completed successfully")
        return {
            "success": True,
            "output": result.stdout
        }
        
    except subprocess.TimeoutExpired:
        logger.error("Sync command timeout")
        return {
            "success": False,
            "error": "Sync timeout"
        }
    except Exception as e:
        logger.error(f"Error syncing wallet: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
    

def list_master_addresses_service():
    """List all master addresses."""
    try:
        # Build command with gRPC args from config
        cmd = WALLET_CMD_PREFIX.copy()
        cmd.extend(get_grpc_args())
        cmd.append("list-master-addresses")
        
        logger.info(f"Listing master addresses with command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            bufsize=-1
        )
        
        if result.returncode != 0:
            logger.error(f"list-master-addresses failed: {result.stderr}")
            return {
                "success": False,
                "error": result.stderr or "Command failed"
            }
        
        output = result.stdout
        logger.info(f"Master addresses output: {output}")
        
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
        
        logger.info(f"Found {len(addresses)} master addresses")
        
        return {
            "success": True,
            "addresses": addresses
        }
        
    except subprocess.TimeoutExpired:
        logger.error("list-master-addresses command timeout")
        return {
            "success": False,
            "error": "Command timed out"
        }
    except Exception as e:
        logger.error(f"Error listing master addresses: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def set_active_address_service(address):
    """Set an address as the active master address."""
    try:
        # Build command with gRPC args from config
        cmd = WALLET_CMD_PREFIX.copy()
        cmd.extend(get_grpc_args())
        cmd.extend(["set-active-master-address", address])
        
        logger.info(f"Setting active address with command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            bufsize=-1
        )
        
        if result.returncode != 0:
            logger.error(f"set-active-master-address failed: {result.stderr}")
            return {
                "success": False,
                "error": result.stderr or "Command failed"
            }
        
        output = result.stdout
        logger.info(f"Set active address output: {output}")
        
        # Force wallet sync after changing address
        #logger.info("Forcing wallet synchronization after address change...")
        #sync_result = sync_wallet()
        
        #if not sync_result.get('success'):
        #    logger.warning("Sync after address change failed, but continuing...")
        
        # Get updated balance for the new active address
        logger.info("Getting balance for new active address...")
        balance_data = get_wallet_balance()
        
        return {
            "success": True,
            "message": "Address set as active successfully",
            "output": output,
            "balance": balance_data,
            "active_address": address
        }
        
    except subprocess.TimeoutExpired:
        logger.error("set-active-master-address command timeout")
        return {
            "success": False,
            "error": "Command timed out"
        }
    except Exception as e:
        logger.error(f"Error setting active address: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def get_wallet_public_key():
    """Get wallet public key (active address)."""
    result = get_active_address()
    if result.get('success'):
        return result.get('active_address')
    return None


def import_seedphrase_service(seedphrase, version):
    """Import keys from seed phrase."""
    try:
        logger.info(f"Importing seedphrase with version: {version}")
        
        # Build command with gRPC args
        cmd = WALLET_CMD_PREFIX.copy()
        cmd.extend(get_grpc_args())
        cmd.extend([
            "import-keys",
            "--seedphrase", seedphrase,
            "--version", str(version)
        ])
        
        logger.info(f"Executing command: {' '.join([cmd[0], cmd[1], '--seedphrase', '[REDACTED]', '--version', str(version)])}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            bufsize=-1
        )
        
        if result.returncode != 0:
            logger.error(f"Import seedphrase failed: {result.stderr}")
            return {
                "success": False,
                "error": result.stderr or "Import failed"
            }
        
        logger.info("Import successful, loading...")
        
        # Force wallet sync
        #sync_result = sync_wallet()
        
        return {
            "success": True,
            "message": f"Keys imported from seed phrase (version {version}) successfully",
            "output": result.stdout
        }
        
    except subprocess.TimeoutExpired:
        logger.error("Import seedphrase timeout")
        return {
            "success": False,
            "error": "Command timed out"
        }
    except Exception as e:
        logger.error(f"Error importing seedphrase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def show_seedphrase_service():
    """Show wallet seed phrase."""
    try:
        logger.info("Retrieving seedphrase...")
        
        # Build command with gRPC args
        cmd = WALLET_CMD_PREFIX.copy()
        cmd.extend(get_grpc_args())
        cmd.append("show-seedphrase")
        
        logger.info(f"Executing command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
            bufsize=-1
        )
        
        if result.returncode != 0:
            logger.error(f"Show seedphrase failed: {result.stderr}")
            return {
                "success": False,
                "error": result.stderr or "Failed to retrieve seedphrase"
            }
        
        output = result.stdout.strip()
        logger.info("Seedphrase retrieved successfully")
        
        # Extract seedphrase if there's a label
        seedphrase = output
        if "Seed Phrase:" in output:
            seedphrase = output.split("Seed Phrase:")[1].strip()
        
        return {
            "success": True,
            "seedphrase": seedphrase,
            "raw_output": output
        }
        
    except subprocess.TimeoutExpired:
        logger.error("Show seedphrase timeout")
        return {
            "success": False,
            "error": "Command timed out"
        }
    except Exception as e:
        logger.error(f"Error showing seedphrase: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
