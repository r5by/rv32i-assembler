    .section .text
    .globl main, add

    # Macro definition
    .macro LOAD_IMM reg, value
        li \reg, \value  # load register
        addi \reg, \reg, \value
    .endm

    # Function: add
add:
    # Prologue
    addi sp, sp, -16      # Allocate stack space
    sw ra, 12(sp)         # Save return address
    sw s0, 8(sp)          # Save s0
    sw s1, 4(sp)          # Save s1
    sw s2, 0(sp)          # Save s2

    # Function body
    # mv s0, a0             # Move first argument to s0
    # mv s1, a1             # Move second argument to s1
    add s2, s0, s1        # s2 = s0 + s1
    # mv a0, s2             # Move result to a0 (return value)

    # Epilogue
    lw s2, 0(sp)          # Restore s2
    lw s1, 4(sp)          # Restore s1
    lw s0, 8(sp)          # Restore s0
    lw ra, 12(sp)         # Restore return address
    addi sp, sp, 16       # Deallocate stack space
    # jr ra                 # Return to caller

    # Function: main
main:
    # Prologue
    addi sp, sp, -8       # Allocate stack space
    sw ra, 4(sp)          # Save return address
    sw s0, 0(sp)          # Save s0

    # Function body
    LOAD_IMM a0, 10       # Load immediate value 10 into a0 using macro
    LOAD_IMM a1, 20       # Load immediate value 20 into a1 using macro
    # jal ra, add           # Call function 'add'
    # Result from 'add' is now in a0

    # Epilogue
    lw s0, 0(sp)          # Restore s0
    lw ra, 4(sp)          # Restore return address
    addi sp, sp, 8        # Deallocate stack space
    # jr ra                 # Return to caller
