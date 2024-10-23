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
    def __init__(self, msg: str):
        super().__init__(msg)
        self.msg = msg

    def message(self):
        return (
            FMT_PARSE
            + '{}("{}")'.format(self.__class__.__name__, self.msg)
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