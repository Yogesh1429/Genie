# this is json_extracter_test3

import re
import json
import logging
import textwrap
from typing import Tuple, Dict, Any

# Install this:
# pip install json-repair ftfy unidecode

logger = logging.getLogger(__name__)

# Try to import packages
try:
    from json_repair import repair_json
    HAS_JSON_REPAIR = True
except ImportError:
    HAS_JSON_REPAIR = False
    logger.info("json-repair not available. Install with: pip install json-repair")

try:
    from ftfy import fix_text
    HAS_FTFY = True
except ImportError:
    HAS_FTFY = False
    logger.info("ftfy not available. Install with: pip install ftfy")

try:
    from unidecode import unidecode
    HAS_UNIDECODE = True
except ImportError:
    HAS_UNIDECODE = False
    logger.info("unidecode not available. Install with: pip install unidecode")

# Alternative: fix-busted-json (try this if json-repair doesn't work)
try:
    from fix_busted_json import repair_json as fix_busted_repair
    HAS_FIX_BUSTED = True
except ImportError:
    HAS_FIX_BUSTED = False

def extract_json_block(text: str, marker: str = r'>\s*GenIE_json') -> Tuple[str, int, int]:
    """Extract JSON block from text."""
    m = re.search(marker, text, flags=re.IGNORECASE)
    pos = m.end() if m else 0

    start = text.find('{', pos)
    if start == -1:
        raise ValueError("No '{' found after the json marker")

    depth = 0
    in_string = False
    escaped = False
    
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                in_string = False
        else:
            if ch == '"':
                in_string = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i + 1], start, i + 1

    raise ValueError("Did not find a closing '}' for the JSON block")

def basic_text_cleanup(text: str) -> str:
    """Basic text cleanup without external packages."""
    # Remove BOM
    if text.startswith('\ufeff'):
        text = text[1:]
    
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove problematic control characters but keep basic whitespace
    cleaned_chars = []
    for char in text:
        code = ord(char)
        # Keep: space(32), tab(9), newline(10), printable ASCII (32-126), high Unicode
        if code == 9 or code == 10 or (32 <= code <= 126) or code > 127:
            # Skip C1 control characters (128-159)
            if not (128 <= code <= 159):
                cleaned_chars.append(char)
    
    return ''.join(cleaned_chars)

def advanced_text_cleanup(text: str) -> str:
    """Advanced cleanup using external packages if available."""
    # Step 1: Use ftfy for encoding issues
    if HAS_FTFY:
        text = fix_text(text)
        logger.info("Applied ftfy text fixing")
    
    # Step 2: Basic cleanup
    text = basic_text_cleanup(text)
    
    # Step 3: Convert to ASCII as last resort
    if HAS_UNIDECODE:
        # Only use unidecode if we still have issues
        try:
            json.loads(text)
        except json.JSONDecodeError:
            text = unidecode(text)
            logger.info("Applied unidecode conversion")
    
    return text

def parse_json_robustly(raw_json: str) -> Tuple[Dict[str, Any], str]:
    """Try multiple approaches to parse JSON."""
    logger.debug(f"parse_json_robustly \n \n : {raw_json}")
    raw_json = re.sub(r'\\+\s+([nrtbf"\'\/\\])', r'\\\1', raw_json)
    # Attempt 1: Standard JSON
    try:
        return json.loads(raw_json), raw_json
    except json.JSONDecodeError:
        logger.info("Standard JSON parsing failed")

    # Attempt 2: Basic cleanup
    cleaned = basic_text_cleanup(raw_json)
    try:
        return json.loads(cleaned), cleaned
    except json.JSONDecodeError:
        logger.info("Basic cleanup failed")
        logger.debug(f"Basic cleaned \n \n : {cleaned}")

    # Attempt 3: Advanced cleanup with packages
    advanced_cleaned = advanced_text_cleanup(raw_json)
    try:
        return json.loads(advanced_cleaned), advanced_cleaned
    except json.JSONDecodeError:
        logger.info("Advanced cleanup failed")
        logger.debug(f"Advanced cleaned \n \n : {advanced_cleaned}")

    # Attempt 4: json-repair package
    if HAS_JSON_REPAIR:
        try:
            repaired = repair_json(advanced_cleaned)
            logger.debug(f"json-repair  \n \n : {repaired}")
            return json.loads(repaired), repaired
        except Exception as e:
            logger.warning(f"json-repair failed: {e}")
            logger.info(f"json-repair  \n \n : {repaired}")
    
    # Attempt 5: fix-busted-json package (alternative)
    if HAS_FIX_BUSTED:
        try:
            repaired = fix_busted_repair(advanced_cleaned)
            logger.debug(f"fix-busted-json \n \n : {repaired}")
            return json.loads(repaired), repaired
        except Exception as e:
            logger.warning(f"fix-busted-json failed: {e}")
            logger.info(f"fix-busted-json \n \n : {repaired}")

    # Attempt 6: Manual escape sequence fixing (your original approach)
    manual_fixed = advanced_cleaned
    
    # Fix escape sequences with spaces
    manual_fixed = re.sub(r'\\+\s+([nrtbf"\'\/\\])', r'\\\1', manual_fixed)
    
    # Fix newlines in strings
    def fix_string_newlines(match):
        content = match.group(0)
        return content.replace('\n', '\\n').replace('\t', '\\t').replace('\r', '\\r')
    
    manual_fixed = re.sub(r'"(?:[^"\\]|\\.)*"', fix_string_newlines, manual_fixed)
    
    try:
        return json.loads(manual_fixed), manual_fixed
    except json.JSONDecodeError:
        logger.info("Manual fixing failed")

    # Attempt 7: Ultra-aggressive cleanup (remove all non-ASCII)
    ultra_clean = re.sub(r'[^\x20-\x7E\x09\x0A\x0D]', '', manual_fixed)
    return json.loads(ultra_clean), ultra_clean

