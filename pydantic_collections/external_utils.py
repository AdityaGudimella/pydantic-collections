"""Utility functions for pydantic-collections.

Important:
---------
    None of the imported modules in this file should import from pydantic_collections.

"""
import contextlib
import functools
import types
import typing as t

import typing_extensions as te
from pydantic_core import ErrorDetails, InitErrorDetails
from typing_extensions import get_args, get_origin

UnionType = getattr(types, "UnionType", t.Union)


def get_types_from_annotation(
    tp: t.Type[t.Any],  # noqa: ANN401
) -> t.Generator[t.Union[type, t.Any], None, None]:
    """Return a generator that yields all the types that are part of given annotation.

    Args:
    ----
    tp: Type
        The type annotation to extract types from.

    Yields:
    ------
    Generator[Union[type, Any], None, None]
        A generator that yields all the types that are part of the annotation.
    """
    origin = get_origin(tp)
    if origin is t.Union or origin is UnionType:
        for sub_tp in get_args(tp):
            yield from get_types_from_annotation(sub_tp)
    elif isinstance(tp, type):
        yield tp
    else:
        yield origin


def wrap_errors_with_loc(
    *,
    errors: list[ErrorDetails],
    loc_prefix: tuple[str | int, ...],
) -> list[InitErrorDetails]:
    """Wrap errors with a location prefix.

    Args:
    ----
    errors: list[ErrorDetails]
        The list of errors to wrap.
    loc_prefix: tuple[str | int, ...]
        The location prefix to add to the errors.

    Returns:
    -------
    list[InitErrorDetails]
        The list of wrapped errors.
    """
    return [
        t.cast(InitErrorDetails, {**err, "loc": loc_prefix + err.get("loc", ())})
        for err in errors
    ]


_P = te.ParamSpec("_P")
_R_co = t.TypeVar("_R_co", covariant=True)


class _FuncT(te.Protocol[_P, _R_co]):
    def __call__(self, *args: _P.args, **kwargs: _P.kwargs) -> _R_co:
        ...


def tp_cache(func: _FuncT[_P, _R_co]) -> _FuncT[_P, _R_co]:
    """Cache __getitem__ of generic types with a fallback for non-hashable arguments.

    Args:
    ----
    func: _FuncT
        The function to be cached.
        This function will be used as a fallback for non-hashable arguments.

    Returns:
    -------
        The cached function.
    """
    cached = functools.lru_cache(maxsize=None, typed=True)(func)

    @functools.wraps(func)
    def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R_co:
        with contextlib.suppress(TypeError):
            # Try to use the cached version.
            return cached(*args, **kwargs)
        # Fallback to the original function.
        return func(*args, **kwargs)

    return inner
