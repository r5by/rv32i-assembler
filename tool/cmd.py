import sys
import os
import select
import argparse
from asm.asm_backend import RV32Backend, EmitCodeMode
from comm.logging import *
from comm.utils import write_to_file
from comm.exceptions import RV32IBaseException, ProgramNormalExitException
from emu.emulator import RV32IEmulator

def parse_cmd():
    # Create the argument parser
    parser = argparse.ArgumentParser(description="Command line options parser")

    # Add arguments
    parser.add_argument("-v", "--verbose", action="store_true", help="enable verbose output mode")
    parser.add_argument("-q", "--quiet", action="store_true", help="enable quiet output mode")
    parser.add_argument("-show-encoding", "--show-encoding", action="store_true", help="print out instruction encoding "
                                                                                       "info")
    parser.add_argument("-bin", "--binary", nargs='?', const=True, help="output translated machine code in binary "
                                                                      "format to .bin file, default to %s.bin")
    parser.add_argument("-hex", "--hexadecimal", nargs='?', const=True, help="output translated machine code in hex "
                                                                           "format to .hex file, default to %s.hex")
    parser.add_argument("-lst", "--list", type=str, help="output list file for validation, default to %s.lst")

    parser.add_argument("-s", "--assemble", type=str, help="input file (.s) to be assembled")
    parser.add_argument("-base", "--base-addr", type=int, default=0x80100, help="base address to assemble the code "
                                                                                "upon")
    parser.add_argument("-emu", "--emulator", action="store_true", help="launch emulator")

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

    DEBUG(f'Reading in assembly code:\n {assembly_code}')

    # Handle output files
    try:
        mc = RV32Backend(lines=assembly_code, base_addr=args.base_addr)
        mc.parse_lines()
    except RV32IBaseException as e:
        ERROR("Error: {}".format(e.message()))
        e.print_stacktrace()
        sys.exit(-1)

    if args.emulator:
        emulator = RV32IEmulator(mc)

        emulator.instantiate_cpu()
        emulator.load_programs()
        try:
            emulator.launch()
        except RV32IBaseException as ex:
            if isinstance(ex, ProgramNormalExitException):
                sys.exit(0)
            else:
                ex.print_stacktrace()



    mnemonics = mc.mnemonics
    # show encoding in hex format for CheckFile usage
    hex_encoded = mc.emit_code(EmitCodeMode.HEX)

    if args.show_encoding:

        for (asm, encoding) in zip(mnemonics, hex_encoded):
            # Convert the encoding string to an integer
            encoding_int = int(encoding, 16)

            # Convert the integer to bytes in little-endian order
            encoding_bytes = encoding_int.to_bytes(4, byteorder='little')

            # Format bytes as hex strings
            encoding_hex = ','.join(f'0x{byte:02x}' for byte in encoding_bytes)
            INFO(f'{asm} \t# encoding: [{encoding_hex}]')

    if args.binary:
        if isinstance(args.binary, str):
            output_filename = args.binary
        else:
            source_filename = args.assemble
            output_filename = os.path.splitext(source_filename)[0] + '.bin'

        bin_encoded = mc.emit_code(EmitCodeMode.BIN)
        INFO(f'Writing output into {output_filename}')
        write_to_file(bin_encoded, output_filename)

    if args.hexadecimal:
        # Determine the output filename
        if isinstance(args.hexadecimal, str):
            output_filename = args.hexadecimal
        else:
            # Use the source filename without extension and add .hex
            source_filename = args.assemble
            output_filename = os.path.splitext(source_filename)[0] + '.hex'

        INFO(f'Writing output into {output_filename}')
        write_to_file(hex_encoded, output_filename)

    if args.list:
        INFO("Emit list file (TODO)")
        # list_file = mc.emit_code(EmitCodeMode.LST)
        # TODO: Implement the functionality to emit list file


if __name__ == "__main__":
    parse_cmd()
