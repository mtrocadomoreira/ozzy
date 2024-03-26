import functools

import xarray as xr


def wrap_funcs(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        result = func(*args, **kwargs)
        # print(result)
        if isinstance(result, tuple):
            for res in result:
                res = Wrapper(res) if isinstance(res, xr.Dataset) else res
        else:
            if isinstance(result, xr.Dataset):
                result = Wrapper(result)
        return result

    return wrapped


# for name in dir(xr):
#     itemi = getattr(xr, name)

for name, itemi in xr.__dict__.items():
    if callable(itemi) & ~isinstance(itemi, type):
        # print(f"{item}")

        @wrap_funcs
        def newfunc(*args, **kwargs):
            return itemi(*args, **kwargs)

        # exec(f"{name} = newfunc")
        exec(f"{name} = wrap_funcs(itemi)")

        # def name(*args, **kwargs):
        #     return item(*args, **kwargs)


# print(merge())

print(type(merge))


class Wrapper(xr.Dataset):
    pass


@wrap_funcs
def new_merge(*args, **kwargs):
    return xr.merge(*args, **kwargs)


ds = Wrapper()
print(type(ds))
print(type(merge([ds, ds])))
