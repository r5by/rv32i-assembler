from pathlib import Path
import re

from comm.exceptions import InvalidRegisterException


def init_abi_alias():
	path = Path(__file__).parent / "data/reg_abi_alias.dat"
	_map, rmap = {}, {}

	f = open(path, "r")
	line = f.readline()
	while line != "":
		e = line.split()

		_map[e[0]] = e[1]
		rmap[e[1]] = e[0] # reverse map: "x" to alias

		line = f.readline()
	f.close()

	return _map, rmap

abi_alias, alias_abi = init_abi_alias()

# Regular expressions for different cases
dict_pat_reg = {
	"x": re.compile(r"^x([0-9]|[1-2][0-9]|3[0-1])$"),
	"named": re.compile(r"^(zero|ra|sp|gp|tp|fp)$"),
	"a": re.compile(r"^a[0-7]$"),
	"s": re.compile(r"^s([0-9]|1[0-1])$"),
	"t": re.compile(r"^t([0-6])$"),
}

def is_reg(token: str):
	for key, pattern in dict_pat_reg.items():
		if pattern.match(token):
			return True

	return False

def reg_map(reg: str):

	# Check if the register matches any of the valid patterns
	for key, pattern in dict_pat_reg.items():
		if pattern.match(reg):
			# Check and return for x category
			if key == "x":
				return reg
			# For other named registers, return the ABI alias
			return abi_alias[reg]

	# If none of the patterns match, raise an exception
	raise InvalidRegisterException(reg)


def get_alias_name_by_id(gpr_idx: int) -> str:
	return alias_abi[f'x{gpr_idx}']