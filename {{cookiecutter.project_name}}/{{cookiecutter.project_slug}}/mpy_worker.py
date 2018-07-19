"""
A worker that runs on a Micropython board.

The data within "{{" & "}}" is populated by a Jinja2 template engine.
"""

import uos as os
import uhashlib as hashlib


def did_it_change(file_to_check: str, file_hash: bytes) -> int:
    try:
        with open(file_to_check, "rb") as fp:
            file_data = fp.read()
    except OSError:
        return 0
    else:
        return int(hashlib.sha1(file_data).digest() != file_hash)


def mkdir_with_parents(dir_parts: tuple) -> None:
    parent_parts = dir_parts[:-1]

    if dir_parts:
        mkdir_with_parents(parent_parts)

        try:
            os.mkdir("/".join(dir_parts))
        except OSError:
            pass
    else:
        return


def list_all_files() -> set:
    result = set()
    next_one = set(os.listdir())  # some seed, to start the fire.

    while next_one:
        # create a copy so we can sleep at night (iteration + mutation = no sleep).
        this_one = next_one.copy()
        next_one = set()

        for something in this_one:
            # looks like we have something, let's inspect.
            try:
                # if its a directory, then it shall provide some children.
                children = os.listdir(something)
            except OSError:
                # if not, then it's a file, and we shall put it in the result.
                result.add(something)
            else:
                # queue the children to be inspected in next iteration (with correct path).
                next_one.update([something + "/" + child for child in children])

    return result


# remove trash dirs / files
for file in list_all_files():
    if file not in {{all_files}}:
        os.remove(file)

        dir = "/".join(file.split("/")[:-1])
        try:
            # remove the dir containing this file, if it's empty.
            if not os.listdir(dir):
                os.rmdir(dir)
        except OSError:
            pass

# create necessary dirs
for file in {{dirs_to_create}}:
    mkdir_with_parents(file)

# inform everyone about files have changed
for i in {{all_files_with_hash}}:
    print(did_it_change(*i), end=" ")
