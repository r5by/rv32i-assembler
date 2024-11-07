from tests.filecheck import get_conf
from comm.utils import get_filelist_with_pattern
from asm.asm_backend import RV32Backend
from emu.emulator import RV32IEmulator
from comm.exceptions import RV32IBaseException
from comm.logging import *

BASE_ADDR = 0x80100

def run_example(input_file):
    # read-in source assembly
    with open(input_file, 'r') as file:
        assembly_code = file.read()

    # create rv32i asm backend
    try:
        mc = RV32Backend(lines=assembly_code, base_addr=BASE_ADDR)
        mc.parse_lines()
    except RV32IBaseException as e:
        ERROR("Error: {}".format(e.message()))
        e.print_stacktrace()
        sys.exit(-1)


    # init emulator
    emulator = RV32IEmulator(mc)

    emulator.instantiate_cpu()
    emulator.load_programs()
    emulator.launch()
    sys.exit(0)


if __name__ == '__main__':
    exp_dir = get_conf(key='EXP_DIR')

    examples = get_filelist_with_pattern(pat='*.asm', src_dir=exp_dir)
    for exp_file in examples:
        run_example(input_file=exp_file)