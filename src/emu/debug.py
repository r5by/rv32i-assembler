import os
import sys
import typing
from comm.colors import *
from comm.int32 import UInt32
from comm.logging import DEBUGGER_INFO, DEBUGGER_ERROR, DEBUGGER_WARN
from comm.exceptions import LaunchDebuggerException, InvalidAddressException, ProgramNormalExitException, \
    RV32IBaseException
from comm.utils import parse_numeric_argument

HIST_FILE = os.path.join(os.path.expanduser("~"), ".rv32emu_history")
from . import TranslatableInstruction

if typing.TYPE_CHECKING:
    from . import CPU

def print_help_info():
    DEBUGGER_INFO(FMT_DEBUG + "Welcome to the RV32Emu Debugger! Here are some commands you can use:" + FMT_NONE)
    DEBUGGER_INFO(FMT_INFO + "\t'i'  - Display the current instruction at the program counter." + FMT_NONE)
    DEBUGGER_INFO(FMT_INFO + "\t\tExample: 'i'" + FMT_NONE)
    DEBUGGER_INFO(FMT_INFO + "\t'c'  - Continue execution until the next breakpoint." + FMT_NONE)
    DEBUGGER_INFO(FMT_INFO + "\t\tExample: 'c'" + FMT_NONE)
    DEBUGGER_INFO(FMT_INFO + "\t's'  - Execute the next instruction (step into)." + FMT_NONE)
    DEBUGGER_INFO(FMT_INFO + "\t\tExample: 's'" + FMT_NONE)
    DEBUGGER_INFO(FMT_INFO + "\t'd'  - Dump memory or registers. Supports subcommands for specific dumps." + FMT_NONE)
    DEBUGGER_INFO(FMT_INFO + "\t\tExamples: 'd regs' to dump all registers," + FMT_NONE)
    DEBUGGER_INFO(FMT_INFO + "\t\t          'd a 4' to dump the contents of register a4," + FMT_NONE)
    DEBUGGER_INFO(FMT_INFO + "\t'ds' - Dump the stack." + FMT_NONE)
    DEBUGGER_INFO(FMT_INFO + "\t\tExample: 'ds'" + FMT_NONE)
    DEBUGGER_INFO(FMT_INFO + "\t'ri' - Run a specific instruction. You must specify the instruction and its operands." + FMT_NONE)
    DEBUGGER_INFO(FMT_INFO + "\t\tExample: 'ri add a0 a1 a2' to execute 'add' with operands a0, a1, and a2." + FMT_NONE)


def launch_debug_session(cpu: "CPU", prompt=""):
    if cpu.debugger_active:
        return
    import code
    import readline
    import rlcompleter

    cpu.debugger_active = True

    print_help_info()  # welcome banner

    def dump(*args):
        """
            Dump contents of registers
        """

        if not args:
            cpu.regs.dump_all()
            return

        reg_type = args[0]
        if reg_type not in ['a', 's', 't']:
            DEBUGGER_ERROR(f'Invalid register type: {reg_type}')
            return

        if len(args) == 1:
            # Dump all registers of a specific type
            cpu.regs.dump_by_type(t=reg_type)
        elif len(args) == 2:
            # Dump a specific register by name
            cpu.regs.dump_by_name(f'{reg_type}{args[1]}')
        elif len(args) == 3:
            # Dump a range of registers
            cpu.regs.dump_by_range(t=reg_type, l=int(args[1]), r=int(args[2]))

        else:
            DEBUGGER_ERROR(f'Dumping registers fails: wrong input arguments: {args}')

    def dump_mem(*args):
        if not args:
            raise InvalidAddressException(f'An address must be provided in order to dump memory.')

        addr = UInt32(parse_numeric_argument(args[0]))
        mmu.dump(addr, args[1:])

    def dump_stack(*args):
        #todo> support stack
        mmu.dump(regs.get_by_name("sp"), *args)

    def ins():
        current_instruction = mmu.read_ins(cpu.pc)
        DEBUGGER_INFO("Current instruction at 0x{:08X}: {}".format(cpu.pc, current_instruction))

    def cont():
        try:
            cpu.run()

        except RV32IBaseException as ex:
            if isinstance(ex, LaunchDebuggerException):
                DEBUGGER_WARN(FMT_DEBUG + "Returning to debugger...")
                return

            elif isinstance(ex, ProgramNormalExitException):

                DEBUGGER_WARN(FMT_DEBUG + "Exiting debugger...")
                cpu.halted = True  # Indicate that the CPU has halted
                raise ex

            else:
                DEBUGGER_ERROR(f"Unknown CPU state exception: {ex}")
                ex.print_stacktrace()

    def step():
        try:
            cpu.step()

        except RV32IBaseException as ex:
            if isinstance(ex, LaunchDebuggerException):
                raise ex

            elif isinstance(ex, ProgramNormalExitException):

                DEBUGGER_WARN(FMT_DEBUG + "Exiting debugger...")
                cpu.halted = True  # Indicate that the CPU has halted
                raise ex

            else:
                DEBUGGER_ERROR(f"Unknown CPU state exception: {ex}")
                ex.print_stacktrace()


    # Dictionary of aliases to function references
    aliases = {
        'i': ins,
        'c': cont,
        'n': step,
        'd': dump,
        'ds': dump_stack, # not supported yet
        'dm': dump_mem,
    }

    import shlex
    def handle_command(input_line):
        try:
            parts = shlex.split(input_line)
            if not parts:
                return  # Ignore empty input
            command = parts[0]
            args = parts[1:]  # Remaining parts are arguments

            # DEBUGGER_INFO(f'command: {command}')
            # DEBUGGER_INFO(f'args: {args}')
            if command not in aliases:
                DEBUGGER_ERROR("Unknown command")
                print_help_info()

            if args:
                aliases[command](*args)
            else:
                aliases[command]()

        except Exception as e:
            DEBUGGER_ERROR(f"Error executing command: {str(e)}")

    # Command loop within interactive console
    class CustomConsole(code.InteractiveConsole):
        def raw_input(self, prompt=""):
            line = input(prompt)
            handle_command(line)
            return ''

    # Setup the environment
    registers = cpu.regs
    regs = cpu.regs
    memory = cpu.mmu
    mem = cpu.mmu
    mmu = cpu.mmu
    locals().update(aliases)

    sess_vars = globals()
    sess_vars.update(locals())
    readline.set_completer(rlcompleter.Completer(sess_vars).complete)
    readline.parse_and_bind("tab: complete")
    if os.path.exists(HIST_FILE):
        readline.read_history_file(HIST_FILE)

    # Launch custom interactive console
    try:
        CustomConsole(sess_vars).interact(
            banner=FMT_DEBUG + prompt + FMT_NONE,
            exitmsg="Exiting debugger",
        )
    except RV32IBaseException as ex:

        if isinstance(ex, ProgramNormalExitException):

            # If CPU has halted, exit the function
            if cpu.halted:
                return

        else:
            ex.print_stacktrace()
            sys.exit(-1)

    finally:
        cpu.debugger_active = False
        readline.write_history_file(HIST_FILE)

