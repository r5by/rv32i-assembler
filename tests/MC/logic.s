sll a5, a4, a3
slti a0, a2, -20
sltiu s2, s3, 0x50
xori tp, t1, -99
ori a0, a1, -2048
# ori a0, a1, ~2047
# ori a0, a1, !1
# ori a0, a1, %lo(2048)
andi ra, sp, 2047
andi x1, x2, 2047