"""A bunch of command-line utils to help you do the chores."""

import shutil
import subprocess
import tempfile
from pathlib import Path
from jinja2 import Template

import click
import mpy_cross
import hashlib
from typing import List

COMPILE_DIR = Path.cwd() / ".compiled"
AUTO_START_PATH = Path.home() / ".config" / "autostart" / "muro.desktop"
THIS_DIR = Path(__file__).parent
MPY_DIR = THIS_DIR / "micropython"
MPY_WORKER_TEMPLATE = THIS_DIR / "mpy_worker.py"
COMMON_DIR = THIS_DIR / "common"
PROJECT_FILES = [*MPY_DIR.rglob("*.py"), *COMMON_DIR.rglob("*.py")]

AUTO_START_FILE = f"""\
#!/usr/bin/env xdg-open
[Desktop Entry]
Type=Application
Name={{cookiecutter.project_name}}
Description={{cookiecutter.project_description}}
Exec={subprocess.check_output(["which", "python"], encoding="utf-8").strip()} -m {{cookiecutter.project_slug}}.cli run\
"""


def clean_compiled():
    shutil.rmtree(COMPILE_DIR, ignore_errors=True)


clean_compiled()


def run_subproc(cmd: list, silent=False) -> str:
    if not silent:
        print("Run:", " ".join(map(str, cmd)))
    return subprocess.check_output(cmd, encoding="utf-8")


def run_ampy_cmd(port: str, cmd: list, silent=False) -> str:
    return run_subproc(["/usr/bin/env", "ampy", "-p", port] + cmd, silent)


def run_code_on_board(port: str, code_as_str: str, silent=False) -> str:
    with tempfile.NamedTemporaryFile(mode="w") as fp:
        fp.write(code_as_str)
        fp.flush()
        return run_ampy_cmd(port, ["run", fp.name], silent)


def save_code_on_board(
        port: str, code_as_str: str, file_name_on_board: str, silent=False
) -> str:
    with tempfile.NamedTemporaryFile(mode="w") as fp:
        fp.write(code_as_str)
        fp.flush()
        return run_ampy_cmd(port, ["put", fp.name, file_name_on_board], silent)


def cross_compile(input_path: Path) -> Path:
    output_path = COMPILE_DIR / (".".join(input_path.name.split(".")[:-1]) + ".mpy")
    mpy_corss_process = mpy_cross.run(input_path, "-o", output_path)

    if mpy_corss_process.wait() == 0:
        return output_path
    else:
        exit("Something bad happened!")


class File:
    def __init__(self, file_path: Path):
        self.path = file_path
        self.path_compiled = cross_compile(file_path)

        with open(self.path_compiled, "rb") as fp:
            self.hash = hashlib.sha1(fp.read()).digest()

        self.path_on_board = str(
            file_path.relative_to(THIS_DIR.parent).with_suffix(
                self.path_compiled.suffix
            )
        )
        self.dir_path_parts_on_board = file_path.parent.relative_to(
            THIS_DIR.parent
        ).parts

    def __repr__(self):
        return f"<File path: {self.path}>"


def create_mpy_code(project_files: List[File]) -> str:
    with open(MPY_WORKER_TEMPLATE, "r") as fp:
        return Template(fp.read()).render(
            dirs_to_create={file.dir_path_parts_on_board for file in project_files},
            all_files={file.path_on_board for file in project_files},
            all_files_with_hash={
                (file.path_on_board, file.hash) for file in project_files
            },
        )


@click.group()
def cli():
    pass


@click.command(short_help="Put glove on MicroPython board")
@click.option(
    "--port", default="/dev/ttyUSB0", help="USB serial port for connected board"
)
def install(port):
    """
    Puts the required code for glove to function
    on the MicroPython chip, using "ampy".

    By default, it uses /dev/ttyUSB0 as the port.

    It also uses the `mpy-cross` utility to cross compile the files,
    which helps when the files are big.

    It also configures the application to be run at boot,
    using the `glove run` command.
    """

    try:
        COMPILE_DIR.mkdir()

        project_files = [File(file_path) for file_path in PROJECT_FILES]
        mpy_code = create_mpy_code(project_files)

        print("Analysing board...")
        code_output = run_code_on_board(port, mpy_code, silent=True)

        for file, did_change in zip(project_files, code_output.strip().split()):
            if int(did_change):
                run_ampy_cmd(port, ["put", file.path_compiled, file.path_on_board])
    finally:
        clean_compiled()

    print('Configuring "main.py"...')
    save_code_on_board(port, "import glove.micropython.glove", "main.py", silent=True)

    if click.confirm("Add `glove run` to auto-start?", default=False):
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
