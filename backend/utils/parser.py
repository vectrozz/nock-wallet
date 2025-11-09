"""
Parsing utilities for wallet command outputs.
"""
import re
from logger import logger


def remove_ansi_codes(text):
    """Remove ANSI escape codes from text."""
    ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
    return ansi_pattern.sub('', text)


def parse_list_notes(output):
    """
    Parse list-notes command output to extract wallet notes.
    
    Args:
        output: Command output string
    
    Returns:
        dict: {
            "notes": [...],
            "notes_count": int,
            "total_assets": int
        }
    """
    notes = []
    
    # Clean ANSI codes
    output = remove_ansi_codes(output)
    
    if "Wallet Notes" not in output:
        logger.warning("No 'Wallet Notes' section found in output")
        return {"notes": [], "notes_count": 0, "total_assets": 0}
    
    # Find the "Wallet Notes" section
    wallet_notes_idx = output.find("Wallet Notes")
    notes_text = output[wallet_notes_idx:]
    
    # Split by separator lines (50+ dashes or em-dashes)
    sections = re.split(r'\n[―\-]{50,}\n', notes_text)
    
    logger.debug(f"Found {len(sections)} sections after split")
    
    note_number = 0
    for i, section in enumerate(sections):
        section = section.strip()
        
        # Skip empty sections and header
        if not section or "Wallet Notes" in section or len(section) < 50:
            continue
        
        # Detect version by checking what's in the section
        is_v1 = "Note Information" in section
        is_v0 = "Details" in section and not is_v1
        
        if not is_v0 and not is_v1:
            continue
        
        note_number += 1
        
        try:
            # Extract name
            name_match = re.search(r'- Name:\s*\[(.*?)\]', section, re.DOTALL)
            name = name_match.group(1).strip().replace('\n', ' ') if name_match else "Unknown"
            
            # Extract version
            version_match = re.search(r'- Version:\s*(\d+)', section)
            version = int(version_match.group(1)) if version_match else 0
            
            # Extract assets
            if is_v1:
                assets_match = re.search(r'- Assets \(nicks\):\s*(\d+)', section)
            else:
                assets_match = re.search(r'- Assets:\s*(\d+)', section)
            value = int(assets_match.group(1)) if assets_match else 0
            
            # Extract block height
            block_match = re.search(r'- Block Height:\s*(\d+)', section)
            block_height = int(block_match.group(1)) if block_match else 0
            
            # Extract source (only v0)
            source = None
            if is_v0:
                source_match = re.search(r'- Source:\s*(\S+)', section)
                source = source_match.group(1) if source_match else "Unknown"
            
            # Extract signer
            signer = "Unknown"
            
            # Check for N/A first
            if "Lock Information: N/A" in section or re.search(r'Lock Information:\s*N/A', section):
                signer = "N/A"
            else:
                # Find "Signers:" in the section
                signers_idx = section.find('Signers:')
                if signers_idx != -1:
                    # Take everything after "Signers:"
                    after_signers = section[signers_idx + len('Signers:'):]
                    
                    # Find the first address (50+ alphanumeric characters)
                    search_area = after_signers[:500]
                    signer_match = re.search(r'([A-Za-z0-9]{50,})', search_area)
                    
                    if signer_match:
                        signer = signer_match.group(1).strip()
                        logger.debug(f"Signer found: {signer[:50]}...")
                    else:
                        logger.warning(f"Signer not found after 'Signers:'. Search area: {repr(search_area[:200])}")
                else:
                    logger.warning(f"'Signers:' not found in section {note_number}")
            
            note = {
                'number': note_number,
                'name': name,
                'value': value,
                'block_height': block_height,
                'version': version,
                'signer': signer
            }
            
            if source:
                note['source'] = source
            
            notes.append(note)
            
            format_type = "v1" if is_v1 else "v0"
            logger.debug(f"Note {note_number} ({format_type}): {name[:50]}... = {value} nick (block {block_height}, signer: {signer[:30]}...)")
            
        except Exception as e:
            logger.error(f"Error parsing section {i}: {str(e)}")
            logger.debug(f"Section content (first 400 chars): {section[:400]}")
            import traceback
            logger.error(traceback.format_exc())
            continue
    
    total_assets = sum(note["value"] for note in notes)
    
    logger.info(f"Balance parsed: {len(notes)} notes, total: {total_assets} nick")
    
    return {
        "notes": notes,
        "notes_count": len(notes),
        "total_assets": total_assets
    }


def parse_active_address(output):
    """
    Parse active-address command output.
    
    Args:
        output: Command output string
    
    Returns:
        str or None: Active address or None if not found
    """
    # Look for "Active Address:" line
    match = re.search(r'Active Address:\s*(\S+)', output)
    if match:
        return match.group(1).strip()
    
    # Alternative: look for an address-like string (50+ chars)
    lines = output.split('\n')
    for line in lines:
        line = line.strip()
        if len(line) >= 50 and re.match(r'^[A-Za-z0-9]+$', line):
            return line
    
    return None