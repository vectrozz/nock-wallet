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
    
    # ✅ ÉTAPE 1: Split par separator lines (50+ dashes or em-dashes)
    big_sections = re.split(r'\n[―\-]{50,}\n', notes_text)
    
    # ✅ ÉTAPE 2: Pour chaque grande section, re-split par "Note Information" 
    # pour séparer les notes V0 et V1 qui ne sont pas séparées par des tirets
    all_sections = []
    for big_section in big_sections:
        # Si la section contient à la fois "Details" et "Note Information"
        if "Details" in big_section and "Note Information" in big_section:
            # Split en gardant "Note Information"
            parts = re.split(r'(Note Information)', big_section)
            
            # Reconstruire : première partie (V0) + reste (V1)
            v0_part = parts[0].strip()
            if v0_part and len(v0_part) > 50:
                all_sections.append(v0_part)
            
            # V1 part = "Note Information" + ce qui suit
            if len(parts) >= 3:
                v1_part = ("Note Information" + parts[2]).strip()
                if v1_part and len(v1_part) > 50:
                    all_sections.append(v1_part)
        else:
            # Section normale, garder telle quelle
            if big_section.strip() and len(big_section.strip()) > 50:
                all_sections.append(big_section.strip())
    
    logger.debug(f"Found {len(all_sections)} note sections after splitting")
    
    note_number = 0
    for i, section in enumerate(all_sections):
        # Skip header
        if "Wallet Notes" in section:
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
            
            # Extract block height - CHERCHER APRÈS le marqueur de début de note
            block_height = 0
            if is_v1:
                # Pour V1: chercher après "Note Information"
                note_info_idx = section.find('Note Information')
                if note_info_idx != -1:
                    after_note_info = section[note_info_idx:]
                    block_match = re.search(r'- Block Height:\s*(\d+)', after_note_info)
                    if block_match:
                        block_height = int(block_match.group(1))
                    else:
                        logger.warning(f"V1 Block height not found after 'Note Information' in note {note_number}")
            else:
                # Pour V0: chercher après "Details"
                details_idx = section.find('Details')
                if details_idx != -1:
                    after_details = section[details_idx:]
                    block_match = re.search(r'- Block Height:\s*(\d+)', after_details)
                    if block_match:
                        block_height = int(block_match.group(1))
                    else:
                        logger.warning(f"V0 Block height not found after 'Details' in note {note_number}")
            
            # Extract source (only v0)
            source = None
            if is_v0:
                source_match = re.search(r'- Source:\s*(\S+)', section)
                source = source_match.group(1) if source_match else "Unknown"
            
            # ✅ Extract signer - CHERCHER DANS LA BONNE PARTIE DE LA SECTION
            signer = "Unknown"
            
            # Check for N/A first
            if "Lock Information: N/A" in section or re.search(r'Lock Information:\s*N/A', section):
                signer = "N/A"
            else:
                # ✅ Pour V1: chercher après "Lock Information:"
                # ✅ Pour V0: chercher après "Lock" (pas "Lock Information")
                if is_v1:
                    lock_info_idx = section.find('Lock Information:')
                    if lock_info_idx != -1:
                        after_lock = section[lock_info_idx:]
                    else:
                        after_lock = section
                else:
                    # V0: chercher après "Lock\n" (avec retour à la ligne)
                    lock_idx = section.find('Lock\n')
                    if lock_idx != -1:
                        after_lock = section[lock_idx:]
                    else:
                        after_lock = section
                
                # Find "Signers:" in the relevant part
                signers_idx = after_lock.find('Signers:')
                if signers_idx != -1:
                    # Take everything after "Signers:"
                    after_signers = after_lock[signers_idx + len('Signers:'):]
                    
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