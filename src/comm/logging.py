import logging
from comm.colors import *

class CustomFormatter(logging.Formatter):
    # ANSI escape codes for colors
    COLORS = {
        'DEBUG': FMT_DEBUG, # Magenta
        'INFO': FMT_INFO,  # Green
        'WARNING': FMT_WARNING,  # Yellow
        'ERROR': FMT_ERROR,  # Red
        'CRITICAL': '\033[95m'
    }
    RESET = '\033[0m'

    def format(self, record):
        msg = record.getMessage().strip()  # Get the message and strip any leading/trailing whitespace
        if not msg:  # Skip formatting if the message is empty
            return ''

        # Apply color based on the log level
        color = self.COLORS.get(record.levelname, self.RESET)
        formatted_lines = []
        for line in msg.split('\n'):
            formatted_lines.append(f"{self.formatTime(record)} {color}[{record.levelname}] {line}{self.RESET}")
        return '\n'.join(formatted_lines)


# Configure the logging system with custom formatter
formatter = CustomFormatter(fmt='%(message)s', datefmt='%Y-%m-%d %H:%M:%S')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.addHandler(handler)

logger.setLevel(logging.INFO)

def DEBUG_INFO(message):
    logger.debug(message)


def INFO(message):
    logger.info(message)


def ERROR(message):
    logger.error(message)

def WARN(message):
    logger.warn(message)