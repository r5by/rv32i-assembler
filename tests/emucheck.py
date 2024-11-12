import os
import json
import sys
from venv import create

import pytest
from asm.asm_backend import RV32Backend
from comm.utils import load_json_config, JSONBuilder
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

def load_conf_paras(confs):
    # Prepare test parameters
    test_parameters = []
    for config in confs:
        # Convert 'set' and 'check' values from hex strings to integers
        set_conf = {reg: hex_to_int(val) for reg, val in config.get('set', {}).items()}
        check_conf = {reg: hex_to_int(val) for reg, val in config.get('check', {}).items()}
        test_parameters.append((config['src'], {'set': set_conf, 'check': check_conf}))

    return test_parameters

@pytest.mark.parametrize("src, conf", load_conf_paras(load_json_config('emu_conf.json')))
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

def create_golden_json(golden_data_file, output_json_file):
    builder = JSONBuilder()
    with open(golden_data_file, 'r') as f:
        for line_number, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue  # Skip empty lines
            # Each line has three points separated by ";"
            points = line.split(';')
            if len(points) != 3:
                print(f"Invalid line format at line {line_number}: {line}")
                continue  # Skip invalid lines

            # Parse the three points
            p1_str = points[0].strip()
            p2_str = points[1].strip()
            p3_str = points[2].strip()

            # Each point has x, y, z coordinates separated by ","
            p1_coords = [coord.strip() for coord in p1_str.split(',')]
            p2_coords = [coord.strip() for coord in p2_str.split(',')]
            p3_coords = [coord.strip() for coord in p3_str.split(',')]

            if len(p1_coords) != 3 or len(p2_coords) != 3 or len(p3_coords) != 3:
                print(f"Invalid point format at line {line_number}: {line}")
                continue

            # Start a new entry
            builder.add_entry()
            # Set the source file
            builder.add_src("../examples/padd.s")
            # Set registers a0 to a5 with p1 and p2 coordinates
            # a0, a1, a2 for p1_x, p1_y, p1_z
            # a3, a4, a5 for p2_x, p2_y, p2_z

            regs_set = ['a0', 'a1', 'a2', 'a3', 'a4', 'a5']
            p_coords = p1_coords + p2_coords
            for reg, val in zip(regs_set, p_coords):
                builder.add_set(reg, val)

            # Set 'check' registers r0 to r2 with expected result point p3_x, p3_y, p3_z
            regs_check = ['r0', 'r1', 'r2']
            for reg, val in zip(regs_check, p3_coords):
                builder.add_check(reg, val)

    builder.write_json(output_json_file)

create_golden_json("golden.data", "test.json")