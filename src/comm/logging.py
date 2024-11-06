import sys
import logging
from comm.colors import *

class CustomFormatter(logging.Formatter):
    # ANSI escape codes for colors
    COLORS = {
        'DEBUG': FMT_DEBUG,  # Magenta
        'INFO': FMT_INFO,  # Green
        'WARNING': FMT_WARNING,  # Yellow
        'ERROR': FMT_ERROR,  # Red
        'CRITICAL': '\033[95m'  # Bright magenta
    }
    RESET = '\033[0m'

    def format(self, record):
        # Record's message without altering white space
        msg = record.getMessage()
        if not msg:  # Skip formatting if the message is empty
            return ''

        # Apply color based on the log level
        color = self.COLORS.get(record.levelname, self.RESET)
        formatted_lines = []

        # Keep track of line breaks and format each line individually
        lines = msg.split('\n')
        for line in lines:
            line = line.rstrip()  # Strip only trailing whitespace to preserve alignment
            formatted_line = f"{self.formatTime(record)} {color}[{record.levelname}] {line}{self.RESET}"
            formatted_lines.append(formatted_line)

        return '\n'.join(formatted_lines)

# Clear all handlers if previously set
logger = logging.getLogger()
if logger.hasHandlers():
    logger.handlers.clear()  # Remove all handlers associated with the root logger

handler = logging.StreamHandler(sys.stdout) # set default stdout handler

# Configure the logging system with custom formatter
formatter = CustomFormatter(fmt='%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(handler)

logger.setLevel(logging.INFO)

def DEBUG(message):
    logger.debug(message)

def INFO(message):
    logger.info(message)

def ERROR(message):
    logger.error(message)

def WARN(message):
    logger.warn(message)

# Use synchronized logger during a debugger session (for emulator)
def DEBUGGER_INFO(message):
    INFO(message)
    sys.stdout.flush()

def DEBUGGER_ERROR(message):
    logger.error(message)
    sys.stdout.flush()

def DEBUGGER_WARN(message):
    WARN(message)
    sys.stdout.flush()