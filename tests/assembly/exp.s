    .section .text
    .globl main, add

    # Macro definition
    .macro LOAD_IMM reg, imm
        addi \reg, x0, \imm
    .endm

    # Function: add
add:
    # Prologue
    addi sp, sp, -16      # Adjust stack pointer to allocate space
    sw ra, 12(sp)         # Save return address
    sw s0, 8(sp)          # Save s0 (callee-saved register)
    sw s1, 4(sp)          # Save s1
    sw s2, 0(sp)          # Save s2

    # Function body
    addi s0, a0, 0        # Move first argument (a0) to s0
    addi s1, a1, 0        # Move second argument (a1) to s1
    add s2, s0, s1        # s2 = s0 + s1
    addi a0, s2, 0        # Move result to a0 (return value)

    # Epilogue
    lw s2, 0(sp)          # Restore s2
    lw s1, 4(sp)          # Restore s1
    lw s0, 8(sp)          # Restore s0
    lw ra, 12(sp)         # Restore return address
    addi sp, sp, 16       # Deallocate stack space
    jalr x0, ra, 0        # Return to caller

    # Function: main
main:
    # Prologue
    addi sp, sp, -8       # Adjust stack pointer to allocate space
    sw ra, 4(sp)          # Save return address
    sw s0, 0(sp)          # Save s0

    # Function body
    LOAD_IMM a0, 10       # Load immediate value 10 into a0 using macro
    LOAD_IMM a1, 20       # Load immediate value 20 into a1 using macro
    jal ra, add           # Call function 'add'
    # Result from 'add' is now in a0 (a0 = 10 + 20)

    # Epilogue
    lw s0, 0(sp)          # Restore s0
    lw ra, 4(sp)          # Restore return address
    addi sp, sp, 8        # Deallocate stack space
    jalr x0, ra, 0        # Return to caller (end of program)
