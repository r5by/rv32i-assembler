# FileCheck compatible validation tests
#  llvm-mc %s -triple=riscv32 -riscv-no-aliases -show-encoding \
# | FileCheck -check-prefixes=CHECK-ASM %s


# CHECK-ASM: encoding: [0xb3,0x00,0x00,0x00]
add x1, x0, x0
# CHECK-ASM: encoding: [0xb3,0x82,0x63,0x40]
sub t0, t2, t1