import typing
from abc import ABC, abstractmethod
from typing import List, Type, Dict, Callable, Optional, Union, Set, Iterable, Tuple
from comm.logging import DEBUG_INFO, INFO
from comm.colors import FMT_CPU, FMT_NONE, FMT_DEBUG
from comm.int32 import Int32, UInt32
from comm.exceptions import ASSERT_LEN, LaunchDebuggerException, RV32IBaseException

if typing.TYPE_CHECKING:
    from .debug import launch_debug_session

from . import (
    Instruction,
    Immediate,
    MMU,
    Registers,
    CSR,
    PrivModes
)


class ISA(ABC):
    """
    Represents a collection of instructions

    Each instruction set has to inherit from this class. Each instruction should be it's own method:

    instruction_<name>(self, ins: LoadedInstruction)

    instructions containing a dot '.' should replace it with an underscore.
    """

    def __init__(self, cpu: "CPU"):
        """Create a new instance of the Instruction set. This requires access to a CPU, and grabs vertain things
        from it such as access to the MMU and registers.
        """
        self.name = self.__class__.__name__
        self.cpu = cpu

    def load(self) -> Dict[str, Callable[["Instruction"], None]]:
        """
        This is called by the CPU once it instantiates this instruction set

        It returns a dictionary of all instructions in this instruction set,
        pointing to the correct handler for it
        """
        return {name: ins for name, ins in self.get_instructions()}

    def get_instructions(self) -> Iterable[Tuple[str, Callable[[Instruction], None]]]:
        """
        Returns a list of all valid instruction names included in this instruction set

        converts underscores in names to dots
        """
        for member in dir(self):
            if member.startswith("instruction_"):
                yield member[12:].replace("_", "."), getattr(self, member)

    def parse_mem_ins(self, ins: "Instruction") -> Tuple[str, UInt32]:
        """
        parses rd, imm(rs) argument format and returns (rd, imm+rs1)
        (so a register and address tuple for memory instructions)
        """
        assert len(ins.args) == 3
        # handle rd, rs1, imm
        rd = ins.get_reg(0)
        rs = self.regs.get(ins.get_reg(1)).unsigned()
        imm = ins.get_imm(2)
        return rd, rs + imm.abs_value.unsigned()

    def parse_rd_rs_rs(
            self, ins: "Instruction", signed=True
    ) -> Tuple[str, Int32, Int32]:
        """
        Assumes the command is in <name> rd, rs1, rs2 format
        Returns the name of rd, and the values in rs1 and rs2
        """
        ASSERT_LEN(ins.args, 3)
        if signed:
            return (
                ins.get_reg(0),
                Int32(self.regs.get(ins.get_reg(1))),
                Int32(self.regs.get(ins.get_reg(2))),
            )
        else:
            return (
                ins.get_reg(0),
                UInt32(self.regs.get(ins.get_reg(1))),
                UInt32(self.regs.get(ins.get_reg(2))),
            )

    def parse_rd_rs_imm(self, ins: "Instruction") -> Tuple[str, Int32, Immediate]:
        """
        Assumes the command is in <name> rd, rs, imm format
        Returns the name of rd, the value in rs and the immediate imm
        """
        return (
            ins.get_reg(0),
            Int32(self.regs.get(ins.get_reg(1))),
            ins.get_imm(2),
        )

    def parse_rs_rs_imm(self, ins: "Instruction") -> Tuple[Int32, Int32, Immediate]:
        """
        Assumes the command is in <name> rs1, rs2, imm format
        Returns the values in rs1, rs2 and the immediate imm
        """
        return (
            Int32(self.regs.get(ins.get_reg(0))),
            Int32(self.regs.get(ins.get_reg(1))),
            ins.get_imm(2),
        )

    def get_reg_content(self, ins: "Instruction", ind: int) -> Int32:
        """
        get the register name from ins and then return the register contents
        """
        return self.regs.get(ins.get_reg(ind))

    @property
    def mmu(self):
        return self.cpu.mmu

    @property
    def regs(self) -> Registers:
        return self.cpu.regs

    def __repr__(self):
        return "InstructionSet[{}] with {} instructions".format(
            self.__class__.__name__, len(list(self.get_instructions()))
        )

