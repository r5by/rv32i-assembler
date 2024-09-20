from riscv_assembler.utils import get_path
from riscv_assembler.code_emitter import MCEmitter

if __name__ == '__main__':
    # cnv = MCEmitter(hex_mode=True, output_mode='f')  # Initialize converter
    # encodings = cnv.translate(get_path('./MC/test2.s'), get_path('./warn.bin'))  # Get encodings

    cnv = MCEmitter(hex_mode=True)  # Initialize converter
    encodings = cnv.translate(get_path('MC/test2.s'))  # Get encodings

    print(encodings)
