"""The api followed by the pydantic-collections package."""
import abc
import typing as t

import pydantic as pdt
import typing_extensions as te

BaseModelT = t.TypeVar("BaseModelT", bound=pdt.BaseModel)
IncEx: t.TypeAlias = set[int] | set[str] | dict[int, t.Any] | dict[str, t.Any] | None


class PydanticCollection(abc.ABC):
    """A collection of pydantic models."""

    @classmethod
    @abc.abstractmethod
    def model_construct(
        cls: type[te.Self],
        _fields_set: set[str] | None = None,
        *values: dict[str, t.Any],
    ) -> te.Self:
        """Construct a PydanticCollection with validated data for each element."""
        raise NotImplementedError

    @abc.abstractmethod
    def model_copy(
        self: te.Self, *, update: dict[str, t.Any] | None = None, deep: bool = False
    ) -> te.Self:
        """Return a copy of the model."""
        raise NotImplementedError

    @abc.abstractmethod
    def model_dump(
        self,
        *,
        mode: t.Literal["json", "python"] | str = "python",
        include: IncEx = None,
        exclude: IncEx = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> list[dict[str, t.Any]]:
        """Generate a dictionary representation for each element of the model."""
        raise NotImplementedError

    @abc.abstractmethod
    def model_dump_json(
        self,
        *,
        indent: int | None = None,
        include: IncEx = None,
        exclude: IncEx = None,
        by_alias: bool = False,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        round_trip: bool = False,
        warnings: bool = True,
    ) -> str:
        """Generate a JSON representation of the model."""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def model_validate(
        cls: type[te.Self],
        obj: t.Any,  # noqa: ANN401
        *,
        strict: bool | None = None,
        from_attributes: bool | None = None,
        context: dict[str, t.Any] | None = None,
    ) -> te.Self:
        """Validate a pydantic model instance."""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def model_validate_json(
        cls: type[te.Self],
        json_data: str | bytes | bytearray,
        *,
        strict: bool | None = None,
        context: dict[str, t.Any] | None = None,
    ) -> te.Self:
        """Validate a pydantic model instance from JSON."""
        raise NotImplementedError


_KeyT = t.TypeVar("_KeyT")
_ValueT = t.TypeVar("_ValueT")


class DataBase(t.Protocol[_KeyT, _ValueT]):
    """A protocol for persisting data."""

    @property
    def __persisting_data__(self) -> dict[_KeyT, _ValueT]:
        """The data that will be persisted."""
        raise NotImplementedError

    def add(self, key: _KeyT, value: _ValueT) -> None:
        """Add data to the database."""
        raise NotImplementedError

    def load(self) -> dict[_KeyT, _ValueT]:
        """Load data from the database."""
        raise NotImplementedError

    def delete(self, id: _KeyT) -> None:
        """Delete data from the database."""
        raise NotImplementedError

    def commit(self) -> None:
        """Commit changes to the database."""
        raise NotImplementedError
