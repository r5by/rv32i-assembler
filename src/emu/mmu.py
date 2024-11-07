"""
RiscEmu (c) 2021 Anton Lydike

SPDX-License-Identifier: MIT
"""

from typing import Dict, List, Optional, Union

from comm.exceptions import InvalidAddressException
from comm.int32 import UInt32
from comm.logging import INFO, ERROR, DEBUG
from comm.colors import FMT_BOLD
from . import (
    Instruction,
    TranslatableInstruction
)

# todo> virtual memory support
class MMU:
    """
    The MemoryManagementUnit. This provides a unified interface for reading/writing data from/to memory.

    It also provides various translations for addresses.
    """

    """
    The maximum size of the memory in bytes
    """
    max_size = 0xFFFFFFFF

    """
    No single allocation can be bigger than 64 MB
    """
    max_alloc_size = 8 * 1024 * 1024 * 64

    """
     The global symbol table
     """
    st: Dict[str, int]  #todo> remove this?

    """
     The program base point
    """
    base: UInt32
    size: int

    def __init__(self, base_addr, symbol_table):
        """
        Create a new MMU
        """
        self.st = symbol_table
        self.base = UInt32(base_addr)
        self.program = {} # abs_addr => translatable assembly code

    def read_ins(self, addr: UInt32) -> Instruction:
        """
        Read a single instruction located at addr

        :param addr: The location
        :return: The Instruction
        """
        DEBUG(f'Reading from 0x{addr:08X}')
        return self.program[addr]

    def read(self, addr: Union[int, UInt32], size: int) -> bytearray:
        """
        Read size bytes of memory at addr

        :param addr: The address at which to start reading
        :param size: The number of bytes to read
        :return: The bytearray at addr
        """
        pass

    def write(self, addr: int, size: int, data: bytearray):
        """
        Write bytes into memory

        :param addr: The address at which to write
        :param size: The number of bytes to write
        :param data: The bytearray to write (only first size bytes are written)
        """
        pass

    def dump(self, addr: UInt32, *args, **kwargs):
        """
        Dumpy the memory contents (instructions only for this simple example)

        :param addr: The address at which to dump
        :param args: args for the dump function of the loaded memory section
        :param kwargs: kwargs for the dump function of the loaded memory section
        """
        if not self.is_valid_addr(addr):
            # don't panic
            return

        t_addr = UInt32(addr)
        mem_instr = self.read_ins(t_addr)
        INFO(
            FMT_BOLD
            + f'0x{addr:08X}: {mem_instr}'
        )


    def load_program(self, asms, align_to: int = 4):
        for addr, asm_cano in asms.items():
            instr_name = asm_cano[0]

            instr_operands = asm_cano[1]
            instr_regs = instr_operands.regs
            instr_imm = instr_operands.imm
            trans_instr = TranslatableInstruction(name=instr_name, addr=addr, regs=instr_regs,  imm=instr_imm)

            self.program[addr] = trans_instr

        self.size = len(asms)

    def find_entrypoint(self) -> Optional[UInt32]:
        return self.base

    def is_valid_addr(self, addr: UInt32) -> bool:
        if addr < self.base:
            ERROR(f'Given address 0x{addr:08X} is below base address 0x{self.base:08X}.')
            return False

        if addr - self.base >> 2 >= self.size:
            ERROR(f'Given address 0x{addr:08X} is out of memory range.')
            return False

        if addr.value & 3 != 0: # address must be aligned to 4 bytes
            ERROR(f'Given address 0x{addr:08X} must be aligned by 4 bytes.')
            return False

        return True
