# FileCheck compatible validation tests
#  llvm-mc %s -triple=riscv32 -riscv-no-aliases -show-encoding \
# | FileCheck -check-prefixes=CHECK-ASM %s


# CHECK-ASM: encoding: [0xb3,0x17,0xd7,0x00]
sll a5, a4, a3