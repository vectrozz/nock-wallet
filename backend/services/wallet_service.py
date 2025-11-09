"""
Wallet service - handles balance, sync, and address operations.
"""
import re
import subprocess
from utils.command import execute_wallet_command
from utils.parser import parse_list_notes
from config import SYNC_TIMEOUT
from logger import logger


def get_wallet_balance():
    """
    Get wallet balance by parsing list-notes output.
    
    Returns:
        dict: {
            "notes": [...],
            "notes_count": int,
            "total_assets": int,
            "error": str (optional),
            "error_details": str (optional),
            "is_rpc_error": bool (optional)
        }
    """
    try:
        # Execute list-notes command
        result = execute_wallet_command(['list-notes'])
        
        output = result.stdout
        error_output = result.stderr
        
        logger.info(f"list-notes executed - return code: {result.returncode}, output length: {len(output)} characters")
        
        # Check if command failed
        if result.returncode != 0:
            logger.error(f"list-notes failed with exit code {result.returncode}")
            
            # Check if it's an RPC error
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
    """
    Get the active wallet address.
    
    Returns:
        dict: {
            "success": bool,
            "active_address": str (optional),
            "version": int (optional),
            "error": str (optional)
        }
    """
    try:
        # ✅ Utiliser list-active-addresses au lieu de active-address
        result = execute_wallet_command(['list-active-addresses'])
        
        if result.returncode != 0:
            logger.error(f"list-active-addresses failed: {result.stderr}")
            return {
                "success": False,
                "error": "Failed to get active address"
            }
        
        output = result.stdout
        logger.info(f"Active address output: {output}")
        
        # Parse the output to extract active signing address
        active_address = None
        active_version = None
        
        # Look for address in "Addresses -- Signing" section
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
            logger.warning("No active address found in output")
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
        
    except subprocess.TimeoutExpired:
        logger.error("list-active-addresses command timeout")
        return {
            "success": False,
            "error": "Command timeout"
        }
    except Exception as e:
        logger.error(f"Error getting active address: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


def sync_wallet():
    """
    Sync the wallet with the blockchain.
    
    Returns:
        dict: {
            "success": bool,
            "output": str,
            "error": str (optional)
        }
    """
    try:
        logger.info("Starting wallet sync...")
        
        result = execute_wallet_command(['sync'], timeout=SYNC_TIMEOUT)
        
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
            "error": "Sync timeout - operation took too long"
        }
    except Exception as e:
        logger.error(f"Error syncing wallet: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }