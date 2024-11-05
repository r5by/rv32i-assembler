from abc import abstractmethod
from comm.colors import *
import typing

if typing.TYPE_CHECKING:
    from asm.instr_info import InstrInfo


class RV32IBaseException(BaseException):
    @abstractmethod
    def message(self) -> str:
        raise NotImplemented

    def print_stacktrace(self):
        import traceback
        traceback.print_exception(type(self), self, self.__traceback__)

class ParseException(RV32IBaseException):
    def __init__(self, msg: str, data=None):
        super().__init__(msg)
        self.msg = msg
        self.data = data

    def message(self):
        return (
            FMT_PARSE
            + '{}("{}, {}")'.format(self.__class__.__name__, self.msg, self.data)
            + FMT_NONE
        )

class UnknownAssemblyException(RV32IBaseException):
    def __init__(self, asm: str):
        self.asm = asm

    def message(self):
        return (
            FMT_WARNING
            + "{}({})".format(
                self.__class__.__name__,
                self.asm,
            )
            + FMT_NONE
        )

class UnimplementedException(RV32IBaseException):
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

    def message(self):
        return "{}({})".format(self.__class__.__name__, self.msg)

class InvalidRegisterException(RV32IBaseException):
    def __init__(self, reg):
        self.reg = reg

    def message(self):
        return (
            FMT_CPU
            + "{}(Invalid register: {})".format(self.__class__.__name__, self.reg)
            + FMT_NONE
        )

class NumberFormatException(RV32IBaseException):
    def __init__(self, msg):
        super().__init__(msg)
        self.msg = msg

    def message(self):
        return "{}({})".format(self.__class__.__name__, self.msg)

def INS_NOT_IMPLEMENTED(ins):
    raise UnimplementedException(ins)

def ASSERT_LEN(a1, size):
    if len(a1) != size:
        raise ParseException(
            "ASSERTION_FAILED: Expected {} to be of length {}".format(a1, size),
            (a1, size),
        )

# this exception is not printed and simply signals that an interactive debugging session is
class LaunchDebuggerException(RV32IBaseException):
    def message(self) -> str:
        return ""