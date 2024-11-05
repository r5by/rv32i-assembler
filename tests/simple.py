from comm.utils import get_path
from asm.asm_backend import AsmBackend

if __name__ == '__main__':
    # cnv = MCEmitter(hex_mode=True, output_mode='f')  # Initialize converter
    # encodings = cnv.translate(get_path('./MC/test2.s'), get_path('./warn.bin'))  # Get encodings

    cnv = AsmBackend(hex_mode=True)  # Initialize converter
    encodings = cnv.translate(get_path('MC/test2.s'))  # Get encodings

    print(encodings)
