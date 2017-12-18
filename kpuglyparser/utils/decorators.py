def compose(*functions):
    def inner(arg):
        for f in functions:
            arg = f(arg)
        return arg
    return inner


def to_map(function):
    def inner(arg):
        return map(function, arg)
    return inner


def to_filter(function):
    def inner(arg):
        return filter(function, arg)
    return inner
