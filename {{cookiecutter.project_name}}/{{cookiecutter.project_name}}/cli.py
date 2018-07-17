"""
A bunch of command-line utils to help you do the chores.
"""

import shutil
import subprocess
from pathlib import Path

import click
import mpy_cross
from pulsectl import Pulse

from muro.muro_cpy import mainloop, list_players

COMPILE_DIR = Path.cwd() / ".compiled"
MICROPYTHON_DIR = Path(__file__).parent / "micropython"
AUTOSTART_PATH = (
    Path.home() / ".config" / "autostart" / "{{cookiecutter.project_name}}.desktop"
)

INCLUDE_FILES = MICROPYTHON_DIR.glob()  # files to put in the mpy board
DONT_COMPILE = [MICROPYTHON_DIR / "main.py"]  # don't cross-compile these files

AUTOSTART_FILE = f"""\
#!/usr/bin/env xdg-open
[Desktop Entry]
Type=Application
Name={{cookiecutter.project_name}}
Description={{cookiecutter.project_description}}
Exec={subprocess.check_output(["which", "python"], encoding='utf-8').strip()} -m {{cookiecutter.project_name}}.cli run\
"""


def clean_compiled():
    shutil.rmtree(COMPILED_DIR, ignore_errors=True)


clean_compiled()


def run_subproc(cmd):
    print("Run:", " ".join(map(str, cmd)))
    subprocess.check_call(cmd)


def run_ampy_cmd(port, cmd):
    return run_subproc(["/usr/bin/env", "ampy", "-p", port] + cmd)


def cross_compile(input_path):
    output_path = COMPILED_DIR / (".".join(input_path.name.split(".")[:-1]) + ".mpy")
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

    ampy_dirs = run_ampy_cmd("ls").split()
    try:
        COMPILED_DIR.mkdir()

        for file_path in TO_INCLUDE:
            # ampy doesn't allow non-existent dirs, so have to create them.
            if file_path not in dirs:
                run_ampy_cmd(["mkdir", dirname])
                ampy_dirs.append(file_path)

            if file_path not in DONT_COMPILE:
                file_path = cross_compile(file_path)

            run_subproc(
                get_ampy_cmd(port)
                + ["put", file_path, file_path.relative_to(MICROPYTHON_DIR)]
            )
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
    mainloop()


###########################################
# Add your own command-line utils here.   #
# For more information on how to do that, #
# check out the Click documentation :     #
#   http://click.pocoo.org                #
###########################################


cli.add_command(install)
cli.add_command(run)
cli.add_command(autostart)

if __name__ == "__main__":
    cli()
