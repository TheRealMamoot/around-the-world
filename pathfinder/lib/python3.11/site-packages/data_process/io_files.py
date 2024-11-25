import os
import glob


def file_list_in(root, pattern, **kwargs):
    pattern = os.path.join(root, pattern)
    rv = glob.glob(pattern, **kwargs)
    rv = [os.path.relpath(x, root) for x in rv]
    return rv


def prepare_dir(path):
    if not path.endswith("/"):
        path = os.path.dirname(path)

    if not path:
        return

    if not os.path.isdir(path):
        os.makedirs(path)
