"""
A worker that runs on a Micropython board.

The data within "{{" & "}}" is populated by a Jinja2 template engine.
"""

import uos as os
import uhashlib as hashlib


def get_path_parent(path: str) -> str:
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
        mkdir_with_parents(get_path_parent(dir))

        try:
            os.mkdir(dir)
        except OSError:
            pass
    else:
        return


def list_all_files_and_dirs() -> tuple:
    files, dirs = set(), set()
    next_one = set(os.listdir())  # some seed, to start the fire.

    while next_one:
        # create a copy so we can sleep at night (iteration + mutation = no sleep).
        this_one = next_one.copy()
        next_one = set()

        for something in this_one:
            # looks like we have something, let's inspect.
            try:
                # if its a directory, then it should provide some children.
                children = os.listdir(something)
            except OSError:
                # if "something" was a file, then it will bleed here. (files hate listdir())
                files.add(something)
            else:
                # dirs pass through there.
                dirs.add(something)
                # queue the children to be inspected in next iteration (with correct path).
                next_one.update([something + "/" + child for child in children])

    return files, dirs


all_files, all_dirs = list_all_files_and_dirs()

# remove trash files
for file in all_files:
    if file not in {{required_files}}:
        try:
            os.remove(file)
        except OSError:
            pass

# remove trash dirs
for dir in all_dirs:
    if dir not in {{required_dirs}}:
        try:
            os.rmdir(dir)
        except OSError:
            pass

# create necessary dirs
for dir in {{required_dirs}}:
    mkdir_with_parents(dir)

# inform everyone that files have changed
for i in {{required_files_with_hash}}:
    print(did_it_change(*i), end=" ")
