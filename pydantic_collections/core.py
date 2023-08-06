"""Core classes for pydantic collections."""
import types
import typing as t
from dataclasses import dataclass

import pydantic as pdt
import pydantic_core as pdc
from pydantic._internal._model_construction import ModelMetaclass

from pydantic_collections import external_utils as extu
from pydantic_collections.api import DataBase

UnionType = getattr(types, "UnionType", t.Union)


class CollectionModelConfig(pdt.ConfigDict):
    """Configuration options for collection models."""

    validate_assignment_strict: bool


_T = t.TypeVar("_T")


@dataclass
class Element(t.Generic[_T]):
    """A generic class representing an element in a collection."""

    annotation: t.Any
    adapter: pdt.TypeAdapter[_T]


_ModelMetaclassT = t.TypeVar("_ModelMetaclassT", bound=ModelMetaclass)


class BaseCollectionModelMeta(ModelMetaclass):
    """Base Metaclass for pydantic-collection models."""

    @extu.tp_cache
    def __getitem__(
        cls: _ModelMetaclassT, el_type: t.Any  # noqa: ANN401
    ) -> _ModelMetaclassT:
        """Return a new collection model class with the given element type.

        Args:
        ----
        cls: _ModelMetaclassT
            The collection model class to create a new subclass of.
        el_type: t.Any
            The type of the elements in the collection.

        Returns:
        -------
        _ModelMetaclassT
            A new collection model class with the given element type.
        """
        if not issubclass(cls, BaseCollectionModel):
            raise TypeError(
                "{!r} is not a BaseCollectionModel".format(cls)
            )  # pragma: no cover

        element = Element(annotation=el_type, adapter=pdt.TypeAdapter(el_type))
        return t.cast(
            _ModelMetaclassT,
            type(
                f"{cls.__name__}[{el_type}]",
                (cls,),
                {
                    "__element__": element,
                    "__annotations__": {"root": t.List[el_type]},
                },
            ),
        )


BaseModelT = t.TypeVar("BaseModelT", bound=pdt.BaseModel)


class BaseCollectionModel(
    pdt.RootModel[t.Any],
    t.Generic[BaseModelT],
    metaclass=BaseCollectionModelMeta,
):
    """Base class for all pydantic-collection collection models.

    Important:
    ---------
        Your subclass must subclass both this class and pydantic.RootModel class with
        the type parameter for the RootModel being a subclass of Collection[_BaseModelT]
    """

    if t.TYPE_CHECKING:  # pragma: no cover
        __element__: Element[BaseModelT]

    _DEFAULT_VALIDATE_ASSIGNMENT = True
    _DEFAULT_VALIDATE_ASSIGNMENT_STRICT = True

    model_config = CollectionModelConfig(
        extra="forbid",
        validate_assignment=_DEFAULT_VALIDATE_ASSIGNMENT,
        validate_assignment_strict=_DEFAULT_VALIDATE_ASSIGNMENT_STRICT,
    )

    def _validate_element_type(
        self,
        value: t.Any,  # noqa: ANN401
        loc: tuple[int | str, ...],
    ) -> None:
        types = extu.get_types_from_annotation(self.__element__.annotation)
        if not isinstance(value, tuple(types)):
            error = {
                "type": "is_instance_of",
                "loc": loc,
                "input": value,
                "ctx": {"class": str(self.__element__.annotation)},
            }
            raise pdt.ValidationError.from_exception_data(
                title=self.__class__.__name__,
                line_errors=[t.cast(pdc.InitErrorDetails, error)],
            )

    def _validate_element(
        self, value: t.Any, loc: tuple[int | str, ...]  # noqa: ANN401
    ) -> BaseModelT:  # noqa: ANN401
        if not self.model_config.get(
            "validate_assignment", self._DEFAULT_VALIDATE_ASSIGNMENT
        ):
            return value

        strict = False
        if self.model_config.get(
            "validate_assignment_strict", self._DEFAULT_VALIDATE_ASSIGNMENT_STRICT
        ):
            self._validate_element_type(value, loc)
            strict = True

        try:
            return self.__element__.adapter.validate_python(
                value,
                strict=strict,
                from_attributes=True,
            )
        except pdt.ValidationError as e:
            errors = extu.wrap_errors_with_loc(
                errors=e.errors(),
                loc_prefix=loc,
            )
            raise pdt.ValidationError.from_exception_data(
                title=self.__class__.__name__,
                line_errors=errors,
            ) from e


_KeyT = t.TypeVar("_KeyT")
_ValueT = t.TypeVar("_ValueT")


class NullDB(DataBase[_KeyT, _ValueT]):
    """A null database that does nothing."""

    def add(self, key: _KeyT, value: _ValueT) -> None:
        """Add data to the database."""

    def load(self) -> dict[_KeyT, _ValueT]:
        """Load data from the database."""
        return {}

    def delete(self, id: _KeyT) -> None:
        """Delete data from the database."""

    def commit(self) -> None:
        """Commit changes to the database."""
