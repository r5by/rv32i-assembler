import logging

class CustomFormatter(logging.Formatter):
    # ANSI escape codes for colors
    COLORS = {
        'DEBUG': '\033[93m',  # Yellow
        'INFO': '\033[92m',  # Green
        'WARNING': '\033[93m',  # Yellow
        'ERROR': '\033[91m',  # Red
        'CRITICAL': '\033[95m'  # Magenta
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

logger.setLevel(logging.DEBUG)

def DEBUG_INFO(message):
    logger.debug(message)


def INFO(message):
    logger.info(message)


def ERROR(message):
    logger.error(message)

def WARN(message):
    logger.warn(message)