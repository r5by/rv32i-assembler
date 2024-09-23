[![celebi-pkg](https://circleci.com/gh/celebi-pkg/riscv-assembler.svg?style=svg)](https://circleci.com/gh/celebi-pkg/riscv-assembler)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

![example](references/mdimg.png)
# riscv-assembler Documentation
RISC-V Assembly code assembler package. [View the full documentation here]([https://www.riscvassembler.org](https://celebi-pkg.github.io/riscv-assembler/))

This package contains tools and functions that can convert **RISC-V Assembly code to machine code**. The whole process is implemented using Python purely for understandability, less so for efficiency in computation. These tools can be used to **convert given lines of code or [whole files](#convert) to machine code**. For conversion, output file types are binary, text files, and printing to console. The supported instruction types are **R, I, S, SB, U, and UJ**. Almost all standard instructions are supported, most pseudo instructions are also supported.

Feel free to open an issue or contact me at [kayacelebi17@gmail.com](mailto:kayacelebi17@gmail.com?subject=[GitHub]%20riscv-assembler) with any questions/inquiries.

# Installation
The package can be installed using pip:

    $ pip install riscv-assembler

If issues arise try:

    $ python3 -m pip install riscv-assembler

# RV32I modification

Supported instructions can be found in `riscv_assembler/data/rv32i.json`. During my implementation, I found the following resource links to be very useful.

## References
1. [riscv-cheet-sheet](https://projectf.io/posts/riscv-cheat-sheet/)
2. [riscv-spec-v2.2](https://riscv.org/wp-content/uploads/2017/05/riscv-spec-v2.2.pdf)
3. [RV32I Base Integer Instruction Set](https://five-embeddev.com/riscv-user-isa-manual/Priv-v1.12/rv32.html)
4. [riscv-calling-conv](https://riscv.org/wp-content/uploads/2015/01/riscv-calling.pdf)
5. [riscv-card](https://www.cs.sfu.ca/~ashriram/Courses/CS295/assets/notebooks/RISCV/RISCV_CARD.pdf)
