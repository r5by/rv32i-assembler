import os
import glob
import json
import inspect


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
