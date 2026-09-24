"""Proxy types to make mypy happy..."""

import datetime
from typing import TYPE_CHECKING

import neomodel

if TYPE_CHECKING:
    from typing import Any, Generic, TypeVar, overload

    T = TypeVar("T")

    class _Property(Generic[T]):
        @overload
        def __get__(self, obj: None, objtype: type) -> "_Property[T]": ...
        @overload
        def __get__(self, obj: Any, objtype: type) -> T: ...
        def __get__(self, obj: Any, objtype: type) -> Any: ...
        def __set__(self, obj: Any, value: T) -> None: ...
        def __init__(
            self, *args: Any, **kwargs: Any  # pylint: disable=unused-argument
        ) -> None: ...

    class StringProperty(_Property[str]): ...

    class IntegerProperty(_Property[int]): ...

    class BooleanProperty(_Property[bool]): ...

    class FloatProperty(_Property[float]): ...

    class DateProperty(_Property[datetime.date]): ...

    class DateTimeProperty(_Property[datetime.datetime]): ...

    class ArrayProperty(_Property[list[Any]]): ...

else:
    StringProperty = neomodel.StringProperty
    IntegerProperty = neomodel.IntegerProperty
    BooleanProperty = neomodel.BooleanProperty
    FloatProperty = neomodel.FloatProperty
    DateProperty = neomodel.DateProperty
    DateTimeProperty = neomodel.DateTimeProperty
    ArrayProperty = neomodel.ArrayProperty
