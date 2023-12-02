import inspect
import logging


def catch(function: callable) -> callable:
    def wrapper(*args, **kwargs) -> object:
        spec = inspect.getfullargspec(function).args

        try:
            args_repr = [f"{type(chunk).__name__} {spec[index]} = {repr(chunk)}" for index, chunk in enumerate(args)]
        except IndexError:
            args_repr = [repr(chunk) for chunk in args]

        kwargs_repr = [f"{type(value).__name__} {key} = {value}" for key, value in kwargs.items()]

        try:
            return function(*args, **kwargs)
        except Exception as error:
            logger = logging.getLogger()
            logger.info(
                f"Caught function call "
                f"'{function.__name__}' "
                f"with arguments: "
                f"{', '.join(args_repr + kwargs_repr)}"
            )
            logger.error(error)

            return None

    return wrapper
