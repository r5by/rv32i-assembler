import sys
import select
import argparse
from riscv_assembler.code_emitter import MCEmitter
from riscv_assembler.common import *

def parse_cmd():
    # Create the argument parser
    parser = argparse.ArgumentParser(description="Command line options parser")

    # Add arguments
    parser.add_argument("-v", "--verbose", action="store_true", help="enable verbose output mode")
    parser.add_argument("-q", "--quiet", action="store_true", help="enable quiet output mode")
    parser.add_argument("-show-encoding", "--show-encoding", action="store_true", help="print out instruction encoding "
                                                                                       "info")
    parser.add_argument("-bin", "--binary", type=str, help="output translated machine code in binary "
                                                                      "format to .bin file, default to %s.bin")
    parser.add_argument("-hex", "--hexadecimal", type=str, help="output translated machine code in hex "
                                                                           "format to .hex file, default to %s.hex")
    parser.add_argument("-lst", "--list", type=str, help="output list file for validation, default to %s.lst")

    parser.add_argument("-s", "--assemble", type=str, help="Input file (.s) to be assembled")

    # Parse the arguments
    args = parser.parse_args()

    # Handle logging mode
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        INFO(f'Current logging level is set to DEBUG')
    elif args.quiet:
        logger.setLevel(logging.ERROR)
        INFO(f'Current logging level is set to ERROR')
    else:
        INFO(f'Current logging level is set to INFO')

    # Handle input
    assembly_code = None

    if args.assemble:
        INFO(f"Assembling: {args.assemble}")
        # Read the source file content
        with open(args.assemble, 'r') as file:
            assembly_code = file.read()

    if not args.assemble and not sys.stdin.isatty():
        # Read from stdin if no src or data provided and stdin is piped
        # example usage:
        #       echo "add x0, x1, x2" | python3 cmd.py -v
        INFO("Reading assembly instructions from standard input")
        ready, _, _ = select.select([sys.stdin], [], [], 0)
        if not ready:
            ERROR(f"A source code must be provided by source file (.s) provided from stdin!")
            sys.exit(1)

        assembly_code = sys.stdin.read()

    DEBUG_INFO(f'Reading in assembly code:\n {assembly_code}')

    # Handle output files
    mc = MCEmitter(hex_mode=True)
    mnemonics, encoded = mc.translate(assembly_code)

    if args.show_encoding:
        for (asm, encoding) in zip(mnemonics, encoded):
            # Convert the encoding string to an integer
            encoding_int = int(encoding, 16)

            # Convert the integer to bytes in little-endian order
            encoding_bytes = encoding_int.to_bytes(4, byteorder='little')

            # Format bytes as hex strings
            encoding_hex = ','.join(f'0x{byte:02x}' for byte in encoding_bytes)
            print(f'{asm} \t# encoding: [{encoding_hex}]')

    if args.binary:
        INFO(f'Writing output into {args.binary}')

    if args.hexadecimal:
        print("Emitting hex file...")

    if args.list:
        print("Emit list file (TODO)")
        # TODO: Implement the functionality to emit list file


if __name__ == "__main__":
    parse_cmd()
