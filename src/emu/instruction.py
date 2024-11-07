import re
from typing import Union, Tuple, Optional
from functools import lru_cache

from abc import ABC, abstractmethod
from typing import Union
from comm.int32 import Int32, UInt32
from comm.exceptions import NumberFormatException
from asm.reg_info import alias_abi

class Immediate:
    """
    This class solves a problem of ambiguity when interpreting assembly code.

    Let's look at the following four cases (assuming 1b is 16 bytes back):
     a) beq     a0, a1, 1b      // conditional jump 16 bytes back
     b) beq     a0, a1, -16     // conditional jump 16 bytes back
     c) addi    a0, a1, 1b      // subtract (pc - 16) from a1
     d) addi    a0, a1, -16     // subtract 16 from a1

    We want a and b to behave the same, but c and d not to.

    The Immediate class solves this problem, by giving each instruction two ways of
    interpreting a given immediate. It can either get the "absolute value" of the
    immediate, or it's relative value to the PC.

    In this case, the beq instruction would interpret both as PC relative values,
    while addi would treat them as absolute values.
    """

    abs_value: Int32
    pcrel_value: Int32

    __slots__ = ["abs_value", "pcrel_value"]

    def __init__(self, abs_value: Union[int, Int32], pcrel_value: Union[int, Int32]):
        self.abs_value = Int32(abs_value)
        self.pcrel_value = Int32(pcrel_value)


class Instruction(ABC):
    name: str
    regs: tuple
    imm: int

    @abstractmethod
    def get_imm(self) -> Immediate:
        """
        parse and get immediate argument
        """
        pass

    @abstractmethod
    def get_reg(self, num: int) -> int:
        """
        parse and get an register GPR index
        """
        pass

    def __repr__(self):
        # no operands
        if not self.regs and not self.imm:
            return f"{self.name}"

        # Creating canonized register representations with 'x' prefix
        x_args = [f'x{num}' for num in self.regs]

        # Joining all register representations with commas
        regs_repr = ", ".join(x_args) if x_args else ""

        # Adding immediate value if it exists
        if self.imm is not None:
            imm_repr = f", {self.imm}"
        else:
            imm_repr = ""

        # Formatting the whole representation
        return f"{self.name} {regs_repr}{imm_repr}".strip()


class InstructionWithEncoding(ABC):
    """
    Mixin for instructions that have encodings
    """

    @property
    @abstractmethod
    def encoding(self) -> int:
        raise NotImplementedError()


from comm.utils import parse_numeric_argument

_NUM_LABEL_RE = re.compile(r"[0-9][fb]")
_INT_IMM_RE = re.compile(r"[+-]?([0-9]+|0x[A-Fa-f0-9]+)")


class TranslatableInstruction(Instruction):
    def __init__(
        self,
        name: str,
        addr: UInt32,
        regs: Optional[Union[Tuple[()], Tuple[int], Tuple[int, int], Tuple[int, int, int]]] = None,
        imm: Optional[int] = None,
    ):
        self.name = name
        self._addr = addr

        self.regs = regs
        self.imm = imm

    @property
    def addr(self) -> UInt32:
        return self._addr

    @lru_cache(maxsize=None)
    def get_imm(self) -> Immediate:
        if not self.imm:
            raise NumberFormatException(f"Current instruction: {self} doesn't have immediate operand.")

        val = self.imm
        return Immediate(abs_value=val, pcrel_value=val - self.addr)

    def get_reg(self, num: int) -> int:
        return self.regs[num]

    def get_reg_alias(self, num: int) -> str:
        reg = self.regs[num]
        return alias_abi[reg]