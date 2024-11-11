import os
import json
import sys

import pytest
from asm.asm_backend import RV32Backend
from emu.emulator import RV32IEmulator
from comm.exceptions import RV32IBaseException, ProgramNormalExitException, LaunchDebuggerException
from comm.logging import *

BASE_ADDR = 0x80100

# Helper function to convert hex strings to integers
def hex_to_int(val):
    if isinstance(val, str):
        if val.startswith('0x') or val.startswith('0X'):
            return int(val, 16)
        elif val.isdigit():
            return int(val)
    return val

# Load test configurations from JSON file
with open('emu_conf.json', 'r') as f:
    test_configs = json.load(f)

# Prepare test parameters
test_parameters = []
for config in test_configs:
    # Convert 'set' and 'check' values from hex strings to integers
    set_conf = {reg: hex_to_int(val) for reg, val in config.get('set', {}).items()}
    check_conf = {reg: hex_to_int(val) for reg, val in config.get('check', {}).items()}
    test_parameters.append((config['src'], {'set': set_conf, 'check': check_conf}))

@pytest.mark.parametrize("src, conf", test_parameters)
def test_example(src, conf):
    # Read-in source assembly
    input_file = os.path.abspath(src)
    with open(input_file, 'r') as file:
        assembly_code = file.read()

    # Create RV32I assembler backend
    try:
        mc = RV32Backend(lines=assembly_code, base_addr=BASE_ADDR)
        mc.parse_lines()
    except RV32IBaseException as e:
        ERROR("Error: {}".format(e.message()))
        e.print_stacktrace()
        sys.exit(-1)

    # Initialize emulator
    emulator = RV32IEmulator(mc)
    emulator.instantiate_cpu()
    emulator.load_programs()

    # Pre-set registers
    for reg, val in conf['set'].items():
        emulator.cpu.regs.set_by_name(reg, val)

    try:
        emulator.launch()

    except RV32IBaseException as ex:

        # Check the register values
        for reg, expected_val in conf['check'].items():
            actual_val = emulator.cpu.regs.get_by_name(reg)
            assert actual_val == expected_val, f"Register {reg}: expected {expected_val}, got {actual_val}"

