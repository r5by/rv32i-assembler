import os
import glob
import json
import inspect
from comm.exceptions import ParseException


def get_path(dir: str) -> str:
    """
    Takes a directory name as a string and returns its full path.
    If the directory does not exist, it creates it.

    Args:
        dir (str): The directory name.

    Returns:
        str: The full path of the directory.
    """
    # Get the absolute path of the directory
    full_path = os.path.abspath(dir)

    # Check if the path exists
    if not os.path.exists(full_path):
        # Create the directory (including any necessary parent directories)
        os.makedirs(full_path)

    return full_path

def list_asm_files_full_paths(directory):
    """
    Returns a list of full paths for files in the given directory that match the pattern '*.s'.
    """
    paths = [os.path.join(directory, fn)
            for fn in os.listdir(directory)
            if fn.endswith('.s') and os.path.isfile(os.path.join(directory, fn))]
    paths.sort()  # todo> should design test cases without order!
    return paths

def get_filelist_with_pattern(pat: str, src_dir):
    '''
        Get a list of file (full path) in {src_dir} satisfying the regular expression {pat}
    '''
    # Construct the search pattern
    pattern = os.path.join(src_dir, pat)

    # Find all files matching the pattern
    file_list = glob.glob(pattern)

    # Return the list of full file paths
    return file_list

def write_to_file(output : list, file : str) -> None:
    extension = file[-4:]

    if extension == '.bin':
        with open(file, 'wb') as f:
            for instr in output:
                byte_array = [instr[i:i+8] for i in range(0,len(instr),8)]
                byte_list = [int(b,2) for b in byte_array]
                f.write(bytearray(byte_list))

    elif extension == '.hex':
        with open(file, 'wb') as f:
            for instr in output:
                hex_string = instr[2:] if instr.startswith('0x') else instr
                byte_data = bytes.fromhex(hex_string)
                f.write(byte_data)

    elif extension == '.lst':
        raise NotImplementedError()

    else:
        raise NotImplementedError()

def load_json_config(conf: str):
    # Get the caller's frame
    caller_frame = inspect.stack()[1]
    caller_filename = caller_frame.filename

    # Get the directory of the caller's file
    caller_directory = os.path.dirname(os.path.abspath(caller_filename))

    # Combine the caller's directory with the provided conf path
    full_path = os.path.join(caller_directory, conf)
    full_path = os.path.expanduser(os.path.expandvars(full_path))
    full_path = os.path.abspath(full_path)

    # Open and read the JSON file
    with open(full_path, 'r') as file:
        json_data = json.load(file)

    return json_data

def parse_numeric_argument(arg: str) -> int:
    """
    parse hex or int strings
    """
    try:
        if arg.lower().startswith("0x"):
            return int(arg, 16)
        return int(arg)
    except ValueError as ex:
        raise ParseException(
            'Invalid immediate argument "{}", maybe missing symbol?'.format(arg), ex
        )

def align_addr(addr: int, to_bytes: int = 8) -> int:
    """
    align an address to `to_bytes` (meaning addr & to_bytes = 0)

    This will increase the address
    """
    return addr + (-addr % to_bytes)


def format_imm(imm, n):
    """
     Format negative/positive immediate value to the n-bit 2's-compliment format
    """
    # Mask the immediate value to n-bits
    mask = (1 << n) - 1
    imm_n = imm & mask  # Keep only the lower n bits

    # Check if the sign bit of an n-bit number is set (two's complement check)
    if imm_n >= (1 << (n - 1)):
        imm_n -= (1 << n)  # Adjust for two's complement if the number is negative

    return imm_n


import json

class JSONBuilder:
    def __init__(self):
        self.entries = []
        self.current_entry = None

    def add_entry(self):
        """Start a new entry and save the current one if it exists."""
        if self.current_entry is not None:
            self.entries.append(self.current_entry)
        self.current_entry = {"src": "", "set": {}, "check": {}}

    def add_src(self, src):
        """Add or update the 'src' field of the current entry."""
        if self.current_entry is None:
            self.add_entry()
        self.current_entry["src"] = src

    def add_set(self, key, value):
        """Add a key-value pair to the 'set' dictionary of the current entry."""
        if self.current_entry is None:
            self.add_entry()
        self.current_entry["set"][key] = value

    def add_check(self, key, value):
        """Add a key-value pair to the 'check' dictionary of the current entry."""
        if self.current_entry is None:
            self.add_entry()
        self.current_entry["check"][key] = value

    def to_json(self):
        """Return the JSON representation of the entries."""
        # Add the last entry if it hasn't been added yet
        if self.current_entry is not None:
            self.entries.append(self.current_entry)
            self.current_entry = None
        return json.dumps(self.entries, indent=4)

    def write_json(self, filename):
        """Write the JSON data to a file."""
        with open(filename, 'w') as f:
            f.write(self.to_json())


if __name__ == '__main__':
    # Create an instance of JSONBuilder
    builder = JSONBuilder()

    # First entry
    builder.add_entry()
    builder.add_src("../examples/math.asm")
    builder.add_set("a0", "0x11")
    builder.add_set("a1", "0x101")
    builder.add_set("sp", 100)
    builder.add_check("a0", "0")
    builder.add_check("a7", 93)
    builder.add_check("a1", -10)

    # Second entry
    builder.add_entry()
    builder.add_src("../examples/fibs.asm")
    # 'set' is empty for this entry
    builder.add_check("t2", 610)

    # Output the JSON data
    # print(builder.to_json())

    # Optionally, write the JSON data to a file
    builder.write_json('output.json')