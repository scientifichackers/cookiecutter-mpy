"""A bunch of command-line utils to help you do the chores."""

import shutil
import subprocess
import tempfile
from pathlib import Path

import click
import mpy_cross

COMPILE_DIR = Path.cwd() / ".compiled"
AUTO_START_PATH = Path.home() / ".config" / "autostart" / "muro.desktop"
ROOT_DIR = Path(__file__).parent
MICRO_PYTHON_DIR = ROOT_DIR / "micropython"
COMMON_DIR = ROOT_DIR / "common"

# files to put in the micropython board
PROJECT_FILES = [*MICRO_PYTHON_DIR.glob("*.py"), *COMMON_DIR.glob("*.py")]

AUTO_START_FILE = f"""\
#!/usr/bin/env xdg-open
[Desktop Entry]
Type=Application
Name={{cookiecutter.project_name}}
Description={{cookiecutter.project_description}}
Exec={subprocess.check_output(["which", "python"], encoding="utf-8").strip()} -m {{cookiecutter.project_slug}}.cli run\
"""

MPY_DIR_MAKER = """\
import uos as os


def makedirs(dir_parts: tuple):
    parent_parts = dir_parts[:-1]

    if parent_parts:
        makedirs(parent_parts)

        try:
            os.mkdir("/".join(dir_parts))
        except OSError:
            pass
    else:
        return


for file_path_parts in {}:
    makedirs(file_path_parts)
"""


def clean_compiled():
    shutil.rmtree(COMPILE_DIR, ignore_errors=True)


clean_compiled()


def run_subproc(cmd: list) -> str:
    print("Run:", " ".join(map(str, cmd)))
    return subprocess.check_output(cmd, encoding="utf-8")


def run_ampy_cmd(port: str, cmd: list) -> str:
    return run_subproc(["/usr/bin/env", "ampy", "-p", port] + cmd)


def run_code_on_board(port: str, code_as_str: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w") as fp:
        fp.write(code_as_str)
        fp.flush()
        return run_ampy_cmd(port, ["run", fp.name])


def save_code_on_board(port: str, code_as_str: str, file_name_on_board: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w") as fp:
        fp.write(code_as_str)
        fp.flush()
        return run_ampy_cmd(port, ["put", fp.name, file_name_on_board])


def cross_compile(input_path: Path) -> Path:
    output_path = COMPILE_DIR / (".".join(input_path.name.split(".")[:-1]) + ".mpy")
    mpy_corss_process = mpy_cross.run(input_path, "-o", output_path)

    if mpy_corss_process.wait() == 0:
        return output_path
    else:
        exit("Something bad happened!")


@click.group()
def cli():
    pass


@click.command(short_help="Put {{cookiecutter.project_name}} on MicroPython board")
@click.option(
    "--port", default="/dev/ttyUSB0", help="USB serial port for connected board"
)
def install(port):
    """
    Puts the required code for {{cookiecutter.project_name}} to function
    on the MicroPython chip, using "ampy".

    By default, it uses /dev/ttyUSB0 as the port.

    It also uses the `mpy-cross` utility to cross compile the files, 
    which helps when the files are big.
    
    It also configures the application to be run at boot,
    using the `{{cookiecutter.project_name}} run` command.
    """

    run_code_on_board(
        port,
        MPY_DIR_MAKER.format(
            {
                file_path.parent.relative_to(ROOT_DIR.parent).parts
                for file_path in PROJECT_FILES
            }
        ),
    )

    try:
        COMPILE_DIR.mkdir()

        for file_path in PROJECT_FILES:
            file_path_for_board = file_path.relative_to(ROOT_DIR.parent)
            compiled_file_path = cross_compile(file_path)

            run_ampy_cmd(
                port,
                [
                    "put",
                    compiled_file_path,
                    str(file_path_for_board.with_name(compiled_file_path.name)),
                ],
            )
    finally:
        clean_compiled()

    save_code_on_board(
        port,
        "import {{cookiecutter.project_slug}}.micropython.{{cookiecutter.project_slug}}",
        "main.py",
    )

    if click.confirm(
        "Add `{{cookiecutter.project_name}} run` to auto-start?", default=False
    ):
        print(f"Adding to auto-start... ({AUTO_START_PATH})")

        if not AUTO_START_PATH.parent.exists():
            AUTO_START_PATH.parent.mkdir(parents=True)

        with open(AUTO_START_PATH, "w") as f:
            f.write(AUTO_START_FILE)

    print("Done!")


@click.command()
def run():
    """Run {{cookiecutter.project_name}}"""

    import {{cookiecutter.project_slug}}.{{cookiecutter.project_slug}}


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
