import typing


_T = typing.TypeVar("_T", bound=typing.Callable[..., typing.Any])


def override(function: _T) -> _T:
    function.is_overridden = True

    return function
