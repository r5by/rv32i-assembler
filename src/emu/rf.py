from collections import defaultdict

from asm.reg_info import get_alias_name_by_id
from comm.colors import *
from comm.exceptions import InvalidRegisterException
from comm.int32 import Int32, UInt32
from comm.logging import INFO, ERROR

ONE_LINE = False

RF_LEN = 4  # registers in rv32i are all 4 bytes
COL_WIDTH = len("zero=0x00000000")  # dummy entry in each column
COL_SEP = "-"*COL_WIDTH + " "  # column seperator (underline)

class RF:
    """
    Represents RV32I related registers
    """

    valid_regs = {
        "zero": 0,  # Hard-wired zero
        "ra": 1,    # Return address
        "sp": 2,    # Stack pointer
        "gp": 3,    # Global pointer
        "tp": 4,    # Thread pointer
        "t0": 5,    # Temporary/alternate link register
        "t1": 6,    # Temporary
        "t2": 7,    # Temporary
        "s0": 8,    # Saved register/frame pointer
        "fp": 8,    # Frame pointer (alias for s0)
        "s1": 9,    # Saved register
        "a0": 10,   # Function argument/return value
        "a1": 11,   # Function argument/return value
        "a2": 12,   # Function argument
        "a3": 13,   # Function argument
        "a4": 14,   # Function argument
        "a5": 15,   # Function argument
        "a6": 16,   # Function argument
        "a7": 17,   # Function argument
        "s2": 18,   # Saved register
        "s3": 19,   # Saved register
        "s4": 20,   # Saved register
        "s5": 21,   # Saved register
        "s6": 22,   # Saved register
        "s7": 23,   # Saved register
        "s8": 24,   # Saved register
        "s9": 25,   # Saved register
        "s10": 26,  # Saved register
        "s11": 27,  # Saved register
        "t3": 28,   # Temporary
        "t4": 29,   # Temporary
        "t5": 30,   # Temporary
        "t6": 31    # Temporary
    }

    alias_2_len = {
        "a": 8,
        "s": 12,
        "t": 7
    }

    max_alias_len = max(alias[1] for alias in alias_2_len.items())  # maximum number of aliased register (`s` for rv32i)

    def __init__(self):
        # canonized registers (x<num>) to its saved value
        self.vals: dict[int, Int32] = defaultdict(UInt32)

        self.last_set = None
        self.last_read = None

        self.size = len(self.valid_regs) # total number of GPRs

    def is_reg_name_valid(self, reg: str) -> bool:
        return reg in self.valid_regs.keys()

    def is_reg_type_valid(self, t: str) -> bool:
        return t in self.alias_2_len.keys()

    def dump_all(self):
        """
        Dump all registers to stdout
        """
        named_regs = [self._reg_repr(reg) for reg in RF.named_registers()]

        lines: list[list[str]] = [[] for _ in range(self.max_alias_len)]

        for name, s in self.alias_2_len.items():
            for i in range(self.max_alias_len):
                if i >= s:
                    lines[i].append(" " * 15)
                else:
                    reg = "{}{}".format(name, i)
                    lines[i].append(self._reg_repr(reg))

        # print title line
        INFO(
            "Registers[{},{}]:".format(
                FMT_ORANGE + FMT_UNDERLINE + "read" + FMT_NONE,
                FMT_RED + FMT_BOLD + "written" + FMT_NONE,
            )
        )

        # print named registers
        if ONE_LINE:
            INFO("\t" + " ".join(named_regs))
            INFO("\t" + COL_SEP * 6)
        else:
            INFO("\t" + " ".join(named_regs[0:3]))
            INFO("\t" + " ".join(named_regs[3:]))
            INFO("\t" + COL_SEP * 3)

        # print a, s, t registers
        for line in lines:
            INFO("\t" + " ".join(line))

    def dump_by_type(self, t: str):
        """
        Dump the a-type registers
        """
        if not self.is_reg_type_valid(t):
            ERROR(f'Invalid type: {t}')
            return

        INFO(
            f"Dumping {t}-type registers:\n"
            + ";\n".join(self._reg_repr("{}{}".format(t, i)) for i in range(self.alias_2_len[t]))
        )

    def dump_by_range(self, t: str, l: int, r: int):
        if not self.is_reg_type_valid(t):
            ERROR(f'Invalid type: {t}')
            return

        INFO(
            f"Dumping {t}-type registers in given range ({l} to {r}):\n"
            + ";\n".join(self._reg_repr("{}{}".format(t, i)) for i in range(l, r))
        )

    def dump_by_name(self, reg: str):
        if not self.is_reg_name_valid(reg):
            ERROR(f'Invalid register: {reg}')
            return

        INFO(
            f'Dumping register: {self._reg_repr(reg)}'
        )

    def _reg_repr(self, reg: str, name_len=4, fmt="08X"):
        txt = "{:{}}=0x{:{}}".format(reg, name_len, self.get_by_name(reg, False), fmt)
        if reg == self.last_set:
            return FMT_RED + FMT_BOLD + txt + FMT_NONE
        if reg == self.last_read:
            return FMT_ORANGE + FMT_UNDERLINE + txt + FMT_NONE
        if reg == "zero":
            return txt

        return FMT_INFO + txt

    def set_by_name(self, reg: str, val: Int32, mark_set: bool = True) -> bool:
        if not self.is_reg_name_valid(reg):
            raise InvalidRegisterException(reg)

        reg_id = self.valid_regs[reg]

        return self.set(reg_id, val, mark_set)

    def set(self, reg: int, val: Int32, mark_set: bool = True) -> bool:
        """
        Set a register content to val
        :param reg: The register to set (by index)
        :param val: The new value
        :param mark_set: If True, marks this register as "last accessed" (only used internally)
        :return: If the operation was successful
        """
        if reg == 0:
            return False

        if mark_set:
            self.last_set = get_alias_name_by_id(reg)

        self.vals[reg] = val.signed()
        return True

    def get_by_name(self, reg: str, mark_read: bool = True) -> Int32:
        if not self.is_reg_name_valid(reg):
            raise InvalidRegisterException(reg)

        reg_id = self.valid_regs[reg]
        return self.get(reg_id, mark_read)

    def get(self, reg: int, mark_read: bool = True) -> Int32:
        """
        Returns the contents of register reg
        :param reg: The register name
        :param mark_read: If the register should be marked as "last read" (only used internally)
        :return: The contents of register reg
        """
        if mark_read:
            self.last_read = get_alias_name_by_id(reg)

        return self.vals[reg]

    @staticmethod
    def named_registers():
        """
        Return all named registers
        :return: The list
        """
        return ["zero", "ra", "sp", "gp", "tp", "fp"]

    # def __repr__(self):
    #     # return "<Registers[xlen=32]{}>".format(
    #     #     "{"
    #     #     + ", ".join(self._reg_repr("a{}".format(i), 2, "0x") for i in range(8))
    #     #     + "}",
    #     # )
    #     # todo>
    #     return 'todo'

# if __name__ == '__main__':
#     regs = RF()
#     regs.dump()