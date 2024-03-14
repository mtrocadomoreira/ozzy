from datetime import timedelta
import time


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
