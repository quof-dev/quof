import functools
import typing
import inspect


def strict_types(function):
    print(id(function))
    print(inspect.getfullargspec(function))

    def type_checker(*args, **kwargs):
        hints = typing.get_type_hints(function)

        all_args = kwargs.copy()
        all_args.update(dict(zip(function.__code__.co_varnames, args)))

        for argument, argument_type in ((i, type(j)) for i, j in all_args.items()):
            if argument in hints:
                if not issubclass(argument_type, hints[argument]):
                    raise TypeError('Type of {} is {} and not {}'.format(argument, argument_type, hints[argument]))

        result = function(*args, **kwargs)

        if 'return' in hints:
            if type(result) != hints['return']:
                raise TypeError('Type of result is {} and not {}'.format(type(result), hints['return']))

        return result

    return type_checker


def overload(function: typing.Callable):
    functions = [function]

    @functools.wraps(function)
    def wrapper(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        for function_object in functions:
            if isinstance(function_object, type):
                func = function_object.__new__
            elif isinstance(function_object, (classmethod, staticmethod)):
                func = function_object.__get__(function_object.__class__)
            else:
                func = function_object

            _args = list(args)
            _kwargs = dict(kwargs)

            _defaults = list(func.__defaults__ or [])

            arguments = []
            for index in range(func.__code__.co_argcount):
                argument = func.__code__.co_varnames[index]

                if not index and isinstance(function, (type, classmethod)):
                    continue

                if _args:
                    value = _args.pop(0)
                elif argument in _kwargs:
                    value = _kwargs.pop(argument)
                elif _defaults:
                    value = _defaults.pop(0)
                else:
                    break

                annotation = typing.get_type_hints(function_object).get(argument)
                if isinstance(annotation, type) and not isinstance(value, annotation):
                    break

                arguments.append(value)
            else:
                if _args:
                    if func.__code__.co_flags & 0x04:
                        arguments.extend(_args)
                    else:
                        continue
                if _kwargs:
                    if not func.__code__.co_flags & 0x08:
                        continue

                if isinstance(function, (classmethod, staticmethod)):
                    return func(*arguments, **_kwargs)
                else:
                    return function(*arguments, **_kwargs)

        raise TypeError("An overloaded function cannot be called due to a type mismatch in the arguments passed!")

    def append(func: typing.Callable):
        functions.append(func)

        return wrapper

    wrapper.append = append

    return wrapper


@strict_types
def test(args: str, a: int) -> None:
    ...


@strict_types
def test():
    ...


print(test("1", a=2))
