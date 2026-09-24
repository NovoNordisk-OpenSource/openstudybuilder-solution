from dataclasses import dataclass
from typing import Callable, Self

from common.exceptions import ValidationException


@dataclass(frozen=True)
class ParameterTermVO:
    uid: str


@dataclass(frozen=True)
class SimpleParameterTermVO(ParameterTermVO):
    """
    Value object representing single parameter term - a pair of (name, uid)
    """

    value: str | float
    labels: list[str] | None = None

    @classmethod
    def from_repository_values(
        cls, *, uid: str, value: str, labels: list[str] | None = None
    ) -> Self:
        if labels is None:
            labels = []
        return cls(uid=uid, value=value, labels=labels)

    @classmethod
    def from_input_values(
        cls,
        *,
        uid: str,
        parameter_term_by_uid_lookup_callback: Callable[
            [str], tuple[str, list[str]]
        ] = lambda _: ("", []),
        value: str | None = None,
    ) -> Self:
        labels = None

        if value is None:
            ValidationException.raise_if(
                parameter_term_by_uid_lookup_callback is None,
                msg="parameter_term_by_uid_lookup_callback is required when value is None",
            )
            value, labels = parameter_term_by_uid_lookup_callback(uid)
            ValidationException.raise_if(
                value is None,
                msg="One or more of the specified template parameters can not be found.",
            )
        return cls(uid=uid, value=value, labels=labels)


@dataclass(frozen=True)
class NumericParameterTermVO(SimpleParameterTermVO):
    value: float

    @classmethod
    def from_input_values(cls, *, uid: str, value: float) -> Self:
        return cls(uid=uid, value=value)


@dataclass(frozen=True)
class ParameterTermEntryVO:
    """
    Value Object representing a set of single parameter terms entered into template
    placeholder. Contains parameter name, a conjunction  and list of parameter
    values to be combined into resulting name.
    """

    parameters: list[ParameterTermVO] | list[SimpleParameterTermVO]
    conjunction: str
    parameter_name: str
    labels: list[str]

    @classmethod
    def from_repository_values(
        cls,
        *,
        parameter_name: str,
        parameters: list[ParameterTermVO],
        conjunction: str,
        labels: list[str],
    ) -> Self:
        return cls(
            parameter_name=parameter_name,
            parameters=parameters,
            conjunction=conjunction,
            labels=labels,
        )

    @classmethod
    def from_input_values(
        cls,
        *,
        parameter_name: str,
        parameters: list[ParameterTermVO] | list[SimpleParameterTermVO],
        conjunction: str,
        labels: list[str],
        parameter_exists_callback: Callable[[str], bool],
        parameter_term_uid_exists_for_parameter_callback: Callable[
            [str, str, str], bool
        ],
        conjunction_exists_callback: Callable[[str], bool],
    ) -> Self:
        ValidationException.raise_if_not(
            parameter_exists_callback(parameter_name),
            msg=f"Unknown parameter name: {parameter_name}",
        )

        for parameter_term in parameters:
            ValidationException.raise_if_not(
                parameter_term_uid_exists_for_parameter_callback(
                    parameter_name, parameter_term.uid, parameter_term.value
                ),
                msg=f"Parameter term {parameter_term.uid} ('{parameter_term.value}') not valid for parameter '{parameter_name}'",
            )

        ValidationException.raise_if_not(
            conjunction_exists_callback(conjunction),
            msg=f"Unknown conjunction: {conjunction}",
        )

        return cls(
            parameter_name=parameter_name,
            conjunction=conjunction,
            parameters=parameters,
            labels=labels,
        )
