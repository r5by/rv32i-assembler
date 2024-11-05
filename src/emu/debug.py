import os.path
import typing
from comm.colors import *
from comm.logging import INFO
from comm.exceptions import LaunchDebuggerException

HIST_FILE = os.path.join(os.path.expanduser("~"), ".rv32emu_history")

from . import TranslatableInstruction

if typing.TYPE_CHECKING:
    from . import CPU


def launch_debug_session(cpu: "CPU", prompt=""):
    if cpu.debugger_active:
        return
    import code
    import readline
    import rlcompleter

    # set the active debug flag
    cpu.debugger_active = True

    # setup some aliases:
    registers = cpu.regs
    regs = cpu.regs
    memory = cpu.mmu
    mem = cpu.mmu
    mmu = cpu.mmu

    # setup helper functions:
    def dump(what, *args, **kwargs):
        if what == regs:
            regs.dump(*args, **kwargs)
        else:
            mmu.dump(what, *args, **kwargs)

    def dump_stack(*args, **kwargs):
        mmu.dump(regs.get_by_name("sp"), *args, **kwargs)

    def ins():
        current_instruction = mmu.read_ins(cpu.pc)
        INFO("Current instruction at 0x{:08X}: {}".format(cpu.pc, current_instruction))

    #todo>
    def run_ins(name, *args: str):
        if len(args) > 3:
            print("Invalid arg count!")
            return
        # context = mmu.context_for(cpu.pc)

        ins = TranslatableInstruction(name, tuple(args), cpu.pc)
        # ins = SimpleInstruction(name, tuple(args), context, cpu.pc)
        print(FMT_DEBUG + "Running instruction {}".format(ins) + FMT_NONE)
        cpu.run_instruction(ins)

    def cont(verbose=False):
        try:
            cpu.run()
        except LaunchDebuggerException:
            print(FMT_DEBUG + "Returning to debugger...")
            return

    def step():
        try:
            cpu.step()
        except LaunchDebuggerException:
            return

    # aliases here
    aliases = {
        'c': cont,
        's': step,
        'd': dump,
        'ds': dump_stack,
        'ri': run_ins,
    }

    # Add aliases to locals
    locals().update(aliases)

    # collect all variables
    sess_vars = globals()
    sess_vars.update(locals())

    # add tab completion
    readline.set_completer(rlcompleter.Completer(sess_vars).complete)
    readline.parse_and_bind("tab: complete")
    if os.path.exists(HIST_FILE):
        readline.read_history_file(HIST_FILE)

    relaunch_debugger = False

    try:
        code.InteractiveConsole(sess_vars).interact(
            banner=FMT_DEBUG + prompt + FMT_NONE,
            exitmsg="Exiting debugger",
        )
    finally:
        cpu.debugger_active = False
        readline.write_history_file(HIST_FILE)
