# FileCheck compatible validation tests
#  llvm-mc %s -triple=riscv32 -riscv-no-aliases -show-encoding \
# | FileCheck -check-prefixes=CHECK-ASM %s


# CHECK-ASM: encoding: [0xb3,0x17,0xd7,0x00]
sll	a5, a4, a3
# CHECK-ASM: encoding: [0x13,0x25,0xc6,0xfe]
slti	a0, a2, -20
# CHECK-ASM: encoding: [0x13,0xb9,0x09,0x05]
sltiu	s2, s3, 80
# CHECK-ASM: encoding: [0x13,0x42,0xd3,0xf9]
xori	tp, t1, -99
# CHECK-ASM: encoding: [0x13,0xe5,0x05,0x80]
ori	a0, a1, -2048
# CHECK-ASM: encoding: [0x93,0x70,0xf1,0x7f]
andi	ra, sp, 2047
# CHECK-ASM: encoding: [0x93,0x70,0xf1,0x7f]
andi	ra, sp, 2047
