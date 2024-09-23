import re

from riscv_assembler.common import DEBUG_INFO
from riscv_assembler.utils import load_json_config
from enum import Enum, auto
from typing import Dict, List, Union, Callable
from abc import ABC, abstractmethod
from riscv_assembler.reg_info import reg_map

__all__ = ['RV32InstrInfo']

# Enum for instruction types
class InstructionType(Enum):
    R = auto()
    I = auto()
    S = auto()
    B = auto()
    U = auto()
    J = auto()
    # Additional types can be added here if needed

# Base class
class InstrInfo(ABC):
    def __init__(self, isa_config_file: str):
        self.instr_map: Dict[str, InstructionType] = {}
        self.load_isa_config(isa_config_file)

    def load_isa_config(self, isa_config_file: str):
        isa_config = load_json_config(isa_config_file)

        # Map each mnemonic to its instruction type
        for instr_type_str, mnemonics in isa_config.items():
            instr_type = InstructionType[instr_type_str]
            for mnemonic in mnemonics:
                self.instr_map[mnemonic] = instr_type

    @abstractmethod
    def parse(self, *args, **kwargs):
        pass

# Derived class
class RV32InstrInfo(InstrInfo):
    def __init__(self, isa_config_file: str):
        super().__init__(isa_config_file)

    def parse(self, op: str, args: List[Union[str, int]]) -> str:
        """
        Parses an instruction and returns its binary representation.

        Args:
            op (str): The instruction mnemonic.
            args (List[Union[str, int]]): List of arguments for the instruction.

        Returns:
            str: Binary representation of the instruction.
        """
        if op not in self.instr_map:
            raise ValueError(f"Unsupported instruction '{op}'")

        instr_type = self.instr_map[op]
        DEBUG_INFO(f'determining type of {op}: {instr_type.name}')
        parse_method = self.get_parse_method(instr_type)
        return parse_method(op, args)

    def get_parse_method(self, instr_type: InstructionType) -> Callable:
        parse_methods = {
            InstructionType.R: self.parse_R_type,
            InstructionType.I: self.parse_I_type,
            InstructionType.S: self.parse_S_type,
            InstructionType.B: self.parse_B_type,
            InstructionType.U: self.parse_U_type,
            InstructionType.J: self.parse_J_type,
        }
        return parse_methods.get(instr_type, self.unsupported_instruction_type)

    def unsupported_instruction_type(self, *args, **kwargs):
        raise NotImplementedError("Unsupported instruction type.")

    @staticmethod
    def extract_reg_num(reg_name: str) -> int:
        # reg_name = reg_map(reg_alias)
        reg_pattern = r'x(\d+)$'
        match = re.match(reg_pattern, reg_name)
        if not match:
            raise ValueError(f"Invalid register name '{reg_name}'")
        return int(match.group(1))
    
    @staticmethod
    def extract_imm_num(imm_expr: str) -> str:
        if imm_expr.startswith('%hi') or imm_expr.startswith('%pcrel_hi'):
            pat_hi = r'%(hi|pcrel_hi)\((.*?)\)'
            content = re.match(pat_hi, imm_expr).group(2)
            remain = re.sub(pat_hi, lambda match: str(eval(content) >> 12), imm_expr)
        elif imm_expr.startswith('%lo') or imm_expr.startswith('%pcrel_lo'):
            pat_lo = r'%(lo|pcrel_lo)\((.*?)\)'
            content = re.match(pat_lo, imm_expr).group(2)
            remain = re.sub(pat_lo, lambda match: str(eval(content) & 0xfff), imm_expr)
        else:
            remain = eval(imm_expr) if is_expr(imm_expr) else imm_expr
            
        return remain

    @staticmethod
    def extract_imm_reg(imm_expr: str) -> (int, str):
        remain = RV32InstrInfo.extract_imm_num(imm_expr)

        pat_num_paren = r'^(.*)\(([^()]*)\)\s*$'  # i.e. 4(x3) or 0x800(x2)
        match = re.search(pat_num_paren, remain)
        if not match:
            raise ValueError(f'imm(reg) format is not found in expression: {imm_expr}')

        imm = match.group(1).strip()  # Content before the parentheses
        reg = reg_map(match.group(2))

        imm = eval(imm) if is_expr(imm) else int(imm)
        return imm, reg

    # Parsing methods for each instruction type
    def parse_S_type(self, op: str, args: List[Union[str, int]]) -> str:
        """
        Parses an S-type instruction.

        Args:
            op (str): Instruction mnemonic.
            args (List[Union[str, int]]): [rs2, imm, rs1]

        Returns:
            str: Binary representation of the instruction.
        """
        # S-type instructions mapping
        instr_map = {
            'sb': {'funct3': 0b000, 'opcode': 0b0100011},
            'sh': {'funct3': 0b001, 'opcode': 0b0100011},
            'sw': {'funct3': 0b010, 'opcode': 0b0100011},
            # Add other S-type instructions if necessary
        }

        if op not in instr_map:
            raise ValueError(f"Unsupported S-type instruction '{op}'")

        funct3 = instr_map[op]['funct3']
        opcode = instr_map[op]['opcode']

        # Expected argument order: rs2 (source register), imm (offset), rs1 (base register)
        if len(args) == 3:
            rs2, rs1, imm = args
        elif len(args) == 2:
            rs2 = args[0]
            imm, rs1 = RV32InstrInfo.extract_imm_reg(args[1])

        rs1_num = RV32InstrInfo.extract_reg_num(rs1)
        rs2_num = RV32InstrInfo.extract_reg_num(rs2)

        # Handle immediate value (12 bits, sign-extended)
        imm_12 = int(imm) & 0xFFF  # Mask to 12 bits

        # Split immediate into imm[11:5] and imm[4:0]
        imm_11_5 = (imm_12 >> 5) & 0x7F  # 7 bits
        imm_4_0 = imm_12 & 0x1F          # 5 bits

        # Assemble the instruction bits
        instruction = (
            (imm_11_5 << 25) |
            (rs2_num << 20) |
            (rs1_num << 15) |
            (funct3 << 12) |
            (imm_4_0 << 7) |
            opcode
        )

        # Convert the instruction to a 32-bit binary string
        bin_instr = format(instruction, '032b')
        DEBUG_INFO(f'binary encoding completed: {bin_instr}')

        return bin_instr

    def parse_R_type(self, op: str, args: List[Union[str, int]]) -> str:
        """
        Parses an R-type instruction.

        Args:
            op (str): Instruction mnemonic.
            args (List[Union[str, int]]): [rd, rs1, rs2]

        Returns:
            str: Binary representation of the instruction.
        """
        # R-type instructions mapping
        instr_map = {
            'add': {'funct7': 0b0000000, 'funct3': 0b000, 'opcode': 0b0110011},
            'sub': {'funct7': 0b0100000, 'funct3': 0b000, 'opcode': 0b0110011},
            'sll': {'funct7': 0b0000000, 'funct3': 0b001, 'opcode': 0b0110011},
            'slt': {'funct7': 0b0000000, 'funct3': 0b010, 'opcode': 0b0110011},
            'sltu': {'funct7': 0b0000000, 'funct3': 0b011, 'opcode': 0b0110011},
            'xor': {'funct7': 0b0000000, 'funct3': 0b100, 'opcode': 0b0110011},
            'srl': {'funct7': 0b0000000, 'funct3': 0b101, 'opcode': 0b0110011},
            'sra': {'funct7': 0b0100000, 'funct3': 0b101, 'opcode': 0b0110011},
            'or': {'funct7': 0b0000000, 'funct3': 0b110, 'opcode': 0b0110011},
            'and': {'funct7': 0b0000000, 'funct3': 0b111, 'opcode': 0b0110011},
            # Add other R-type instructions if necessary
        }

        if op not in instr_map:
            raise ValueError(f"Unsupported R-type instruction '{op}'")

        funct7 = instr_map[op]['funct7']
        funct3 = instr_map[op]['funct3']
        opcode = instr_map[op]['opcode']

        # Expected argument order: rd (destination register), rs1, rs2
        if len(args) != 3:
            raise ValueError(f"Expected 3 arguments for R-type instruction '{op}', got {len(args)}")

        rd, rs1, rs2 = args

        rd_num = RV32InstrInfo.extract_reg_num(rd)
        rs1_num = RV32InstrInfo.extract_reg_num(rs1)
        rs2_num = RV32InstrInfo.extract_reg_num(rs2)

        # Assemble the instruction bits
        instruction = (
                (funct7 << 25) |
                (rs2_num << 20) |
                (rs1_num << 15) |
                (funct3 << 12) |
                (rd_num << 7) |
                opcode
        )

        # Convert the instruction to a 32-bit binary string
        bin_instr = format(instruction, '032b')
        DEBUG_INFO(f'binary encoding completed: {bin_instr}')

        return bin_instr

    def parse_I_type(self, op: str, args: List[Union[str, int]]) -> str:
        """
        Parses an I-type instruction.

        Args:
            op (str): Instruction mnemonic.
            args (List[Union[str, int]]): [rd, rs1, imm]

        Returns:
            str: Binary representation of the instruction.
        """
        # I-type instructions mapping
        instr_map = {
            'addi': {'funct3': 0b000, 'opcode': 0b0010011},
            'xori': {'funct3': 0b100, 'opcode': 0b0010011},
            'ori':  {'funct3': 0b110, 'opcode': 0b0010011},
            'andi': {'funct3': 0b111, 'opcode': 0b0010011},
            'slti': {'funct3': 0b010, 'opcode': 0b0010011},
            'sltiu':{'funct3': 0b011, 'opcode': 0b0010011},
            'slli': {'funct3': 0b001, 'opcode': 0b0010011, 'funct7': 0b0000000},
            'srli': {'funct3': 0b101, 'opcode': 0b0010011, 'funct7': 0b0000000},
            'srai': {'funct3': 0b101, 'opcode': 0b0010011, 'funct7': 0b0100000},
            'lb':   {'funct3': 0b000, 'opcode': 0b0000011},
            'lh':   {'funct3': 0b001, 'opcode': 0b0000011},
            'lw':   {'funct3': 0b010, 'opcode': 0b0000011},
            'lbu':  {'funct3': 0b100, 'opcode': 0b0000011},
            'lhu':  {'funct3': 0b101, 'opcode': 0b0000011},
            'jalr': {'funct3': 0b000, 'opcode': 0b1100111},
            'ecall': {'funct3': 0b000, 'opcode': 0b1110011, 'funct7': 0b0000000},
            'ebreak': {'funct3': 0b000, 'opcode': 0b1110011, 'funct7': 0b0000001},
        }

        if op not in instr_map:
            raise ValueError(f"Unsupported I-type instruction '{op}'")

        instr_info = instr_map[op]
        funct3 = instr_info['funct3']
        opcode = instr_info['opcode']
        funct7 = instr_info.get('funct7', None)

        if len(args) == 3:
            rd, rs1, imm = args
            imm = RV32InstrInfo.extract_imm_num(imm)
        elif len(args) == 2:
            rd = args[0]
            imm, rs1 = RV32InstrInfo.extract_imm_reg(args[1])

        if op in ['slli', 'srli', 'srai']:
            shamt = imm
            rd_num = RV32InstrInfo.extract_reg_num(rd)
            rs1_num = RV32InstrInfo.extract_reg_num(rs1)
            shamt_6 = int(shamt) & 0x3F  # Mask to 6 bits

            # Assemble the instruction bits
            instruction = (
                (funct7 << 25) |
                (shamt_6 << 20) |
                (rs1_num << 15) |
                (funct3 << 12) |
                (rd_num << 7) |
                opcode
            )
        elif op == 'jalr':
            # JALR instruction: rd, rs1, imm
            # todo> support all forms of jalr instructions:
            # 1) jalr rd, imm, rs1          [yes]
            # 2) jalr rd, imm(rs)           [no]
            # 3) jalr rd, %lo(imm)(rs1)     [no]
            rd_num = RV32InstrInfo.extract_reg_num(rd)
            rs1_num = RV32InstrInfo.extract_reg_num(rs1)

            imm_12 = int(imm) & 0xFFF  # Mask to 12 bits
            # Assemble the instruction bits
            instruction = (
                (imm_12 << 20) |
                (rs1_num << 15) |
                (funct3 << 12) |
                (rd_num << 7) |
                opcode
            )
        elif op in ['lb', 'lh', 'lw', 'lbu', 'lhu']:
            # Load instructions: rd, imm, rs1
            rd_num = RV32InstrInfo.extract_reg_num(rd)
            rs1_num = RV32InstrInfo.extract_reg_num(rs1)

            imm_12 = int(imm) & 0xFFF  # Mask to 12 bits

            # Assemble the instruction bits
            instruction = (
                (imm_12 << 20) |
                (rs1_num << 15) |
                (funct3 << 12) |
                (rd_num << 7) |
                opcode
            )
        elif op in ['ecall', 'ebreak']:
            # System instructions
            # ecall and ebreak have fixed encodings
            # For simplicity, we can hardcode their encodings
            # ecall: opcode=0b1110011, funct3=0b000, imm=0
            # ebreak: opcode=0b1110011, funct3=0b000, imm=1

            imm_12 = 0 if op == 'ecall' else 1
            rd_num = 0
            rs1_num = 0

            # Assemble the instruction bits
            instruction = (
                (imm_12 << 20) |
                (rs1_num << 15) |
                (funct3 << 12) |
                (rd_num << 7) |
                opcode
            )
        else:
            # Standard I-type instructions: rd, rs1, imm
            rd_num = RV32InstrInfo.extract_reg_num(rd)
            rs1_num = RV32InstrInfo.extract_reg_num(rs1)
            imm_12 = int(imm) & 0xFFF  # Mask to 12 bits

            # Assemble the instruction bits
            instruction = (
                (imm_12 << 20) |
                (rs1_num << 15) |
                (funct3 << 12) |
                (rd_num << 7) |
                opcode
            )

        # Convert the instruction to a 32-bit binary string
        bin_instr = format(instruction, '032b')
        DEBUG_INFO(f'binary encoding completed: {bin_instr}')

        return bin_instr

    def parse_B_type(self, op: str, args: List[Union[str, int]]) -> str:
        """
        Parses a B-type instruction.

        Args:
            op (str): Instruction mnemonic.
            args (List[Union[str, int]]): [rs1, rs2, imm]

        Returns:
            str: Binary representation of the instruction.
        """
        # B-type instructions mapping
        instr_map = {
            'beq':  {'funct3': 0b000, 'opcode': 0b1100011},
            'bne':  {'funct3': 0b001, 'opcode': 0b1100011},
            'blt':  {'funct3': 0b100, 'opcode': 0b1100011},
            'bge':  {'funct3': 0b101, 'opcode': 0b1100011},
            'bltu': {'funct3': 0b110, 'opcode': 0b1100011},
            'bgeu': {'funct3': 0b111, 'opcode': 0b1100011},
            # Add other B-type instructions if necessary
        }

        if op not in instr_map:
            raise ValueError(f"Unsupported B-type instruction '{op}'")

        funct3 = instr_map[op]['funct3']
        opcode = instr_map[op]['opcode']

        # Expected argument order: rs1, rs2, imm (offset)
        if len(args) != 3:
            raise ValueError(f"Expected 3 arguments for B-type instruction '{op}', got {len(args)}")

        rs1, rs2, imm = args

        rs1_num = RV32InstrInfo.extract_reg_num(rs1)
        rs2_num = RV32InstrInfo.extract_reg_num(rs2)
        imm_13 = int(imm) & 0x1FFF  # Mask to 13 bits

        # Extract bits of the immediate value
        imm_12 = (imm_13 >> 12) & 0x1    # Bit 12
        imm_10_5 = (imm_13 >> 5) & 0x3F  # Bits 10-5
        imm_4_1 = (imm_13 >> 1) & 0xF    # Bits 4-1
        imm_11 = (imm_13 >> 11) & 0x1    # Bit 11

        # Assemble the immediate in the correct positions
        imm_31_25 = (imm_12 << 6) | imm_10_5  # Bits 31-25
        imm_11_7 = (imm_11 << 6) | imm_4_1    # Bits 11-7

        # Assemble the instruction bits
        instruction = (
            (imm_31_25 << 25) |
            (rs2_num << 20) |
            (rs1_num << 15) |
            (funct3 << 12) |
            (imm_11_7 << 7) |
            opcode
        )

        # Convert the instruction to a 32-bit binary string
        bin_instr = format(instruction, '032b')
        DEBUG_INFO(f'binary encoding completed: {bin_instr}')

        return bin_instr

    def parse_U_type(self, op: str, args: List[Union[str, int]]) -> str:
        """
        Parses a U-type instruction.

        Args:
            op (str): Instruction mnemonic.
            args (List[Union[str, int]]): [rd, imm]

        Returns:
            str: Binary representation of the instruction.
        """
        # U-type instructions mapping
        instr_map = {
            'lui': {'opcode': 0b0110111},
            'auipc': {'opcode': 0b0010111},
            # Add other U-type instructions if necessary
        }

        if op not in instr_map:
            raise ValueError(f"Unsupported U-type instruction '{op}'")

        opcode = instr_map[op]['opcode']

        # Expected argument order: rd (destination register), imm (immediate value)
        if len(args) != 2:
            raise ValueError(f"Expected at least 2 arguments for U-type instruction '{op}', got {len(args)}")


        rd, imm = args

        if imm.startswith('%'):
            pat_hi = r'%(hi|pcrel_hi)\((.*?)\)'
            imm = re.sub(pat_hi, lambda match: match.group(2), imm)
            imm += '>> 12'  # effectively shift num>>12 to get the upper 20 bits of the given number

        imm = eval(imm) if is_expr(imm) else int(imm)

        rd_num = RV32InstrInfo.extract_reg_num(rd)
        imm_20 = int(imm) & 0xFFFFF  # Mask to 20 bits

        # Assemble the instruction bits
        instruction = (
                (imm_20 << 12) |
                (rd_num << 7) |
                opcode
        )

        # Convert the instruction to a 32-bit binary string
        bin_instr = format(instruction, '032b')
        DEBUG_INFO(f'binary encoding completed: {bin_instr}')

        return bin_instr

    def parse_J_type(self, op: str, args: List[Union[str, int]]) -> str:
        """
        Parses a J-type instruction.

        Args:
            op (str): Instruction mnemonic.
            args (List[Union[str, int]]): [rd, imm]

        Returns:
            str: Binary representation of the instruction.
        """
        # J-type instructions mapping
        instr_map = {
            'jal': {'opcode': 0b1101111},
            # Add other J-type instructions if necessary
        }

        if op not in instr_map:
            raise ValueError(f"Unsupported J-type instruction '{op}'")

        opcode = instr_map[op]['opcode']

        # Expected argument order: rd (destination register), imm (immediate value)
        if len(args) != 2:
            raise ValueError(f"Expected 2 arguments for J-type instruction '{op}', got {len(args)}")

        rd, imm = args
        imm = eval(imm) if is_expr(imm) else int(imm)

        rd_num = RV32InstrInfo.extract_reg_num(rd)
        imm_21 = int(imm) & 0x1FFFFF  # Mask to 21 bits

        # Extract bits of the immediate value
        imm_20 = (imm_21 >> 20) & 0x1  # Bit 20
        imm_10_1 = (imm_21 >> 1) & 0x3FF  # Bits 10-1
        imm_11 = (imm_21 >> 11) & 0x1  # Bit 11
        imm_19_12 = (imm_21 >> 12) & 0xFF  # Bits 19-12

        # Assemble the immediate in the correct positions
        imm_field = (
                (imm_20 << 31) |
                (imm_19_12 << 12) |
                (imm_11 << 20) |
                (imm_10_1 << 21)
        )

        # Assemble the instruction bits
        instruction = (
                imm_field |
                (rd_num << 7) |
                opcode
        )

        # Adjust the immediate field to the correct positions
        instruction = (
                ((imm_20 << 31) |
                 (imm_19_12 << 12) |
                 (imm_11 << 20) |
                 (imm_10_1 << 21)) |
                (rd_num << 7) |
                opcode
        )

        # Shift the bits to their correct positions
        instruction = (
                ((imm_20 & 0x1) << 31) |
                ((imm_19_12 & 0xFF) << 12) |
                ((imm_11 & 0x1) << 20) |
                ((imm_10_1 & 0x3FF) << 21) |
                (rd_num << 7) |
                opcode
        )

        # Convert the instruction to a 32-bit binary string
        bin_instr = format(instruction, '032b')
        DEBUG_INFO(f'binary encoding completed: {bin_instr}')

        return bin_instr