class RV32I(ISA):
    """
    The RV32I instruction set. Some instructions are missing, such as
    fence, fence.i, rdcycle, rdcycleh, rdtime, rdtimeh, rdinstret, rdinstreth
    All atomic read/writes are also not implemented yet

    See https://maxvytech.com/images/RV32I-11-2018.pdf for a more detailed overview
    """

    def instruction_lb(self, ins: "Instruction"):
        rd, addr = self.parse_mem_ins(ins)
        self.regs.set(rd, UInt32.sign_extend(self.mmu.read(addr.unsigned_value, 1), 8))

    def instruction_lh(self, ins: "Instruction"):
        rd, addr = self.parse_mem_ins(ins)
        self.regs.set(rd, UInt32.sign_extend(self.mmu.read(addr.unsigned_value, 2), 16))

    def instruction_lw(self, ins: "Instruction"):
        rd, addr = self.parse_mem_ins(ins)
        self.regs.set(rd, UInt32(self.mmu.read(addr.unsigned_value, 4)))

    def instruction_lbu(self, ins: "Instruction"):
        rd, addr = self.parse_mem_ins(ins)
        self.regs.set(rd, UInt32(self.mmu.read(addr.unsigned_value, 1)))

    def instruction_lhu(self, ins: "Instruction"):
        rd, addr = self.parse_mem_ins(ins)
        self.regs.set(rd, UInt32(self.mmu.read(addr.unsigned_value, 2)))

    def instruction_sb(self, ins: "Instruction"):
        rd, addr = self.parse_mem_ins(ins)
        self.mmu.write(addr.unsigned_value, 1, self.regs.get(rd).to_bytes(1))

    def instruction_sh(self, ins: "Instruction"):
        rd, addr = self.parse_mem_ins(ins)
        self.mmu.write(addr.unsigned_value, 2, self.regs.get(rd).to_bytes(2))

    def instruction_sw(self, ins: "Instruction"):
        rd, addr = self.parse_mem_ins(ins)
        self.mmu.write(addr.unsigned_value, 4, self.regs.get(rd).to_bytes(4))

    def instruction_sll(self, ins: "Instruction"):
        ASSERT_LEN(ins.args, 3)
        dst = ins.get_reg(0)
        src1 = ins.get_reg(1)
        src2 = ins.get_reg(2)
        self.regs.set(dst, self.regs.get(src1) << (self.regs.get(src2) & 0b11111))

    def instruction_slli(self, ins: "Instruction"):
        ASSERT_LEN(ins.args, 3)
        dst = ins.get_reg(0)
        src1 = ins.get_reg(1)
        imm = ins.get_imm(2)
        self.regs.set(dst, self.regs.get(src1) << (imm.abs_value & 0b11111))

    def instruction_srl(self, ins: "Instruction"):
        ASSERT_LEN(ins.args, 3)
        dst = ins.get_reg(0)
        src1 = ins.get_reg(1)
        src2 = ins.get_reg(2)
        self.regs.set(
            dst, self.regs.get(src1).shift_right_logical(self.regs.get(src2) & 0b11111)
        )

    def instruction_srli(self, ins: "Instruction"):
        ASSERT_LEN(ins.args, 3)
        dst = ins.get_reg(0)
        src1 = ins.get_reg(1)
        imm = ins.get_imm(2)
        self.regs.set(
            dst, self.regs.get(src1).shift_right_logical(imm.abs_value & 0b11111)
        )

    def instruction_sra(self, ins: "Instruction"):
        ASSERT_LEN(ins.args, 3)
        dst = ins.get_reg(0)
        src1 = ins.get_reg(1)
        src2 = ins.get_reg(2)
        self.regs.set(dst, self.regs.get(src1) >> (self.regs.get(src2) & 0b11111))

    def instruction_srai(self, ins: "Instruction"):
        ASSERT_LEN(ins.args, 3)
        dst = ins.get_reg(0)
        src1 = ins.get_reg(1)
        imm = ins.get_imm(2)
        self.regs.set(dst, self.regs.get(src1) >> (imm.abs_value & 0b11111))

    def instruction_add(self, ins: "Instruction"):
        dst, rs1, rs2 = self.parse_rd_rs_rs(ins)
        self.regs.set(dst, rs1 + rs2)

    def instruction_addi(self, ins: "Instruction"):
        dst, rs1, imm = self.parse_rd_rs_imm(ins)
        self.regs.set(dst, rs1 + imm.abs_value)

    def instruction_sub(self, ins: "Instruction"):
        dst, rs1, rs2 = self.parse_rd_rs_rs(ins)
        self.regs.set(dst, rs1 - rs2)

    def instruction_lui(self, ins: "Instruction"):
        ASSERT_LEN(ins.args, 2)
        reg = ins.get_reg(0)
        self.regs.set(reg, ins.get_imm(1).abs_value << 12)

    def instruction_auipc(self, ins: "Instruction"):
        ASSERT_LEN(ins.args, 2)
        reg = ins.get_reg(0)
        imm = ins.get_imm(1).abs_value << 12
        self.regs.set(reg, imm + self.cpu.pc)

    def instruction_xor(self, ins: "Instruction"):
        rd, rs1, rs2 = self.parse_rd_rs_rs(ins)
        self.regs.set(rd, rs1 ^ rs2)

    def instruction_xori(self, ins: "Instruction"):
        rd, rs1, imm = self.parse_rd_rs_imm(ins)
        self.regs.set(rd, rs1 ^ imm.abs_value)

    def instruction_or(self, ins: "Instruction"):
        rd, rs1, rs2 = self.parse_rd_rs_rs(ins)
        self.regs.set(rd, rs1 | rs2)

    def instruction_ori(self, ins: "Instruction"):
        rd, rs1, imm = self.parse_rd_rs_imm(ins)
        self.regs.set(rd, rs1 | imm.abs_value)

    def instruction_and(self, ins: "Instruction"):
        rd, rs1, rs2 = self.parse_rd_rs_rs(ins)
        self.regs.set(rd, rs1 & rs2)

    def instruction_andi(self, ins: "Instruction"):
        rd, rs1, imm = self.parse_rd_rs_imm(ins)
        self.regs.set(rd, rs1 & imm.abs_value)

    def instruction_slt(self, ins: "Instruction"):
        rd, rs1, rs2 = self.parse_rd_rs_rs(ins)
        self.regs.set(rd, UInt32(rs1 < rs2))

    def instruction_slti(self, ins: "Instruction"):
        rd, rs1, imm = self.parse_rd_rs_imm(ins)
        self.regs.set(rd, UInt32(rs1 < imm))

    def instruction_sltu(self, ins: "Instruction"):
        dst, rs1, rs2 = self.parse_rd_rs_rs(ins)
        self.regs.set(dst, UInt32(rs1.unsigned_value < rs2.unsigned_value))

    def instruction_sltiu(self, ins: "Instruction"):
        dst, rs1, imm = self.parse_rd_rs_imm(ins)
        self.regs.set(dst, UInt32(rs1.unsigned_value < imm.abs_value.unsigned_value))

    def instruction_beq(self, ins: "Instruction"):
        rs1, rs2, dst = self.parse_rs_rs_imm(ins)
        if rs1 == rs2:
            self.cpu.pc += dst.pcrel_value.value - 4

    def instruction_bne(self, ins: "Instruction"):
        rs1, rs2, dst = self.parse_rs_rs_imm(ins)
        if rs1 != rs2:
            self.cpu.pc += dst.pcrel_value.value - 4

    def instruction_blt(self, ins: "Instruction"):
        rs1, rs2, dst = self.parse_rs_rs_imm(ins)
        if rs1 < rs2:
            self.cpu.pc += dst.pcrel_value.value - 4

    def instruction_bge(self, ins: "Instruction"):
        rs1, rs2, dst = self.parse_rs_rs_imm(ins)
        if rs1 >= rs2:
            self.cpu.pc += dst.pcrel_value.value - 4

    def instruction_bltu(self, ins: "Instruction"):
        rs1, rs2, dst = self.parse_rs_rs_imm(ins)
        if rs1.unsigned_value < rs2.unsigned_value:
            self.cpu.pc += dst.pcrel_value.value - 4

    def instruction_bgeu(self, ins: "Instruction"):
        rs1, rs2, dst = self.parse_rs_rs_imm(ins)
        if rs1.unsigned_value >= rs2.unsigned_value:
            self.cpu.pc += dst.pcrel_value.value - 4

    def instruction_j(self, ins: "Instruction"):
        ASSERT_LEN(ins.args, 1)
        addr = ins.get_imm(0)
        self.cpu.pc += addr.pcrel_value.value - 4

    def instruction_jal(self, ins: "Instruction"):
        reg = "ra"  # default register is ra
        if len(ins.args) == 1:
            addr = ins.get_imm(0)
        else:
            ASSERT_LEN(ins.args, 2)
            reg = ins.get_reg(0)
            addr = ins.get_imm(1)
        self.regs.set(reg, UInt32(self.cpu.pc))
        self.cpu.pc += addr.pcrel_value.value - 4

    def instruction_jalr(self, ins: "Instruction"):
        ASSERT_LEN(ins.args, 3)
        reg = ins.get_reg(0)
        base = ins.get_reg(1)
        addr = ins.get_imm(2).abs_value.value
        self.regs.set(reg, Int32(self.cpu.pc))
        self.cpu.pc = self.regs.get(base).unsigned_value + addr

    def instruction_ret(self, ins: "Instruction"):
        ASSERT_LEN(ins.args, 0)
        self.cpu.pc = self.regs.get("ra").unsigned_value

    def instruction_ebreak(self, ins: "Instruction"):
        self.instruction_sbreak(ins)

    def instruction_sbreak(self, ins: "Instruction"):
        ASSERT_LEN(ins.args, 0)
        INFO(
            FMT_DEBUG
            + "Debug instruction encountered at 0x{:08X}".format(self.cpu.pc - 1)
            + FMT_NONE
        )
        raise LaunchDebuggerException()

    def instruction_nop(self, ins: "Instruction"):
        ASSERT_LEN(ins.args, 0)
        pass

    def instruction_li(self, ins: "Instruction"):
        ASSERT_LEN(ins.args, 2)
        reg = ins.get_reg(0)
        immediate = ins.get_imm(1).abs_value
        self.regs.set(reg, Int32(immediate))

    def instruction_la(self, ins: "Instruction"):
        ASSERT_LEN(ins.args, 2)
        reg = ins.get_reg(0)
        immediate = ins.get_imm(1).abs_value
        self.regs.set(reg, Int32(immediate))

    def instruction_mv(self, ins: "Instruction"):
        ASSERT_LEN(ins.args, 2)
        rd, rs = ins.get_reg(0), ins.get_reg(1)
        self.regs.set(rd, self.regs.get(rs))

