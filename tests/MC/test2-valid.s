# FileCheck compatible validation tests
#  llvm-mc %s -triple=riscv32 -riscv-no-aliases -show-encoding \
# | FileCheck -check-prefixes=CHECK-ASM %s


# CHECK-ASM: encoding: [0x13,0x04,0xa0,0x00]
addi	s0, zero, 10
# CHECK-ASM: encoding: [0x93,0x04,0xa0,0x00]
addi	s1, zero, 10
# CHECK-ASM: encoding: [0x93,0x04,0x04,0xfe]
addi	s1, s0, -32
