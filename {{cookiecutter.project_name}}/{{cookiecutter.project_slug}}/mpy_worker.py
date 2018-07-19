"""
A worker that runs on a Micropython board.

The data within "{{" & "}}" is populated by a Jinja2 template engine.
"""

import uos as os
import uhashlib as hashlib


def get_parent_path(path: str) -> str:
    return "/".join(path.split("/")[:-1])


def did_it_change(file_to_check: str, file_hash: bytes) -> int:
    try:
        with open(file_to_check, "rb") as fp:
            file_data = fp.read()
    except OSError:
        return 1
    else:
        return int(hashlib.sha1(file_data).digest() != file_hash)


def mkdir_with_parents(dir: str) -> None:
    if dir:
        mkdir_with_parents(get_parent_path(dir))
        try:
            os.mkdir(dir)
        except OSError:
            pass
    else:
        return


def rmdir_with_children(directory):
    os.chdir(directory)
    for f in os.listdir():
        try:
            os.remove(f)
        except OSError:
            pass
    for f in os.listdir():
        rmdir_with_children(f)
    os.chdir("..")
    os.rmdir(directory)


def remove_unwanted(dir_or_file):
    try:
        # if its a directory, then it should provide some children.
        children = os.listdir(dir_or_file)
    except OSError:
        # probably a file, remove if not required.
        if dir_or_file not in required_files:
            try:
                os.remove(dir_or_file)
            except OSError:
                pass
    else:
        # probably a directory, remove if not required.
        if dir_or_file not in required_dirs:
            try:
                rmdir_with_children(dir_or_file)
            except OSError:
                pass

        # queue the children to be inspected in next iteration (with correct path).
        for child in children:
            remove_unwanted(dir_or_file + "/" + child)


# gather information from Jinja template variables
required_files = {{required_files}}
required_files_with_hash = {{required_files_with_hash}}
required_dirs = {{required_dirs}}
required_dirs.add("boot.py")  # avoid fucking up the boot.py.

# Remove unwanted files / directories
remove_unwanted(os.getcwd())

# create necessary dirs
for dir in required_dirs:
    mkdir_with_parents(dir)

# inform everyone which files have changed
for file_and_hash in required_files_with_hash:
    print(did_it_change(*file_and_hash), end=" ")
