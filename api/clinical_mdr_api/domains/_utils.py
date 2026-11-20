from typing import Literal, cast, overload

from clinical_mdr_api.domains.iso_languages import LANGUAGES_INDEXED_BY
from clinical_mdr_api.domains.libraries.parameter_term import ParameterTermEntryVO
from clinical_mdr_api.domains.odms.utils import EN_LANGUAGE, ENG_LANGUAGE
from common import exceptions


@overload
def get_iso_lang_data(
    query: str,
    return_key: None = None,
    ignore_case: bool = True,
) -> str | list[str] | dict[str, str]: ...
@overload
def get_iso_lang_data(
    query: str,
    return_key: Literal["names"],
    ignore_case: bool = True,
) -> list[str]: ...
@overload
def get_iso_lang_data(
    query: str,
    return_key: Literal["639-3"],
    ignore_case: bool = True,
) -> dict[str, str]: ...
@overload
def get_iso_lang_data(
    query: str,
    return_key: Literal["639-1", "639-2/T", "639-2/B"],
    ignore_case: bool = True,
) -> str: ...
def get_iso_lang_data(
    query: str,
    return_key: Literal["names", "639-1", "639-2/T", "639-2/B", "639-3"] | None = None,
    ignore_case: bool = True,
) -> str | list[str] | dict[str, str]:
    """
    Returns ISO language data based on the provided query string and return_key.

    Args:
        query (str): The language identifier to search for (e.g., code or name).
        return_key (Literal["names", "639-1", "639-2/T", "639-2/B", "639-3"] | None, optional):
            Specifies which field to return from the matched language entry.
            - If None, returns the value for the matched key.
            - If "names", returns a list of language names.
            - If "639-3", returns a dictionary mapping 639-3 codes to names.
            - If "639-1", "639-2/T", or "639-2/B", returns the corresponding code as a string.
        ignore_case (bool, optional): Whether to ignore case when searching for the query string. Defaults to True.

    Returns: str | list[str] | dict[str, str]: The requested language data, depending on return_key.

    Raises:
        TypeError: If the query is not a string.
        ValidationException: If the query is not found or does not match when ignore_case is False.

    Examples:
        >>> get_iso_lang_data("spa", "names")
        ["Spanish", "Castilian"]
        >>> get_iso_lang_data("spa", "639-1")
        'es'
    """
    if not isinstance(query, str):
        raise TypeError(f"Expected type str but found {type(query)}")

    keys = LANGUAGES_INDEXED_BY.keys()

    if return_key is not None and return_key not in keys:
        raise KeyError(f"Return key '{return_key}' is not a valid language key.")

    lang = None
    key = ""
    for key in keys:
        index = LANGUAGES_INDEXED_BY[key]

        casefolded_query = query.casefold()

        try:
            lang = index[casefolded_query]
            break
        except KeyError:
            continue

    if lang is None or (not ignore_case and lang[key] != query):
        raise exceptions.ValidationException(
            msg=f"The provided language '{query}' does not match any known language names or codes.",
        )

    return lang[key] if not return_key else lang[return_key]


def get_iso_lang_value(query: str) -> str:
    """
    Returns the language value matching `query` as a string.

    `get_iso_lang_data` without `return_key` is annotated as a union; callers that
    pass the value on as a plain string (e.g. `xml:lang`) use this typed wrapper.
    """
    return cast(str, get_iso_lang_data(query=query))


def is_language_english(lang: str) -> bool:
    return lang.casefold() in [EN_LANGUAGE, ENG_LANGUAGE]


def capitalize_first_letter_if_template_parameter(
    name: str,
    template_plain_name: str,
    parameters: list[ParameterTermEntryVO] | None = None,
) -> str:
    """
    Capitalizes the first letter of `name` if the letter is part of a template parameter which is not a Unit Definition.

    Args:
        name (str): The input string that may have its first letter capitalized.
        template_plain_name (str): The plain name of the template used to determine if capitalization is needed.

    Returns:
        str: `name` with the first letter capitalized if the letter is part of a template parameter which is not a Unit Definition.
        Otherwise, it returns `name` without any changes.
    """
    if (
        template_plain_name.startswith("[")
        and parameters
        and "UnitDefinitionRoot" not in parameters[0].parameters[0].labels
    ):
        idx = name.find("[")
        first_letter = idx + 1
        second_letter = idx + 2

        return (
            name[:first_letter]
            + name[first_letter:second_letter].upper()
            + name[second_letter:]
        )
    return name
