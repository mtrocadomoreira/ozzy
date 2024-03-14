from datetime import timedelta
import time
import numpy as np


# Decorators


def stopwatch(method):
    def timed(*args, **kw):
        ts = time.perf_counter()
        result = method(*args, **kw)
        te = time.perf_counter()
        duration = timedelta(seconds=te - ts)
        print(f"    -> {method.__name__} took: {duration}")
        return result

    return timed


# Consistent output


def print_file_item(file):
    print("  - " + file)


# String manipulation


def unpack_str(attr):
    if isinstance(attr, np.ndarray):
        result = attr[0]
    else:
        result = attr
    return result


def tex_format(str):
    if str == "":
        newstr = str
    else:
        newstr = "$" + str + "$"
    return newstr
