import os


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
