"""Pure helpers for reading ODM XML elements, shared by the ODM XML importers and the
read-only ``OdmXmlParserService``. Nothing here touches the database."""

from xml.dom import minidom

from clinical_mdr_api.domains._utils import get_iso_lang_data
from clinical_mdr_api.domains.enums import OdmTranslatedTextTypeEnum
from clinical_mdr_api.domains.odms.utils import EN_LANGUAGE
from clinical_mdr_api.models.odms.common_models import (
    OdmAliasModel,
    OdmTranslatedTextModel,
)
from common.exceptions import BusinessLogicException

# OSB extensions that are mapped to dedicated fields and are therefore not
# treated as vendor extensions of the element.
EXCLUDED_OSB_VENDOR_ATTRIBUTES: tuple[str, ...] = (
    "version",
    "lang",
    "allowsMultiChoice",
)
EXCLUDED_OSB_VENDOR_ELEMENTS: tuple[str, ...] = (
    "DomainColor",
    "DisplayText",
    "DesignNotes",
    "CompletionInstructions",
)


def get_element_text(element: minidom.Element) -> str:
    return str(element.firstChild.nodeValue) if element.firstChild else ""


def read_translated_texts(element: minidom.Element) -> list[OdmTranslatedTextModel]:
    translated_texts: list[OdmTranslatedTextModel] = []

    for translated_text_type in OdmTranslatedTextTypeEnum:
        parents = element.getElementsByTagName(translated_text_type.value)
        if not parents:
            continue

        for translated_text in parents[0].getElementsByTagName("TranslatedText"):
            translated_texts.append(
                OdmTranslatedTextModel(
                    text_type=translated_text_type,
                    language=get_iso_lang_data(  # type: ignore[arg-type]
                        translated_text.getAttribute("xml:lang") or EN_LANGUAGE
                    ),
                    text=get_element_text(translated_text) or "TBD",
                )
            )

    return translated_texts


def read_aliases(element: minidom.Element) -> list[OdmAliasModel]:
    return [
        OdmAliasModel(
            name=alias.getAttribute("Name"), context=alias.getAttribute("Context")
        )
        for alias in element.getElementsByTagName("Alias")
    ]


def read_sdtm_domains(group_def: minidom.Element) -> list[tuple[str, str]]:
    """Returns (submission_value, name) pairs from the ``Domain`` attribute.

    A domain is either ``submission_value:name`` or a single value that may be
    either the submission value or the name.
    """
    domains: list[tuple[str, str]] = []
    for domain in group_def.getAttribute("Domain").split("|"):
        if not domain:
            continue
        if ":" in domain:
            submission_value, name = domain.split(":", 1)
        else:
            submission_value, name = domain, domain
        domains.append((submission_value, name))
    return domains


def read_codelist_description(codelist_def: minidom.Element) -> str:
    descriptions = codelist_def.getElementsByTagName("Description")
    texts = (
        descriptions[0].getElementsByTagName("TranslatedText") if descriptions else []
    )
    BusinessLogicException.raise_if(
        not texts or not texts[0].firstChild,
        msg=(
            "Code Submission Value not provided for Codelist with OID "
            f"'{codelist_def.getAttribute('OID')}'. Provide a Description with "
            "TranslatedText element for the CodeList."
        ),
    )
    return get_element_text(texts[0])
