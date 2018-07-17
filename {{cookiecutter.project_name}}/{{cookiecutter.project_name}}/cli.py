"""
A bunch of command-line utils to help you do the chores.
"""

import shutil
import subprocess
from pathlib import Path

import click
import mpy_cross
import itertools

COMPILE_DIR = Path.cwd() / ".compiled"
ROOT_DIR = Path(__file__).parent
MICROPYTHON_DIR = ROOT_DIR / "micropython"
COMMON_DIR = ROOT_DIR / 'common'
AUTOSTART_PATH = (
        Path.home() / ".config" / "autostart" / "{{cookiecutter.project_name}}.desktop"
)

# files to put in the mpy board
PROJECT_FILES = itertools.chain((MICROPYTHON_DIR.glob('*.py'), COMMON_DIR.glob('*.py')))

# don't cross-compile these files
DONT_COMPILE = [MICROPYTHON_DIR / "main.py"]

AUTOSTART_FILE = f"""\
#!/usr/bin/env xdg-open
[Desktop Entry]
Type=Application
Name={{cookiecutter.project_name}}
Description={{cookiecutter.project_description}}
Exec={subprocess.check_output(["which", "python"], encoding='utf-8').strip()} -m {{cookiecutter.project_name}}.cli run\
"""


def clean_compiled():
    shutil.rmtree(COMPILE_DIR, ignore_errors=True)


clean_compiled()


def run_subproc(cmd: list) -> str:
    print("Run:", " ".join(map(str, cmd)))
    return subprocess.check_output(cmd)


def run_ampy_cmd(port: str, cmd: list) -> str:
    return run_subproc(["/usr/bin/env", "ampy", "-p", port] + cmd)


def cross_compile(input_path):
    output_path = COMPILE_DIR / (".".join(input_path.name.split(".")[:-1]) + ".mpy")
    mpy_corss_process = mpy_cross.run(input_path, "-o", output_path)

    if mpy_corss_process.wait() == 0:
        return output_path
    else:
        exit("Something bad happend!")


@click.group()
def cli():
    pass


@click.command(short_help="Put muro on MicroPython chip")
@click.option("--port", default="/dev/ttyUSB0", help="Serial port for connected board")
def install(port):
    """
    Puts the required code for muro to function
    on the MicroPython chip, using "ampy".

    By default, it uses /dev/ttyUSB0 as the port.

    It also uses the `mpy-cross` utility to cross compile the files, 
    which helps when the files are big.
    
    It also configures the application to be run at boot,
    using the `{{cookiecutter.project_name}} run` command.
    """

    board_dirs = run_ampy_cmd(port, ["ls"]).split()
    try:
        COMPILE_DIR.mkdir()

        for file_path in PROJECT_FILES:
            dir = file_path.parent.relative_to(MICROPYTHON_DIR)

            # ampy doesn't allow non-existent dirs, so have to create them.
            if file_path not in board_dirs:
                run_ampy_cmd(port, ["mkdir", dir])
                board_dirs.append(file_path)

            if file_path not in DONT_COMPILE:
                file_path = cross_compile(file_path)

            run_ampy_cmd(port, ["put", file_path])
    finally:
        clean_compiled()

    print(
        f"Adding {{cookiecutter.project_name}}.desktop to autostart... ({AUTOSTART_PATH})"
    )

    if not AUTOSTART_PATH.parent.exists():
        AUTOSTART_PATH.parent.mkdir(parents=True)

    with open(AUTOSTART_PATH, "w") as f:
        f.write(AUTOSTART_FILE)

    print("Done!")


@click.command()
def run():
    """Run {{cookiecutter.project_name}}"""

    from {{cookiecutter.project_name}}.{{cookiecutter.project_name}} import mainloop
    mainloop()


###########################################
# Add your own command-line utils here.   #
# For more information on how to do that, #
# check out the Click documentation :     #
#   http://click.pocoo.org                #
###########################################


cli.add_command(install)
cli.add_command(run)

if __name__ == "__main__":
    cli()
