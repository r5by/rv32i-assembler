from email.mime.multipart import MIMEMultipart

from asm import RV32Backend
from asm.instr_info import rv32i
from comm.logging import DEBUG_INFO
from .cpu import CPU, MMU, RV32I
from typing import Optional, Type, List

class RV32IEmulator:

    def __init__(self, asm_backend: "RV32Backend"):
        self.asm_backend: RV32Backend = asm_backend
        self.cpu: Optional[CPU] = None

    def load_programs(self):
        asms = self.asm_backend.analyze_lines()
        self.cpu.mmu.load_program(asms=asms)

    def instantiate_cpu(self):
        mmu = MMU(base_addr=self.asm_backend.base_addr, symbol_table=self.asm_backend.symbol_table)
        self.cpu = CPU(mmu=mmu, isa=RV32I)

    def launch(self):
        self.cpu.launch()