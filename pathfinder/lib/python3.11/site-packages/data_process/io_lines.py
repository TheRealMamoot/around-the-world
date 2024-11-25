def read_lines(path):
    rv = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                rv.append(line)

    return rv
