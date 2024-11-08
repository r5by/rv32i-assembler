        .data
fibs:   .space 56

        .text
.globl  main
main:
        addi    s1, zero, 0     ; storage index
        addi    s2, zero, 56    ; last storage index: n, t2 <== fibs(n//4 + 1), for fibs = lambda n: reduce(lambda x, _: (x[1], x[0] + x[1]), range(n), (0, 1))[0]
        ;ebreak
        addi    t0, zero, 0     ; t0 = F_{i}
        addi    t1, zero, 1     ; t1 = F_{i+1}
loop:
        ; sw      t0, fibs(s1)    ; save  todo> add `sw` into emulator...
        add     t2, t1, t0      ; t2 = F_{i+2}
        addi    t0, t1, 0       ; t0 = t1
        addi    t1, t2, 0       ; t1 = t2
        ;ebreak
        addi    s1, s1, 4       ; increment storage pointer
        blt     s1, s2, loop    ; loop as long as we did not reach array length
        ;ebreak                  ; launch debugger
        addi    a0, zero, 0
        addi    a7, zero, 93
        ;ebreak
        ecall                   ; exit with code 0
