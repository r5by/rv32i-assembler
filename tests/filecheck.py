import os
import re
import subprocess
from asm.utils import get_filelist_with_pattern

CONF_FILE = 'test.cfg'

def parse_conf_by_key(conf: str, key: str):
    with open(conf, 'r') as f:
        res = None
        for line in f:
            line = line.strip()
            if line.startswith(key):
                key, value = line.split('=', 1)
                res = value.strip().strip('"').strip("'")
                break

        if not res:
            raise Exception(f"Error: Required component entry: {key} is not found in {conf}")

        return res

def get_conf(key: str, conf=CONF_FILE):
    dir = parse_conf_by_key(conf, key)
    dir = os.path.expanduser(dir)
    dir = os.path.abspath(dir)

    # Check if the directory exists
    if not os.path.isdir(dir):
        raise Exception(f"Error: Directory {dir} does not exist")

    return dir

def run_filecheck(filecheck_src):
    # Define the paths to the executables
    cmdline_path = os.path.join(tool_dir, 'cmd.py')
    file_check_path = os.path.join(llvm_bin, 'FileCheck')

    # Ensure that the executables exist
    if not os.path.isfile(cmdline_path):
        raise Exception(f"Error: llvm-mc not found at {cmdline_path}")

    if not os.path.isfile(file_check_path):
        raise Exception(f"Error: FileCheck not found at {file_check_path}")

    # Construct the command arguments
    rv32i_cmd = ["python3", cmdline_path, "-s", filecheck_src, "-show-encoding"]
    file_check_cmd = [file_check_path, "-check-prefixes=CHECK-ASM", filecheck_src]

    try:
        # Start the llvm-mc process
        rv32_process = subprocess.Popen(
            rv32i_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Start the FileCheck process, reading from llvm-mc's stdout
        file_check_process = subprocess.Popen(
            file_check_cmd,
            stdin=rv32_process.stdout,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Close llvm_mc_process's stdout in the parent to allow llvm_mc_process to receive a SIGPIPE if file_check_process exits
        rv32_process.stdout.close()

        # Communicate with file_check_process to get its output and errors
        file_check_stdout, file_check_stderr = file_check_process.communicate()

        # Wait for llvm_mc_process to finish and get stderr
        llvm_mc_stderr = rv32_process.stderr.read()
        rv32_process.stderr.close()
        rv32_process.wait()

        # Check for errors in llvm-mc process
        if rv32_process.returncode != 0:
            print(f"Error: llvm-mc exited with return code {rv32_process.returncode}")
            print("llvm-mc stderr:")
            print(llvm_mc_stderr.decode())
            return

        # Check for errors in FileCheck process
        if file_check_process.returncode != 0:
            print(f"Error: FileCheck exited with return code {file_check_process.returncode}")
            print("FileCheck stderr:")
            print(file_check_stderr.decode())
            return

        # If both processes succeeded, print the output
        print(f"Filecheck on {os.path.basename(filecheck_src)} succeed!")

    except Exception as e:
        print(f"Starting llvm toolchain failed: {e}")

def generate_valid_s(input_file, llvm_bin, output_file=""):
    """
    Generate the xxx-valid file from xxx.s using llvm-mc tool
    """

    # If output_file is not provided, generate it from input_file
    if not output_file:
        base_name = os.path.splitext(input_file)[0]
        file_name, _ = os.path.splitext(base_name)

        # Check if the file name already ends with '-valid'
        if file_name.endswith('-valid'):
            # simply ignore the *-valid files
            return
        output_file = base_name + "-valid.s"

    # Get the path to llvm-mc
    llvm_mc_path = os.path.join(llvm_bin, 'llvm-mc')
    if not os.path.isfile(llvm_mc_path):
        raise Exception(f"Error: llvm-mc not found at {llvm_mc_path}")

    # Construct the command to run llvm-mc
    llvm_mc_cmd = [llvm_mc_path, input_file, "-triple=riscv32", "-riscv-no-aliases", "-show-encoding"]

    try:
        # Run llvm-mc and capture the output
        llvm_mc_process = subprocess.Popen(
            llvm_mc_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        llvm_mc_output, llvm_mc_stderr = llvm_mc_process.communicate()

        if llvm_mc_process.returncode != 0:
            print(f"Error: llvm-mc exited with return code {llvm_mc_process.returncode}")
            print("llvm-mc stderr:")
            print(llvm_mc_stderr)
            return

        # Process the output and write to the output file
        with open(output_file, 'w') as outfile:
            # Write initial comments
            outfile.write('# FileCheck compatible validation tests\n')
            outfile.write('#  llvm-mc %s -triple=riscv32 -riscv-no-aliases -show-encoding \\\n')
            outfile.write('# | FileCheck -check-prefixes=CHECK-ASM %s\n\n\n')

            for line in llvm_mc_output.splitlines():
                # Check if the line contains an instruction with encoding
                # The line format is typically: '   instruction    # encoding: [0x.., 0x..]'
                match = re.match(r'^\s*(.*?)\s*# encoding:\s*\[(.*?)\]', line)
                if match:
                    instruction = match.group(1)
                    encoding = match.group(2)
                    # Write the CHECK-ASM line
                    check_line = f"# CHECK-ASM: encoding: [{encoding}]"
                    outfile.write(f"{check_line}\n{instruction}\n")

    except Exception as e:
        print(f"Error running llvm-mc: {e}")

if __name__ == "__main__":
    # Step 1: Generate valid check-files from rv32i assembler
    asm_dir = get_conf(key='ASM_DIR')
    llvm_bin = get_conf(key='LLVM_BIN')
    tool_dir = get_conf(key='TOOL_DIR')

    asm_files = get_filelist_with_pattern(pat='*.s', src_dir=asm_dir)
    for af in asm_files:
        generate_valid_s(input_file=af, llvm_bin=llvm_bin)

    # Step 2: Run llvm FileCheck
    fc_list = get_filelist_with_pattern(pat='*-valid.s', src_dir=asm_dir)
    for fc in fc_list:
        run_filecheck(fc)
