
import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Optional
from riscv_assembler.rv32_parser import *
from riscv_assembler.utils import write_to_file
from riscv_assembler.common import *

__all__ = ['EmitCodeMode', 'RV32Backend']


class EmitCodeMode(Enum):
    HEX = 'hex'  # hexadecimal
    BIN = 'bin'  # binary
    LST = 'lst'  # list
    NIB = 'nib'  # nibble


class AsmBackend(ABC):
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

        # macros
        self._macros = {}

    @property
    def lines(self) -> List[str]:
        return self._lines

    @lines.setter
    def lines(self, lines: List[str]):
        self._lines = lines

    @property
    def macros(self):
        return self._macros

    @macros.setter
    def macros(self, macros):
        self._macros = macros

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
    def parse_lines(self, asm: Optional[str]):
        """
            Invoke Parser class to parse the assembly lines.
            A preprocess procedure is recommended, if assembly code is not given in a specific backend impl.
        """
        pass

    @abstractmethod
    def emit_code(self, mod: EmitCodeMode):
        """
        Subclasses should implement this method to emit the
        machine code using the parsed lines and symbol table.
        """
        pass


class RV32Backend(AsmBackend):

    def __init__(self, lines: str, base_addr: int):
        super().__init__(base_addr)
        self.preproc(lines)

    def preproc(self, input: str):
        """
        This preprocess handles the input RV32I assembly code as a string and does the following:
        1) Keeps the original lines in the self.lines property.
        2) Uses regex patterns to match the RV32I translatable lines, removes all blank spaces, comments,
           and saves the translatable lines' original indices into self.translatable_indices property.
        3) Saves the assembly of translatable lines into self.mnemonics property.
        4) Collects all labels and saves them into the self.symbol_table property.
        5) Replaces all places where macros should be expanded.
        """
        # Split the input into lines and store them
        self.lines = input.splitlines()

        # Patterns for processing
        macro_def_pattern = re.compile(r'^\s*\.macro\s+(\w+)(?:\s+(.*))?')
        macro_end_pattern = re.compile(r'^\s*\.endm')
        label_pattern = re.compile(r'^(\w+):\s*(.*)')
        directive_pattern = re.compile(r'^\s*\.(\w+)\b\s*(.*)')
        comment_pattern = re.compile(r'(;|#).*')
        whitespace_pattern = re.compile(r'\s+')

        in_macro = False
        macro_name = ''
        macro_args = []
        translatable_line_cnt = 0  # actual code to be assembled

        # Iterate over each line
        for idx, line in enumerate(self.lines):
            line = self.lines[idx]
            original_line = line  # Keep the original line for reference
            line = re.sub(r'[;#].*', '', line).strip() # Remove comments (anything after '#' or ';')
            if not line:
                continue # Skip empty lines

            #region Handle macro definitions first
            if not in_macro:
                macro_def_match = macro_def_pattern.match(line)
                if macro_def_match:
                    in_macro = True
                    macro_name = macro_def_match.group(1)
                    macro_args_line = macro_def_match.group(2)
                    if macro_args_line:
                        # Remove slashes and split
                        macro_args = macro_args_line.replace(',','').strip().split()
                        # current_macro_args = [arg.lstrip('/ ') for arg in macro_args]
                    else:
                        macro_args = []

                    macro_lines = []
                    continue  # Move to the next line
            else:
                # Inside a macro definition
                if macro_end_pattern.match(line):
                    in_macro = False
                    self.macros[macro_name] = {
                        'args': macro_args,
                        'lines': macro_lines
                    }
                    macro_name = ''
                    macro_args = []
                    macro_lines = []
                    continue

                # Continue collecting macro lines
                macro_lines.append(line)
                continue
            #endregion

            #region todo> Handle assembler directives
            directive_match = directive_pattern.match(line)
            if directive_match:
                directive_name = directive_match.group(1)
                directive_args = directive_match.group(2)
                self.handle_directives(directive_name, directive_args) # impl. macro definition and end pattern in here
                continue
            #endregion

            # region Handle label definitions
            label_match = label_pattern.match(line)
            if label_match:
                label_name = label_match.group(1)
                self.symbol_table[label_name] = translatable_line_cnt  # label => its next translatable line
                # Remove the label from the line for further processing
                line = line[label_match.end():].strip()
                if not line:
                    continue  # If nothing left after label, move to next line
            # endregion

            # Expand macros
            expanded_lines = self.expand_macros(line).split('\n')

            #region Handle translatable instruction
            for line in expanded_lines:
                if not self.is_translatable_line(line):
                    raise ValueError(f'Unknown assembly code detected {line}!')

                # Remove extra whitespaces
                line = whitespace_pattern.sub(' ', line).strip()
                # Save the index and mnemonic
                self.translatable_indices.append(idx)
                self.mnemonics.append(line)
                translatable_line_cnt += 1
            #endregion

        DEBUG_INFO(f'Preprocess is completed with {translatable_line_cnt} assembly instructions in total')

    def handle_directives(self, directive_name: str, directive_args: str):
        pass

    def is_translatable_line(self, line: str) -> bool:
            """
            Determines if a given assembly code line can be translated into RISC-V assembly code.
            RISC-V mnemonics can include letters, numbers, and periods (e.g., 'fadd.s')

            Args:
                line (str): A string representation of an assembly code line.

            Returns:
                bool: True if the line can be lowered into RISC-V assembly code, False otherwise.
            """
            instruction_pattern = re.compile(r'^[a-zA-Z]+(?:\.[a-zA-Z0-9]+)?$')
            mnemonics = line.split()[0]

            # Match the line against the instruction pattern
            return instruction_pattern.match(mnemonics) is not None

    def expand_macros(self, line: str) -> str:
        """
        Replaces macro invocations in the line with their definitions.
        """
        tokens = line.strip().replace(',','').split()
        if not tokens:
            return line

        mnemonic = tokens[0]
        args = tokens[1:] if len(tokens) > 1 else []

        # todo> handle macro expansion and type of self.macros
        if mnemonic in self.macros:
            # Expand the macro
            macro = self.macros[mnemonic]
            macro_lines = macro['lines']
            macro_args = macro['args']

            # Create a mapping from macro arguments to actual arguments
            arg_map = dict(zip(macro_args, args))

            # Expand each line of the macro
            expanded_lines = []
            for macro_line in macro_lines:
                # Replace arguments in the macro line
                for arg_name, arg_value in arg_map.items():
                    macro_line = macro_line.replace(f'\\{arg_name}', arg_value)
                expanded_lines.append(macro_line)

            # Join the expanded lines into a single string
            return '\n'.join(expanded_lines)

        return line  # No macro expansion needed

    def parse_lines(self, asm: Optional[str] = None):
        DEBUG_INFO(f'Passing assembly lines from {input}')
        parsed = Parser(self.mnemonics, self.symbol_table)
        if len(parsed) <= 0:
            raise ValueError(f'Provided input: {input} yielded nothing from parser. Check input.')

        self.encoded = parsed


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
