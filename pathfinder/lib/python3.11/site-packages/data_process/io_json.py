import os
import json
from .green_dict import json_dumps
from .io_files import prepare_dir


def read_json(fp):
    if not os.path.exists(fp):
        return None

    with open(fp) as f:
        return json.loads(f.read())


def write_json(data, out_path, **kwargs):
    prepare_dir(out_path)
    with open(out_path, "w") as f:
        return f.write(json_dumps(data, **kwargs))
