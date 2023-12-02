import inspect
import logging


def catch(function):
    """ Decorator that registers attributes coming into the function and errors. """

    def wrapper(*args, **kwargs):
        spec = inspect.getfullargspec(function).args

        try:
            args_repr = [f"{type(chunk).__name__} {spec[index]} = {repr(chunk)}" for index, chunk in enumerate(args)]
        except IndexError:
            args_repr = [repr(chunk) for chunk in args]

        kwargs_repr = [f"{type(value).__name__} {key} = {value}" for key, value in kwargs.items()]

        logging.debug(f"Function '{function.__name__}' called with ::= {', '.join(args_repr + kwargs_repr)}")

        try:
            return function(*args, **kwargs)
        except Exception as error:
            logging.error(error, exc_info=True)
            return None

    return wrapper
