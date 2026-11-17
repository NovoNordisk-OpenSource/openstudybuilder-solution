"""Response models of the read-only ODM XML parse endpoint.

The parsed elements come from an uploaded file and are never stored, so they have no
database uid, versioning or audit trail. Where a database-backed model (``OdmForm``,
``OdmItemGroup``, ``OdmItem``) can only be built from persisted aggregates, a file
counterpart with the same field names is defined here. Sub-models that can be built
without the database (aliases, translated texts, vendor relations, term and unit
relations, item/item group references) are reused as they are.

Identifier conventions:
- ``uid`` of forms, item groups and items is the ODM ``OID`` of the definition.
- ``version`` is always ``"file"`` and ``status`` is always ``"File"``.
- Vendor ``uid`` values are derived from the namespace prefix and local name
  (``prefix:Name``).
"""

from typing import Annotated

from pydantic import Field

from clinical_mdr_api.models.concepts.activities.activity_item import CompactCTTerm
from clinical_mdr_api.models.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesSimpleModel,
)
from clinical_mdr_api.models.odms.common_models import (
    OdmAliasModel,
    OdmTranslatedTextModel,
)
from clinical_mdr_api.models.odms.item import (
    OdmItemExternalQuestion,
    OdmItemRefModel,
    OdmItemTermRelationshipModel,
    OdmItemUnitDefinitionWithRelationship,
)
from clinical_mdr_api.models.odms.item_group import OdmItemGroupRefModel
from clinical_mdr_api.models.odms.vendor_attribute import (
    OdmVendorAttributeRelationModel,
    OdmVendorElementAttributeRelationModel,
)
from clinical_mdr_api.models.odms.vendor_element import OdmVendorElementRelationModel
from clinical_mdr_api.models.utils import BaseModel

FILE_VERSION = "file"
FILE_STATUS = "File"
FILE_LIBRARY_NAME = "File"


class OdmXmlSdtmDomain(BaseModel):
    term_uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    submission_value: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class OdmXmlCodelist(CTCodelistAttributesSimpleModel):
    allows_multi_choice: Annotated[bool, Field()] = False


class OdmXmlElement(BaseModel):
    """Fields shared by all parsed ODM definitions."""

    uid: Annotated[str, Field(description="The OID of the definition.")]
    oid: Annotated[str, Field()]
    name: Annotated[str, Field()]
    library_name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        FILE_LIBRARY_NAME
    )
    status: Annotated[str, Field()] = FILE_STATUS
    version: Annotated[str, Field()] = FILE_VERSION
    translated_texts: Annotated[list[OdmTranslatedTextModel], Field()]
    aliases: Annotated[list[OdmAliasModel], Field()]
    vendor_elements: Annotated[list[OdmVendorElementRelationModel], Field()]
    vendor_attributes: Annotated[list[OdmVendorAttributeRelationModel], Field()]
    vendor_element_attributes: Annotated[
        list[OdmVendorElementAttributeRelationModel], Field()
    ]


class OdmXmlForm(OdmXmlElement):
    repeating: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    sdtm_version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )


class OdmXmlItemGroup(OdmXmlElement):
    repeating: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    is_reference_data: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    sas_dataset_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    origin: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    purpose: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    comment: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    sdtm_domains: Annotated[list[OdmXmlSdtmDomain], Field()]


class OdmXmlItem(OdmXmlElement):
    prompt: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    datatype: Annotated[
        CompactCTTerm | None, Field(json_schema_extra={"nullable": True})
    ] = None
    length: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    significant_digits: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = None
    sas_field_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    sds_var_name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    origin: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    comment: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    unit_definitions: Annotated[list[OdmItemUnitDefinitionWithRelationship], Field()]
    external_question: Annotated[
        OdmItemExternalQuestion | None, Field(json_schema_extra={"nullable": True})
    ] = None
    codelist: Annotated[
        OdmXmlCodelist | None, Field(json_schema_extra={"nullable": True})
    ] = None
    terms: Annotated[list[OdmItemTermRelationshipModel], Field()]
    activity_instances: Annotated[list[dict[str, str]], Field()]


class OdmXmlItemEntry(BaseModel):
    ref: Annotated[OdmItemRefModel, Field(description="ItemRef of the item group.")]
    item: Annotated[OdmXmlItem, Field()]


class OdmXmlItemGroupEntry(BaseModel):
    ref: Annotated[OdmItemGroupRefModel, Field(description="ItemGroupRef of the form.")]
    group: Annotated[OdmXmlItemGroup, Field()]
    items: Annotated[list[OdmXmlItemEntry], Field()]


class OdmXmlFormEntry(BaseModel):
    form: Annotated[OdmXmlForm, Field()]
    groups: Annotated[list[OdmXmlItemGroupEntry], Field()]


class OdmXmlParseResponse(BaseModel):
    forms: Annotated[list[OdmXmlFormEntry], Field()]
