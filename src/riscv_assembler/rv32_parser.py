import re
from riscv_assembler.instr_info import *
from riscv_assembler.common import *
from types import FunctionType as function
from typing import Dict, List
__all__ = ['Parser']

class _Parser:

	def __call__(self, *args) -> list:
		if len(args) < 2:
			raise Exception('rv32 instruction parser requires code string and symbol table as input!')

		code_arr = args[0]
		symbol_table = args[1]
		parsed = _Parser.translate(code_arr, symbol_table)
		return parsed



	@staticmethod
	def preprocess(code : list) -> None:

		pass

	@staticmethod
	def is_translatable_line(line: str) -> bool:
		"""
		todo> update the res from pass
        Determines if a given assembly code line can be translated into RISC-V assembly code.

        Args:
            line (str): A string representation of an assembly code line.

        Returns:
            bool: True if the line can be lowered into RISC-V assembly code, False otherwise.
        """
		# Remove comments (anything after '#' or ';')
		line = re.sub(r'[;#].*', '', line)

		# Strip leading and trailing whitespace
		line = line.strip()

		# If the line is empty after stripping, it's not translatable
		if not line:
			return False

		# Check for label definitions (ends with ':')
		if line.endswith(':'):
			return False

		# Split the line at the first colon to separate labels from code
		if ':' in line:
			# This handles labels and instructions on the same line
			_, code_part = line.split(':', 1)
			line = code_part.strip()
			# If there's nothing after the label, it's just a label definition
			if not line:
				return False

		# Check for assembler directives (starts with '.')
		if line.startswith('.'):
			return False

		# todo>
		#  preprocess macro
		#  Check for macro definitions (e.g., '.macro') or macro invocations
		# Assuming macros are defined with '.macro' and invoked by name
		# Since we cannot distinguish macro invocations from instructions without context,
		# we'll consider lines starting with '.macro' or '.endm' as non-translatable
		# if re.match(r'\s*\.macro\b', line) or re.match(r'\s*\.endm\b', line):
		# 	return False

		# At this point, we assume the line is likely an instruction
		# We can attempt to match the line against a pattern of RISC-V instructions

		# Define a regular expression pattern for RISC-V instructions
		# RISC-V mnemonics can include letters, numbers, and periods (e.g., 'fadd.s')
		instruction_pattern = re.compile(r'^[a-zA-Z]+(?:\.[a-zA-Z0-9]+)?$')
		mnemonics = line.split()[0]

		# Match the line against the instruction pattern
		if instruction_pattern.match(mnemonics):
			return True

		return False


	@staticmethod
	def handle_inline_comments(x : str) -> str:
		if "#" in x:
			pos = x.index("#")
			if pos != 0 and pos != len(x)-1:
				return x[0:pos].replace(',', ' ')
		return x.replace(',', ' ')

	@staticmethod
	def handle_specific_instr(x : list) -> list:
		# todo>
		# for sw, lw, lb, lh, sb, sh
		if len(x[0]) == 2 and (x[0] in S_instr or x[0] in I_instr):
			y = x[-1].split('('); y[1] = y[1].replace(')','')
			return x[0:-1] + y
		elif 'requires jump' == 5:
			...

		return x


	@staticmethod
	def translate(code: list, st: Dict[str, int]) -> list:
		# todo> handle jmp, mv
		int_code = []
		code = [e.strip() for e in code]
		for line_num, line in enumerate(code):
			DEBUG_INFO(f'Interpreting: {line}')
			tokens = _Parser.tokenize(line)
			int_code += [_Parser.interpret(tokens) for _ in range(1) if len(tokens) != 0]
			DEBUG_INFO(f'succeed!')

		return int_code

	@staticmethod
	def tokenize(line : str) -> list:
		tokens = [token.lower() for token in line.replace(',', '').split()]
		tokens = _Parser.handle_specific_instr(tokens)
		return tokens

	@staticmethod
	def interpret(tokens : list) -> str:
		f = _Parser.determine_type(tokens[0])
		return f(tokens)

	@staticmethod
	def determine_type(tk : str) -> function:
		'''
			In interpret(), determine which instruction set is being used
			and return the appropriate parsing function.
		'''
		instr_sets = [R_instr, I_instr, S_instr, SB_instr, U_instr, UJ_instr, pseudo_instr]
		parsers = [Rp, Ip, Sp, SBp, Up ,UJp, Psp]
		for i in range(len(instr_sets)):
			if tk in instr_sets[i]:
				return parsers[i]
		raise Exception("Bad Instruction Provided: " + tk + "!")

Parser = _Parser()