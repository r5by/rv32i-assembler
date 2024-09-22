.text
.org 0x0

addi s0, x0, 10
addi s1, x0, 10
# addi x0, x0, 0
# addi x0, x0, 0

# beq s1, s0, loop

loop:
	addi s1, s0, -32
