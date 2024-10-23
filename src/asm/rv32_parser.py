import re

from asm.instr_info import rv32i
from comm.logging import *
from asm.reg_info import is_reg, reg_map
from typing import Dict
__all__ = ['Parser']

class _Parser:

	def __call__(self, *args) -> list:
		if len(args) < 2:
			raise Exception('rv32 instruction parser requires at least code string and symbol table as input!')

		code_arr = args[0]
		symbol_table = args[1]
		base_addr = args[2] if len(args) > 2 else 0  # 0x0 for base offset by default
		parsed = _Parser.translate(code_arr, symbol_table, base_addr)
		return parsed

	@staticmethod
	def translate(code: list, st: Dict[str, int], base: int) -> list:

		def resolve_link_addr(_tk: str):
			for key, value in st.items():
				if key in _tk:
					_tk = _tk.replace(key, str(value))
			return _tk

		int_code = []
		code = [e.strip() for e in code]
		for line_num, line in enumerate(code):
			DEBUG_INFO(f'Interpreting: {line}')
			tokens = _Parser.tokenize(line)

			# Evaluate expressions and link labels
			new_tokens = [tokens[0]]  # Opcode remains the same
			for token in tokens[1:]:
				# attempt to resolve linked addresses
				token = resolve_link_addr(token)

				# handle register alias names
				token = reg_map(token) if is_reg(token) else token

				new_tokens.append(token)

			tokens = new_tokens

			if tokens:
				encoded_instruction = _Parser.encode(tokens)
				int_code.append(encoded_instruction)
				DEBUG_INFO('Succeeded!')
		return int_code

	@staticmethod
	def tokenize(line: str) -> list:
		# instruction, rest = line.strip().split(' ', 1)
		instruction, _, rest = line.strip().partition(' ')

		# Split the rest by commas
		arg_tokens = re.split(r',\s*', rest)

		# Process tokens that might have nested operations (like within parentheses)
		tokens = [instruction] + [token.strip() for token in arg_tokens]
		tokens = [token.lower() for token in tokens if token]  # to keep it simple, our assembler is case-insensitive !!
		return tokens

	@staticmethod
	def encode(tokens : list) -> str:
		return rv32i.parse(op=tokens[0], args=tokens[1:])

# re patterns
# Define the pattern for immediate in binary, hex, octal, or decimal formats
pat_imm = r'(0[bB][01]+|0[xX][0-9a-fA-F]+|0[oO][0-7]+|[1-9][0-9]*|0)'

# Define the pattern for supported operators, note: don't support ()
pat_op = r'(?:\+|\-|\*|/|<<|>>)'  # Non-capturing group for operators

# Approximate pattern for expressions with parentheses (does not ensure balanced parentheses)
pat_expr = r'^\s*(?:' + pat_imm + r'|\s*\(\s*' + pat_imm + r'\s*\))' \
           r'(?:\s*' + pat_op + r'\s*(?:' + pat_imm + r'|\s*\(\s*' + pat_imm + r'\s*\)))*\s*$'


Parser = _Parser()