class CPU(ABC):
    # static cpu configuration
    INS_XLEN: int = 4

    # housekeeping variables
    regs: Registers

    mmu: MMU
    pc: int
    cycle: int
    halted: bool

    # debugging context
    debugger_active: bool

    # instruction information
    instr_handlers: Dict[str, Callable[[Instruction], None]]
    isa: ISA

    # control and status things:
    hart_id: int
    mode: PrivModes
    csr: CSR

    def __init__(self, mmu: MMU, isa: Type["ISA"]):
        self.mmu = mmu
        self.regs = Registers()
        self.instr_handlers = dict()

        #register isa
        self.isa = isa(self)
        self.instr_handlers.update(self.isa.load())

        self.halted = False
        self.cycle = 0
        self.pc = 0
        self.hart_id = 0
        self.debugger_active = False
        self.csr = CSR()

        self.exit_code = 0

    def __repr__(self):
        """
        Returns a representation of the CPU and some of its state.
        """
        return "{}(pc=0x{:08X}, cycle={}, halted={} isa={})".format(
            self.__class__.__name__,
            self.pc,
            self.cycle,
            self.halted,
            self.isa
        )

    def step(self):
        """
                Execute a single instruction, then return.
                """
        launch_debugger = False

        try:
            self.cycle += 1
            ins = self.mmu.read_ins(self.pc)

            ins_str = str(ins)
            DEBUG_INFO(FMT_CPU + "   0x{:08X}:{} {}".format(self.pc, FMT_NONE, ins_str))

            self.pc += self.INS_XLEN
            self.run_instruction(ins)
        except RV32IBaseException as ex:
            if isinstance(ex, LaunchDebuggerException):
                # if the debugger is active, raise the exception to
                if self.debugger_active:
                    raise ex

                print(FMT_CPU + "[CPU] Debugger launch requested!" + FMT_NONE)
                launch_debugger = True
            else:
                print(ex.message())
                ex.print_stacktrace()
                print(FMT_CPU + "[CPU] Halting due to exception!" + FMT_NONE)
                self.halted = True

        if launch_debugger:
            launch_debug_session(self)

    def run(self):
        while not self.halted:
            self.step()

        DEBUG_INFO(
            FMT_CPU
            + "[CPU] Program exited with code {}".format(self.exit_code)
            + FMT_NONE
        )

    # todo> csr
    def setup_csr(self):
        ...

    def run_instruction(self, ins: Instruction):
        """
        Execute a single instruction

        :param ins: The instruction to execute
        """
        try:
            self.instr_handlers[ins.name](ins)
        except KeyError as ex:
            raise RuntimeError("Unknown instruction: {}".format(ins)) from ex

    def initialize_registers(self):
        # set a0 to the hartid
        self.regs.set_by_name("a0", UInt32(self.hart_id))

    #todo>
    def launch(self):
        entrypoint = self.mmu.find_entrypoint()

        self.initialize_registers()
        self.setup_csr()

        DEBUG_INFO(
            FMT_CPU
            + "[CPU] Started running from {}".format(
                entrypoint
            )
            + FMT_NONE
        )

        self.pc = entrypoint
        self.run()
