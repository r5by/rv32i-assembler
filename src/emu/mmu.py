"""
RiscEmu (c) 2021 Anton Lydike

SPDX-License-Identifier: MIT
"""

from typing import Dict, List, Optional, Union

from comm.int32 import Int32, UInt32
from . import (
    Instruction,
    T_AbsoluteAddress,
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
    base: int
    size: int

    def __init__(self, base_addr, symbol_table):
        """
        Create a new MMU
        """
        self.st = symbol_table
        self.base = base_addr
        self.program = {} # abs_addr => translatable assembly code

    def read_ins(self, addr: T_AbsoluteAddress) -> Instruction:
        """
        Read a single instruction located at addr

        :param addr: The location
        :return: The Instruction
        """
        return self.program[addr]

    def read(self, addr: Union[int, Int32], size: int) -> bytearray:
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

    def dump(self, addr, *args, **kwargs):
        """
        Dumpy the memory contents

        :param addr: The address at which to dump
        :param args: args for the dump function of the loaded memory section
        :param kwargs: kwargs for the dump function of the loaded memory section
        """
        pass

    def load_program(self, asms, align_to: int = 4):
        for addr, asm_cano in asms.items():
            instr_name = asm_cano[0]
            instr_args = asm_cano[1]
            trans_instr = TranslatableInstruction(name=instr_name, args=instr_args, addr=addr)
            self.program[addr] = trans_instr


    def find_entrypoint(self) -> Optional[int]:
        return self.base