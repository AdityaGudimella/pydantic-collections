"""MutableMapping implementation."""
import typing as t
from collections import abc as cabc
from typing import Hashable

from pydantic import RootModel

from pydantic_collections.api import BaseModelT
from pydantic_collections.core import BaseCollectionModel


class PydanticMapping(
    BaseCollectionModel[BaseModelT],
    RootModel[dict[str, BaseModelT]],
    cabc.MutableMapping[str, BaseModelT],
):
    """A MutableMapping of PydanticModels."""

    def __init__(
        self,
        root: t.Mapping[str, BaseModelT] | None = None,
        **data: BaseModelT,
    ) -> None:
        """Initialize PydanticMapping.

        Note:
        ----
            A separate initializer is provided for the following reasons:
            - Make root argument optional.
            - Make root argument positional or keyword.
            - Provide **data argument
        """
        if root is None:
            root = {}
        root = root | data
        super().__init__(root=root)

    def __getitem__(self, __key: str) -> BaseModelT:
        return self.root[__key]

    def __setitem__(self, __key: str, __value: BaseModelT) -> None:
        self.root[__key] = self._validate_element(__value, (str(__key),))

    def __delitem__(self, __key: Hashable) -> None:
        del self.root[__key]

    def __iter__(self) -> t.Iterator[Hashable]:  # type: ignore
        return iter(self.root)

    def __len__(self) -> int:
        return len(self.root)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.root!r})"

    def __str__(self) -> str:
        return repr(self)
