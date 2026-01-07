"""
Utility module for sending keyboard inputs to Kiro CLI
Provides helper functions for sending arrow keys and special keys
"""
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class QCLIKeyboard:
    """Helper class for sending keyboard inputs to Kiro CLI via wexpect"""
    
    # ANSI Escape codes for special keys
    # KEY_UP = '\x1b[A'
    # KEY_DOWN = '\x1b[B'
    # KEY_UP = '\x1bOA'      # Changed from '\x1b[A'
    # KEY_DOWN = '\x1bOB'    # Changed from '\x1b[B'
    KEY_UP = '\033[A'
    KEY_DOWN = '\033[B'
    KEY_RIGHT = '\033[C'
    KEY_LEFT = '\033[D'
    KEY_ENTER = '\r'
    KEY_BACKSPACE = '\x7f'
    KEY_DELETE = '\x1b[3~'
    KEY_HOME = '\x1b[H'
    KEY_END = '\x1b[F'
    KEY_PAGE_UP = '\x1b[5~'
    KEY_PAGE_DOWN = '\x1b[6~'
    KEY_TAB = '\t'
    KEY_ESCAPE = '\x1b'
    
    # Control key combinations
    CTRL_C = '\x03'
    CTRL_D = '\x04'
    CTRL_Z = '\x1a'
    CTRL_A = '\x01'
    CTRL_E = '\x05'
    CTRL_K = '\x0b'
    CTRL_U = '\x15'
    
    def __init__(self, wexpect_child):
        """
        Initialize keyboard helper
        
        Args:
            wexpect_child: The wexpect spawn child process
        """
        self.child = wexpect_child
        if not self.child:
            raise RuntimeError("Kiro CLI child process not initialized")
    
    def send_key(self, key: str, delay: float = 0.0):
        """
        Send a single key to Kiro CLI
        
        Args:
            key: The key/character to send (use class constants for special keys)
            delay: Optional delay after sending key (seconds)
        """
        # if not self.child:
        #     raise RuntimeError("Q CLI child process not initialized")
        
        self.child.send(key)
        logger.info(f"Sent key: {repr(key)}")
        
        if delay > 0:
            time.sleep(delay)
    
    def send_arrow(self, direction: str, count: int = 1, delay: float = 0.05):
        """
        Send arrow key(s) to Kiro CLI
        
        Args:
            direction: 'up', 'down', 'left', or 'right'
            count: Number of times to press the arrow key
            delay: Delay between key presses (seconds)
        """
        key_map = {
            'up': self.KEY_UP,
            'down': self.KEY_DOWN,
            'left': self.KEY_LEFT,
            'right': self.KEY_RIGHT
        }
        
        direction = direction.lower()
        if direction not in key_map:
            raise ValueError(f"Invalid direction: {direction}. Use 'up', 'down', 'left', or 'right'")
        
        key = key_map[direction]
        logger.info(f"Sending {count} {direction} arrow key(s)")
        
        for i in range(count):
            self.send_key(key)
            if i < count - 1:  # Don't delay after the last key
                time.sleep(delay*2)
    
    def send_down(self, count: int = 1):
        """Send down arrow key(s)"""
        self.send_arrow('down', count)
    
    def send_up(self, count: int = 1):
        """Send up arrow key(s)"""
        self.send_arrow('up', count)
    
    def send_left(self, count: int = 1):
        """Send left arrow key(s)"""
        self.send_arrow('left', count)
    
    def send_right(self, count: int = 1):
        """Send right arrow key(s)"""
        self.send_arrow('right', count)
    
    def send_enter(self):
        """Send Enter key"""
        logger.debug("Sending Enter key")
        self.send_key(self.KEY_ENTER)
    
    def send_tab(self, count: int = 1):
        """Send Tab key(s)"""
        logger.debug(f"Sending {count} Tab key(s)")
        for _ in range(count):
            self.send_key(self.KEY_TAB)
            time.sleep(0.05)
    
    def send_escape(self):
        """Send Escape key"""
        logger.debug("Sending Escape key")
        self.send_key(self.KEY_ESCAPE)
    
    def send_ctrl(self, char: str):
        """
        Send Ctrl+Key combination
        
        Args:
            char: Single character (a-z)
        """
        char = char.lower()
        if len(char) != 1 or not char.isalpha():
            raise ValueError("char must be a single letter (a-z)")
        
        # Convert 'a' -> 1, 'b' -> 2, etc.
        ctrl_code = chr(ord(char) - ord('a') + 1)
        logger.debug(f"Sending Ctrl+{char.upper()}")
        self.send_key(ctrl_code)
    
    def navigate_menu(self, steps_down: int = 0, steps_up: int = 0, 
                      select: bool = True, delay: float = 0.1):
        """
        Navigate menu and optionally select an option
        
        Args:
            steps_down: Number of down arrow presses
            steps_up: Number of up arrow presses
            select: Whether to press Enter after navigation
            delay: Delay between steps (seconds)
        """
        logger.info(f"Navigating menu: {steps_down} down, {steps_up} up, select={select}")
        
        if steps_down > 0:
            self.send_down(steps_down)
            time.sleep(delay)
        
        if steps_up > 0:
            self.send_up(steps_up)
            time.sleep(delay)
        
        if select:
            self.send_enter()
            logger.info("Selection confirmed with Enter")
    
    def select_option(self, option_number: int, delay: float = 0.1):
        """
        Select menu option by number (1-indexed)
        
        Args:
            option_number: Option number to select (1 = first, 2 = second, etc.)
            delay: Delay before pressing Enter
        """
        if option_number < 1:
            raise ValueError("option_number must be >= 1")
        
        logger.info(f"Selecting menu option #{option_number}")
        
        # Move down (option_number - 1) times since first option is already highlighted
        if option_number > 1:
            self.send_down(option_number - 1)
            time.sleep(delay)
        
        self.send_enter()
    
    def type_text(self, text: str, delay: float = 0.0):
        """
        Type text character by character
        
        Args:
            text: Text to type
            delay: Optional delay between characters
        """
        logger.debug(f"Typing text: {text[:50]}...")
        
        for char in text:
            self.send_key(char)
            if delay > 0:
                time.sleep(delay)
    
    def clear_line(self):
        """Clear current line (Ctrl+U)"""
        logger.debug("Clearing line")
        self.send_key(self.CTRL_U)
    
    def send_backspace(self, count: int = 1):
        """Send backspace key(s)"""
        logger.debug(f"Sending {count} backspace(s)")
        for _ in range(count):
            self.send_key(self.KEY_BACKSPACE)
            time.sleep(0.05)


# Convenience functions for standalone use
def send_arrow_to_qcli(child, direction: str, count: int = 1):
    """
    Convenience function to send arrow keys
    
    Args:
        child: wexpect child process
        direction: 'up', 'down', 'left', or 'right'
        count: Number of times to press
    """
    keyboard = QCLIKeyboard(child)
    keyboard.send_arrow(direction, count)


def navigate_qcli_menu(child, option_number: int):
    """
    Convenience function to navigate and select menu option
    
    Args:
        child: wexpect child process
        option_number: Option to select (1-indexed)
    """
    keyboard = QCLIKeyboard(child)
    keyboard.select_option(option_number)

