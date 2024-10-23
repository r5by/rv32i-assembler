"""
RiscEmu (c) 2024 Luke Li

SPDX-License-Identifier: MIT
"""

# Define the basic color and style format strings
FMT_RED = "\033[31m"
FMT_ORANGE = "\033[33m"
FMT_GRAY = "\033[37m"
FMT_CYAN = "\033[36m"
FMT_GREEN = "\033[32m"
FMT_MAGENTA = "\033[35m"
FMT_BLUE = "\033[34m"
FMT_YELLOW = "\033[93m"

# Additional style definitions
FMT_BOLD = "\033[1m"
FMT_NONE = "\033[0m"
FMT_UNDERLINE = "\033[4m"

# Combined formats for logger
FMT_DEBUG = FMT_MAGENTA + FMT_BOLD
FMT_ERROR = FMT_RED + FMT_BOLD
FMT_INFO = FMT_GREEN + FMT_BOLD
FMT_WARNING = FMT_YELLOW + FMT_BOLD

# Combined formats for emulator console
FMT_MEM = FMT_CYAN + FMT_BOLD
FMT_PARSE = FMT_CYAN + FMT_BOLD
FMT_CPU = FMT_BLUE + FMT_BOLD
FMT_SYSCALL = FMT_YELLOW + FMT_BOLD
FMT_CSR = FMT_ORANGE + FMT_BOLD

ENDC = "\033[0m"  # Reset to default color

# Function to print a message in the given color
def print_colored(color_code, message):
    print(color_code + message + ENDC)

if __name__ == '__main__':
    print_colored(FMT_RED, "This is red text")
    print_colored(FMT_ORANGE, "This is orange text")
    print_colored(FMT_GRAY, "This is gray text")
    print_colored(FMT_CYAN, "This is cyan text")
    print_colored(FMT_GREEN, "This is green text")
    print_colored(FMT_MAGENTA, "This is magenta text")
    print_colored(FMT_BLUE, "This is blue text")
    print_colored(FMT_YELLOW, "This is yellow text")

    print_colored(FMT_ERROR, "This is error text")
    print_colored(FMT_DEBUG, "This is debug text")
    print_colored(FMT_MEM, "This is memory management text")
    print_colored(FMT_PARSE, "This is parsing text")
    print_colored(FMT_CPU, "This is CPU operation text")
    print_colored(FMT_SYSCALL, "This is system call text")
    print_colored(FMT_CSR, "This is CSR activity text")
    print_colored(FMT_UNDERLINE + FMT_GREEN, "This is underlined green text")