rv32i = RV32InstrInfo('./data/rv32i.json')

def is_expr(input_str: str) -> bool:
    # Define token specifications with 'OP' before 'NUMBER'
    token_specification = [
        ('OP', r'\+|\-|\*|/|<<|>>|&|\||\^'),  # Binary Operators
        ('UNARY_OP', r'~|!'),  # Unary Operators
        ('NUMBER',   r'[+-]?('
                     r'0[bB][01]+|'
                     r'0[xX][0-9a-fA-F]+|'
                     r'0[oO][0-7]+|'
                     r'[1-9][0-9]*|'
                     r'0)'
                     ),   # Integer literals
        ('LPAREN',   r'\('),                  # Left Parenthesis
        ('RPAREN',   r'\)'),                  # Right Parenthesis
        ('SKIP',     r'[ \t]+'),              # Skip over spaces and tabs
        ('MISMATCH', r'.'),                   # Any other character
    ]
    # Compile the regular expressions
    token_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    get_token = re.compile(token_regex).match

    # Tokenize input
    tokens = []
    pos = 0
    mo = get_token(input_str)
    while mo is not None:
        kind = mo.lastgroup
        value = mo.group(kind)
        if kind in ('NUMBER', 'OP', 'UNARY_OP', 'LPAREN', 'RPAREN'):
            tokens.append((kind, value))
        elif kind == 'SKIP':
            pass  # Ignore whitespace
        elif kind == 'MISMATCH':
            return False  # Invalid character
        pos = mo.end()
        mo = get_token(input_str, pos)
    if pos != len(input_str):
        return False  # Unprocessed characters remain

    tokens.append(('EOF', None))  # Add EOF token at the end

    # Define a simple recursive parser
    class Parser:
        def __init__(self, tokens):
            self.tokens = tokens
            self.pos = 0
            self.current_token = self.tokens[self.pos]

        def next_token(self):
            self.pos += 1
            if self.pos < len(self.tokens):
                self.current_token = self.tokens[self.pos]
            else:
                self.current_token = ('EOF', None)

        def expect(self, token_type):
            if self.current_token[0] == token_type:
                self.next_token()
            else:
                raise Exception(f"Expected {token_type}, got {self.current_token}")

        def parse(self) -> bool:
            try:
                self.expression()
                if self.current_token[0] != 'EOF':
                    return False
                return True
            except Exception:
                return False

        def expression(self):
            """Parse an expression consisting of terms and binary operators."""
            self.term()
            while self.current_token[0] == 'OP':
                self.next_token()
                self.term()

        def term(self):
            """Parse a term, which can be a unary operator applied to a factor."""
            while self.current_token[0] == 'UNARY_OP':
                self.next_token()
            self.factor()

        def factor(self):
            """Parse a factor, which can be a number or a parenthesized expression."""
            if self.current_token[0] == 'NUMBER':
                self.next_token()
            elif self.current_token[0] == 'LPAREN':
                self.next_token()
                self.expression()
                self.expect('RPAREN')
            else:
                raise Exception("Expected NUMBER or LPAREN")

    parser = Parser(tokens)
    return parser.parse()
