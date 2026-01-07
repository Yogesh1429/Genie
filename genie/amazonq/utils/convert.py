import re

def windows_to_wsl_path(windows_path: str) -> str:
    """Convert Windows path (C:\\path\\to\\file) to WSL path (/mnt/c/path/to/file)"""
    
    
    # Match drive letter pattern (e.g., C:\)
    match = re.match(r'^([A-Za-z]):[/\\](.*)$', windows_path)
    if match:
        drive = match.group(1).lower()
        path = match.group(2).replace('\\', '/')
        return f'/mnt/{drive}/{path}'
    
    # If no drive letter, just convert backslashes
    return windows_path.replace('\\', '/')