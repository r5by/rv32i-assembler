from argparse import ArgumentError
from os.path import exists
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Optional
from riscv_assembler.asm_parser import *
from riscv_assembler.utils import write_to_file
from riscv_assembler.common import *

__all__ = ['EmitCodeMode', 'RV32MCEmitter']


class EmitCodeMode(Enum):
    HEX = 'hex'  # hexadecimal
    BIN = 'bin'  # binary
    LST = 'lst'  # list
    NIB = 'nib'  # nibble


class MCEmitter(ABC):
    def __init__(self, base_addr: Optional[int] = 0x0):
        # input lines of asm code
        self._lines: List[str] = []

        # translatable lines of code indices in self._lines
        self._translatable_indices: List[int] = []

        # keep record of translatable lines (assembly code)
        self._mnemonics: List[str] = []

        # (local) symbol table: label=>index
        self._symbol_table: Dict[str, int] = {}

        # base address to calculate offset
        self._base_addr = base_addr

        # encoded instructions in binary format (by default)
        self._encoded: List[str] = []

    @property
    def lines(self) -> List[str]:
        return self._lines

    @lines.setter
    def lines(self, lines: List[str]):
        self._lines = lines

    @property
    def encoded(self) -> List[str]:
        return self._encoded

    @encoded.setter
    def encoded(self, encoded: List[str]):
        self._encoded = encoded

    @property
    def mnemonics(self) -> List[str]:
        return self._mnemonics

    @mnemonics.setter
    def mnemonics(self, mnemonics: List[str]):
        self._mnemonics = mnemonics

    @property
    def translatable_indices(self) -> List[int]:
        return self._translatable_indices

    # @translatable_indices.setter
    # def translatable_indices(self, indices: List[int]):
    #     self._translatable_indices = indices

    @property
    def symbol_table(self) -> Dict[str, int]:
        return self._symbol_table

    @symbol_table.setter
    def symbol_table(self, table: Dict[str, int]):
        self._symbol_table = table

    @property
    def base_addr(self) -> int:
        return self._base_addr

    @base_addr.setter
    def base_addr(self, addr: int):
        self._base_addr = addr

    @abstractmethod
    def parse_lines(self, input: str):
        """
        Subclasses should implement this method to parse
        the lines of assembly code and populate the properties.
        """
        pass

    @abstractmethod
    def emit_code(self, mod: EmitCodeMode):
        """
        Subclasses should implement this method to emit the
        machine code using the parsed lines and symbol table.
        """
        pass


class RV32MCEmitter(MCEmitter):

    def __call__(self, *args):
        self.parse_lines(*args)

    def parse_lines(self, input: str):
        DEBUG_INFO(f'Passing assembly lines from {input}')
        asm, output = Parser(input)
        if len(output) <= 0:
            raise ValueError(f'Provided input: {input} yielded nothing from parser. Check input.')

        self.encoded = output
        self.mnemonics = asm

    def emit_code(self, mode: EmitCodeMode = EmitCodeMode.HEX):

        if mode == EmitCodeMode.HEX:
            DEBUG_INFO("Emitting code in hexadecimal format...")
            return self.apply_hex()
        elif mode == EmitCodeMode.BIN:
            DEBUG_INFO("Emitting code in binary format...")
            return self.encoded
        elif mode == EmitCodeMode.LST:
            DEBUG_INFO("Emitting code in list format...")
            # todo> add list
            return self.to_list()
        elif mode == EmitCodeMode.NIB:
            DEBUG_INFO("Emitting code in nibble format...")
            return self.apply_nibble()
        else:
            raise ValueError("Unsupported EmitCodeMode")

    def apply_nibble(self) -> list:
        return ['\t'.join([elem[i:i + 4] for i in range(0, len(elem), 4)]) for elem in self.encoded]

    def apply_hex(self) -> list:
        return ['0x' + '{:08X}'.format(int(elem, 2)).lower() for elem in self.encoded]

    def to_list(self) -> list:
        # todo>
        return []
