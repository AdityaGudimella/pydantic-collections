"""MutableSequence[pydantic.BaseModel] implementation."""
import typing as t
from collections import abc as cabc

import typing_extensions as te
from pydantic import RootModel
from pydantic_collections.api import DataBase

from pydantic_collections.core import BaseCollectionModel, BaseModelT

_T_contra = t.TypeVar("_T_contra", contravariant=True)


class _SupportsDunderLT(t.Protocol[_T_contra]):
    def __lt__(self, __other: _T_contra) -> bool:
        ...


class _SupportsDunderGT(t.Protocol[_T_contra]):
    def __gt__(self, __other: _T_contra) -> bool:
        ...


_SupportsRichComparison: te.TypeAlias = t.Union[
    _SupportsDunderLT[t.Any], _SupportsDunderGT[t.Any]
]


class _SortedKey(t.Protocol[_T_contra]):
    """Protocol for key function of the `sorted` built-in function."""

    def __call__(self, x: _T_contra) -> _SupportsRichComparison:
        ...


class PydanticSequence(
    BaseCollectionModel[BaseModelT],
    RootModel[list[BaseModelT]],
    cabc.MutableSequence[BaseModelT],
):
    """A MutableSequence of Pydantic models."""

    def __init__(
        self,
        *data: BaseModelT,
        root: t.Sequence[BaseModelT] | None = None,  # noqa: ANN401
        **kwargs: t.Any,  # noqa: ANN401
    ) -> None:
        """Initialize PydanticSequence.

        Note:
        ----
            A separate initializer is provided for the following reasons:
            - Make root argument optional.
            - Make root argument positional or keyword.
            - Provide *data argument
        """
        if root is None:
            root = []
        root = list(root) if root else []
        if root and kwargs:
            raise ValueError("Cannot provide both data and **kwargs.")
        if kwargs:
            super().__init__(**kwargs)
        else:
            super().__init__(root=root + list(data))

    def _validate_sequence_element_type(
        self, value: t.Any, index: int  # noqa: ANN401
    ) -> None:
        return super()._validate_element_type(value, (index,))

    def _validate_sequence_element(
        self, value: t.Any, index: int  # noqa: ANN401
    ) -> BaseModelT:
        return super()._validate_element(value, (index,))

    def __len__(self) -> int:
        return len(self.root)

    @te.overload
    def __getitem__(self, index: int) -> BaseModelT:
        ...

    @te.overload
    def __getitem__(self, index: slice) -> "BaseCollectionModel[BaseModelT]":
        ...

    def __getitem__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, index: int | slice
    ) -> t.Union[BaseModelT, "BaseCollectionModel[BaseModelT]"]:
        if isinstance(index, slice):
            return self.__class__(self.root[index])
        else:
            return self.root[index]

    @t.overload
    def __setitem__(self, index: int, value: BaseModelT) -> None:
        ...

    @t.overload
    def __setitem__(self, index: slice, value: t.Iterable[BaseModelT]) -> None:
        ...

    def __setitem__(
        self, index: int | slice, value: BaseModelT | t.Iterable[BaseModelT]
    ) -> None:
        if isinstance(index, slice):
            for index, each_value in zip(
                self._get_index_range(index), value, strict=True
            ):
                self.root[index] = self._validate_sequence_element(each_value, index)
        else:
            self.root[index] = self._validate_sequence_element(value, index)

    def __delitem__(self, index: t.Union[int, slice]) -> None:
        del self.root[index]

    def __iter__(self) -> t.Iterator[BaseModelT]:  # type: ignore
        return iter(self.root)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.root!r})"

    def __str__(self) -> str:
        return repr(self)  # pragma: no cover

    def insert(self, index: int, value: BaseModelT) -> None:
        """Insert value before index."""
        self.root.insert(index, self._validate_sequence_element(value, index))

    def sort(self, key: _SortedKey[BaseModelT], reverse: bool = False) -> None:
        """Sort the sequence in place."""
        self.root = sorted(self.root, key=key, reverse=reverse)

    def _get_index_range(self, index: slice) -> t.Iterable[int]:
        """Get the range of indices for a slice."""
        start, stop, step = index.start, index.stop, index.step
        if step is None:
            step = 1
        if start is None:
            start = 0
        if stop is None:
            stop = len(self.root)
        return range(start, stop, step or 1)


_KeyT = t.TypeVar("_KeyT")


class PersistentPydanticSequence(
    PydanticSequence[BaseModelT], t.Generic[_KeyT, BaseModelT]
):
    """A PydanticSequence that persists its data to a file."""

    def __init__(
        self,
        *data: BaseModelT,
        persistence_db_overwrite: bool = False,
        persistence_db: DataBase[_KeyT, BaseModelT],
        persistance_db_key: str | t.Callable[[BaseModelT], _KeyT],
        root: t.Sequence[BaseModelT] | None = None,
        **kwargs: t.Any,  # noqa: ANN401
    ) -> None:
        """Initialize PersistentPydanticSequence.

        Args:
        ----
        persistence_db_overwrite: bool
            Whether to overwrite the database with the data in the sequence.
        persistence_db: DataBase[_KeyT, BaseModelT]
            The database to persist the data to.
        persistance_db_key: str | t.Callable[[BaseModelT], _KeyT]
            The key that acts as a primary key in the db.
        """
        super().__init__(*data, root=root, **kwargs)
        self.__persistence_db_overwrite = persistence_db_overwrite
        self.__persistence_db = persistence_db
        self.__persistence_db_key = persistance_db_key

    def __getitem__(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, index: int | slice
    ) -> BaseModelT | "BaseCollectionModel[BaseModelT]":
        """Get item at index."""
        return super().__getitem__(index)

    def __delitem__(self, index: t.Union[int, slice]) -> None:
        """Delete item at index."""
        super().__delitem__(index)

    def __setitem__(
        self, index: int | slice, value: BaseModelT | t.Iterable[BaseModelT]
    ) -> None:
        """Set item at index."""
        super().__setitem__(index, value)  # type: ignore

    def insert(self, index: int, value: BaseModelT) -> None:
        """Insert value before index."""
        super().insert(index, value)

    def sort(self, key: _SortedKey[BaseModelT], reverse: bool = False) -> None:
        """Sort the sequence in place."""
        return super().sort(key, reverse)

    def commit(self) -> None:
        """Commit changes to persistence database."""
        self.__persistence_db.commit()