def extract_with_packages(text: str) -> str:    
    logger.debug(f"Starting JSON extraction\n {text}")
    
    text = normalize_preserving_code(text)
    # Extract the JSON block
    try:
        raw_json, start, end = extract_json_block(text)
        logger.info(f"Extracted JSON block : {raw_json}")
    except ValueError as e:
        logger.error(f"Failed to extract JSON block: {e}")
        raise
    
    # Parse the JSON
    try:
        obj, used_text = parse_json_robustly(raw_json)
        logger.info("Successfully parsed JSON")
        
        # Extract your specific fields
        approval_reqd = obj.get("approval_required", False)
        approval_prompt = obj.get("approval_prompt", None)
        
        # Handle both "tool_use" and "tooluse"
        tool_use = obj.get("tool_use") or obj.get("tooluse", "")
        
        resp = obj.get("response", "")
        
        # Convert $$$ code fences back to markdown triple backticks
        resp = re.sub(r'\$\$\$', '```', resp)
        
        # Append tool use info if present
        if tool_use and tool_use.strip():
            resp = resp + "\n\nAccessing the tool: " + str(tool_use)
            logger.info(f"Added tool use: {tool_use}")
            return "Agent mode is not currently enabled."
        # Append approval prompt if required
        if approval_reqd and approval_prompt:
            resp = resp + "\n\n" + str(approval_prompt)
            logger.info("Added approval prompt")
        
        return resp
        
    except Exception as e:
        logger.error(f"All parsing attempts failed: {e}")
        
        # Last resort: regex extraction of response field
        try:
            response_patterns = [
                r'"response"\s*:\s*"([^"]*)"',  # Simple case
                r'"response"\s*:\s*"((?:[^"\\]|\\.)*)"',  # With escapes
            ]
            
            for pattern in response_patterns:
                match = re.search(pattern, raw_json, re.DOTALL)
                if match:
                    logger.info("Extracted response using regex fallback")
                    return match.group(1).replace('\\"', '"').replace('\\n', '\n')
            
        except Exception:
            pass
        
        raise e

# Package availability summary
def check_packages():
    """Check which packages are available."""
    logger.info("Package availability:")
    logger.info(f"  json-repair: {'✓' if HAS_JSON_REPAIR else '✗'}")
    logger.info(f"  ftfy: {'✓' if HAS_FTFY else '✗'}")
    logger.info(f"  unidecode: {'✓' if HAS_UNIDECODE else '✗'}")
    logger.info(f"  fix-busted-json: {'✓' if HAS_FIX_BUSTED else '✗'}")

# Example usage
if __name__ == "__main__":
    check_packages()
    
    # Test with sample data, just for testing the file directly
    sample_text = '''
    Some text here > GenIE_json
    {
        "response": "Hello world\nThis is a test",
        "approval_required": false,
        "tool_use": "web_search"
    }
    '''
    
    try:
        result = extract_with_packages(sample_text)
        logger.info(f"\n✓ Extracted result:\n{result}")
    except Exception as e:
        print(f"✗ Extraction failed: {e}")

def remove_unicode_chars(text):
    # Remove all non-ASCII characters (i.e., anything that's not between 0x00 and 0x7F)
    return re.sub(r'[^\x00-\x7F]+', '', text)

def normalize_preserving_code(text: str) -> str:
    # parts = re.split(r'($$$.*?$$$)', text, flags=re.DOTALL)  # split around fenced code
    parts = re.split(r'(\$\$\$.*?\$\$\$)', text, flags=re.DOTALL)
    for i, part in enumerate(parts):
        logger.info(f"part {i}: {part}")
        if not part.startswith('$$$'):
            parts[i] = squeeze_spaces(part)
    return ''.join(parts)

def squeeze_spaces(text: str) -> str:
    # Replace runs of spaces/tabs with a single space, but keep newlines intact
    text = re.sub(r'[^\S\r\n]+', ' ', text)     # [^\S\r\n] = whitespace except \r or \n
    # # Trim spaces at line starts/ends
    # text = re.sub(r'[ \t]+(\r?\n)', r'\1', text)
    # text = re.sub(r'(\r?\n)[ \t]+', r'\1', text)
    return text.strip()
import re, textwrap

# your function (kept as-is)
# def squeeze_spaces(text: str) -> str:
#     text = re.sub(r'[^\S\r\n]+', ' ', text)
#     return text.strip()

def convert_json(raw_response):
    # Replace non-printable characters with cleaned version
    formatted_response = remove_unicode_chars(raw_response)
    # Convert the raw formatted response into a JSON-compatible format
    response_json = {
        "response": formatted_response
    }
    logger.info(f"response_json: {response_json}")
    # Convert the dictionary to a JSON string
    json_response = json.dumps(response_json, indent=2)
    
    return json_response