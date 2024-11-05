        .text
        .globl main

# Main entry point
main:
        addi a0, zero, 15     # Load immediate 15 into register a0
        addi a1, zero, 27     # Load immediate 27 into register a1
        jal ra, add           # Call the add subroutine to calculate a0 + a1
        addi a1, zero, -10    # Load immediate -10 into register a1
        jal ra, sub           # Call the sub subroutine to calculate result - 10

        # exit gracefully
        addi    a0, zero, 0
        addi    a7, zero, 93
        ; scall                   # exit with code 0

# Subroutine to add two numbers
# Input: a0 and a1 (the two numbers to add)
# Output: a0 (result of addition)
add:
        add a0, a0, a1        # a0 = a0 + a1
        jalr zero, ra, 0      # Return to the calling function using jalr

# Subroutine to subtract two numbers
# Input: a0 and a1 (the two numbers to subtract)
# Output: a0 (result of subtraction)
sub:
        sub a0, a0, a1        # a0 = a0 - a1
        jalr zero, ra, 0      # Return to the calling function using jalr
