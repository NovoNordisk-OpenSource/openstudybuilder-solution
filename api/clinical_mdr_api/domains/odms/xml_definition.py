"""
This file contains classes for all elements and attributes that can be used for generating ODM-XML.

There are some conventions to note:
- Classes defined here are subject to be converted to either an XML Element or an XML Attribute.
- If a class contains a property called `_custom_element_name` of type `str` then the name of
  the XML Element, generated based on this class, will be as specified in `_custom_element_name`.
- Properties of type `Attribute` of all classes are considered to be XML attributes for the class these properties are present in.
- Properties of type `str` of all classes, except `Attribute` class,
  are considered to be inner text of the XML Element, generated based on these classes.
  For the sake of consistency, name such properties `_string`.

E.g. given the following class:
class TranslatedText:
    _custom_element_name: str
    _string: str
    lang: Attribute

When we instantiate it:
TranslatedText("_custom_element_name":"Translation", "_string": "This is inner text", "lang": Attribute("lang", "en"))
the following will be produced:
<Translation lang="en">This is inner text</Translation>
"""

from dataclasses import dataclass
from datetime import datetime


class Element:
    _custom_element_name: str

    def __init__(self, _custom_element_name, **kwargs):
        self._custom_element_name = _custom_element_name

        for key, val in kwargs.items():
            setattr(self, key, val)


@dataclass
class Attribute:
    name: str
    value: str | int | datetime | None


class TranslatedText:
    _string: str
    lang: Attribute

    def __init__(self, _string: str, lang: Attribute, **kwargs):
        self._string = _string
        self.lang = lang

        for key, val in kwargs.items():
            setattr(self, key, val)


@dataclass
class Decode:
    translated_text: TranslatedText


class CodeListItem:
    coded_value: Attribute
    decode: Decode

    def __init__(self, coded_value: Attribute, decode: Decode, **kwargs):
        self.coded_value = coded_value
        self.decode = decode

        for key, val in kwargs.items():
            setattr(self, key, val)


@dataclass
class CodeList:
    oid: Attribute
    name: Attribute
    datatype: Attribute
    sas_format_name: Attribute
    codelist_items: list[CodeListItem]

    def __init__(
        self,
        oid: Attribute,
        name: Attribute,
        datatype: Attribute,
        sas_format_name: Attribute,
        codelist_items: list[CodeListItem],
        **kwargs,
    ):
        self.oid = oid
        self.name = name
        self.datatype = datatype
        self.sas_format_name = sas_format_name
        self.codelist_items = codelist_items

        for key, val in kwargs.items():
            setattr(self, key, val)


class Alias:
    name: Attribute
    context: Attribute

    def __init__(self, name: Attribute, context: Attribute, **kwargs):
        self.name = name
        self.context = context

        for key, val in kwargs.items():
            setattr(self, key, val)


@dataclass
class Description:
    translated_text: list[TranslatedText]


@dataclass
class Question:
    translated_text: list[TranslatedText]


@dataclass
class ExternalQuestion:
    dictionary: Attribute
    code: Attribute
    version: Attribute

    def __init__(
        self, dictionary: Attribute, code: Attribute, version: Attribute, **kwargs
    ):
        self.dictionary = dictionary
        self.code = code
        self.version = version

        for key, val in kwargs.items():
            setattr(self, key, val)


@dataclass
class OsbDesignNotes:
    translated_text: list[TranslatedText]
    _custom_element_name = "osb:DesignNotes"


@dataclass
class OsbCompletionInstructions:
    translated_text: list[TranslatedText]
    _custom_element_name = "osb:CompletionInstructions"


@dataclass
class OsbDisplayText:
    translated_text: list[TranslatedText]
    _custom_element_name = "osb:DisplayText"


@dataclass
class CodeListRef:
    codelist_oid: Attribute

    def __init__(self, codelist_oid: Attribute, **kwargs):
        self.codelist_oid = codelist_oid

        for key, val in kwargs.items():
            setattr(self, key, val)


@dataclass
class MeasurementUnitRef:
    measurement_unit_oid: Attribute


class FormalExpression:
    _string: str
    context: Attribute

    def __init__(self, _string: str, context: Attribute, **kwargs):
        self._string = _string
        self.context = context

        for key, val in kwargs.items():
            setattr(self, key, val)


class ConditionDef:
    oid: Attribute
    name: Attribute
    description: Description
    osb_design_notes: OsbDesignNotes | None
    osb_completion_instructions: OsbCompletionInstructions | None
    osb_display_text: OsbDisplayText | None
    aliases: list[Alias]
    formal_expressions: list[FormalExpression]

    def __init__(
        self,
        oid: Attribute,
        name: Attribute,
        description: Description,
        osb_design_notes: OsbDesignNotes | None,
        osb_completion_instructions: OsbCompletionInstructions | None,
        osb_display_text: OsbDisplayText | None,
        aliases: list[Alias],
        formal_expressions: list[FormalExpression],
        **kwargs,
    ):
        self.oid = oid
        self.name = name
        self.description = description
        self.osb_design_notes = osb_design_notes
        self.osb_completion_instructions = osb_completion_instructions
        self.osb_display_text = osb_display_text
        self.aliases = aliases
        self.formal_expressions = formal_expressions

        if not self.description.translated_text:
            del self.description
        if not self.osb_design_notes or not self.osb_design_notes.translated_text:
            del self.osb_design_notes
        if (
            not self.osb_completion_instructions
            or not self.osb_completion_instructions.translated_text
        ):
            del self.osb_completion_instructions
        if not self.osb_display_text or not self.osb_display_text.translated_text:
            del self.osb_display_text

        for key, val in kwargs.items():
            setattr(self, key, val)


class MethodDef:
    oid: Attribute
    name: Attribute
    type: Attribute
    description: Description
    osb_design_notes: OsbDesignNotes | None
    osb_completion_instructions: OsbCompletionInstructions | None
    osb_display_text: OsbDisplayText | None
    aliases: list[Alias]
    formal_expressions: list[FormalExpression]

    def __init__(
        self,
        oid: Attribute,
        name: Attribute,
        method_type: Attribute,
        description: Description,
        osb_design_notes: OsbDesignNotes | None,
        osb_completion_instructions: OsbCompletionInstructions | None,
        osb_display_text: OsbDisplayText | None,
        aliases: list[Alias],
        formal_expressions: list[FormalExpression],
        **kwargs,
    ):
        self.oid = oid
        self.name = name
        self.type = method_type
        self.description = description
        self.osb_design_notes = osb_design_notes
        self.osb_completion_instructions = osb_completion_instructions
        self.osb_display_text = osb_display_text
        self.aliases = aliases
        self.formal_expressions = formal_expressions

        if not self.description.translated_text:
            del self.description
        if not self.osb_design_notes or not self.osb_design_notes.translated_text:
            del self.osb_design_notes
        if (
            not self.osb_completion_instructions
            or not self.osb_completion_instructions.translated_text
        ):
            del self.osb_completion_instructions
        if not self.osb_display_text or not self.osb_display_text.translated_text:
            del self.osb_display_text

        for key, val in kwargs.items():
            setattr(self, key, val)


@dataclass
class OsbActivityInstance:
    _string: str
    adam_code: Attribute
    topic_code: Attribute
    activity_item_classes: Attribute
    is_derived: Attribute
    _custom_element_name: str = "osb:ActivityInstance"


class ItemDef:
    oid: Attribute
    name: Attribute
    origin: Attribute
    datatype: Attribute
    length: Attribute
    significant_digits: Attribute
    sas_field_name: Attribute
    sds_var_name: Attribute
    question: Question
    external_question: ExternalQuestion
    description: Description
    osb_design_notes: OsbDesignNotes | None
    osb_completion_instructions: OsbCompletionInstructions | None
    osb_display_text: OsbDisplayText | None
    aliases: list[Alias]
    activity_instances: list[OsbActivityInstance]
    codelist_ref: CodeListRef
    measurement_unit_refs: list[MeasurementUnitRef]

    def __init__(
        self,
        oid: Attribute,
        name: Attribute,
        origin: Attribute,
        datatype: Attribute,
        length: Attribute,
        significant_digits: Attribute,
        sas_field_name: Attribute,
        sds_var_name: Attribute,
        question: Question,
        external_question: ExternalQuestion,
        description: Description,
        osb_design_notes: OsbDesignNotes | None,
        osb_completion_instructions: OsbCompletionInstructions | None,
        osb_display_text: OsbDisplayText | None,
        aliases: list[Alias],
        activity_instances: list[OsbActivityInstance],
        codelist_ref: CodeListRef,
        measurement_unit_refs: list[MeasurementUnitRef],
        **kwargs,
    ):
        self.oid = oid
        self.name = name
        self.origin = origin
        self.datatype = datatype
        self.length = length
        self.significant_digits = significant_digits
        self.sas_field_name = sas_field_name
        self.sds_var_name = sds_var_name
        self.question = question
        self.external_question = external_question
        self.description = description
        self.osb_design_notes = osb_design_notes
        self.osb_completion_instructions = osb_completion_instructions
        self.osb_design_notes = osb_design_notes
        self.osb_display_text = osb_display_text
        self.aliases = aliases
        self.activity_instances = activity_instances
        self.codelist_ref = codelist_ref
        self.measurement_unit_refs = measurement_unit_refs

        if not self.codelist_ref.codelist_oid.value:
            del self.codelist_ref
        if not self.description.translated_text:
            del self.description
        if not self.question.translated_text:
            del self.question
        if (
            not self.external_question.dictionary.value
            or not self.external_question.code.value
        ):
            del self.external_question
        if not self.osb_design_notes or not self.osb_design_notes.translated_text:
            del self.osb_design_notes
        if (
            not self.osb_completion_instructions
            or not self.osb_completion_instructions.translated_text
        ):
            del self.osb_completion_instructions
        if not self.osb_display_text or not self.osb_display_text.translated_text:
            del self.osb_display_text

        for key, val in kwargs.items():
            setattr(self, key, val)


@dataclass
class ItemRef:
    item_oid: Attribute
    mandatory: Attribute
    order_number: Attribute
    method_oid: Attribute
    collection_exception_condition_oid: Attribute

    def __init__(
        self,
        item_oid: Attribute,
        mandatory: Attribute,
        order_number: Attribute,
        method_oid: Attribute,
        collection_exception_condition_oid: Attribute,
        **kwargs,
    ):
        self.item_oid = item_oid
        self.mandatory = mandatory
        self.order_number = order_number
        self.method_oid = method_oid
        self.collection_exception_condition_oid = collection_exception_condition_oid

        if not self.collection_exception_condition_oid.value:
            del self.collection_exception_condition_oid

        if not self.method_oid.value:
            del self.method_oid

        for key, val in kwargs.items():
            setattr(self, key, val)


@dataclass
class OsbDomainColor:
    _string: str
    _custom_element_name: str = "osb:DomainColor"


class ItemGroupDef:
    oid: Attribute
    name: Attribute
    repeating: Attribute
    purpose: Attribute
    sas_dataset_name: Attribute
    domain: Attribute
    osb_domain_colors: list[OsbDomainColor]
    description: Description
    osb_design_notes: OsbDesignNotes | None
    osb_completion_instructions: OsbCompletionInstructions | None
    osb_display_text: OsbDisplayText | None
    aliases: list[Alias]
    item_refs: list[ItemRef]

    def __init__(
        self,
        oid: Attribute,
        name: Attribute,
        repeating: Attribute,
        purpose: Attribute,
        sas_dataset_name: Attribute,
        domain: Attribute,
        osb_domain_colors: list[OsbDomainColor],
        description: Description,
        osb_design_notes: OsbDesignNotes | None,
        osb_completion_instructions: OsbCompletionInstructions | None,
        osb_display_text: OsbDisplayText | None,
        aliases: list[Alias],
        item_refs: list[ItemRef],
        **kwargs,
    ):
        self.oid = oid
        self.name = name
        self.repeating = repeating
        self.purpose = purpose
        self.sas_dataset_name = sas_dataset_name
        self.domain = domain
        self.osb_domain_colors = osb_domain_colors
        self.description = description
        self.osb_design_notes = osb_design_notes
        self.osb_completion_instructions = osb_completion_instructions
        self.osb_display_text = osb_display_text
        self.aliases = aliases
        self.item_refs = item_refs

        if not self.description.translated_text:
            del self.description
        if not self.osb_design_notes or not self.osb_design_notes.translated_text:
            del self.osb_design_notes
        if (
            not self.osb_completion_instructions
            or not self.osb_completion_instructions.translated_text
        ):
            del self.osb_completion_instructions
        if not self.osb_display_text or not self.osb_display_text.translated_text:
            del self.osb_display_text

        for key, val in kwargs.items():
            setattr(self, key, val)


class ItemGroupRef:
    item_group_oid: Attribute
    mandatory: Attribute
    order_number: Attribute
    collection_exception_condition_oid: Attribute

    def __init__(
        self,
        item_group_oid: Attribute,
        mandatory: Attribute,
        order_number: Attribute,
        collection_exception_condition_oid: Attribute,
        **kwargs,
    ):
        self.item_group_oid = item_group_oid
        self.mandatory = mandatory
        self.order_number = order_number
        self.collection_exception_condition_oid = collection_exception_condition_oid

        if not self.collection_exception_condition_oid.value:
            del self.collection_exception_condition_oid

        for key, val in kwargs.items():
            setattr(self, key, val)


class FormDef:
    oid: Attribute
    name: Attribute
    repeating: Attribute
    description: Description
    osb_design_notes: OsbDesignNotes | None
    osb_completion_instructions: OsbCompletionInstructions | None
    osb_display_text: OsbDisplayText | None
    aliases: list[Alias]
    item_group_refs: list[ItemGroupRef]

    def __init__(
        self,
        oid: Attribute,
        name: Attribute,
        repeating: Attribute,
        description: Description,
        osb_design_notes: OsbDesignNotes | None,
        osb_completion_instructions: OsbCompletionInstructions | None,
        osb_display_text: OsbDisplayText | None,
        aliases: list[Alias],
        item_group_refs: list[ItemGroupRef],
        **kwargs,
    ):
        self.oid = oid
        self.name = name
        self.repeating = repeating
        self.description = description
        self.osb_design_notes = osb_design_notes
        self.osb_completion_instructions = osb_completion_instructions
        self.osb_display_text = osb_display_text
        self.aliases = aliases
        self.item_group_refs = item_group_refs

        if not self.description.translated_text:
            del self.description
        if not self.osb_design_notes or not self.osb_design_notes.translated_text:
            del self.osb_design_notes
        if (
            not self.osb_completion_instructions
            or not self.osb_completion_instructions.translated_text
        ):
            del self.osb_completion_instructions
        if not self.osb_display_text or not self.osb_display_text.translated_text:
            del self.osb_display_text

        for key, val in kwargs.items():
            setattr(self, key, val)


@dataclass
class Symbol:
    translated_text: TranslatedText


@dataclass
class MeasurementUnit:
    oid: Attribute
    name: Attribute
    symbol: Symbol

    def __init__(self, oid: Attribute, name: Attribute, symbol: Symbol, **kwargs):
        self.oid = oid
        self.name = name
        self.symbol = symbol

        for key, val in kwargs.items():
            setattr(self, key, val)


@dataclass
class MetaDataVersion:
    oid: Attribute
    name: Attribute
    description: Attribute
    form_defs: list[FormDef]
    item_group_defs: list[ItemGroupDef]
    item_defs: list[ItemDef]
    condition_defs: list[ConditionDef]
    method_defs: list[MethodDef]
    codelists: list[CodeList]


@dataclass
class BasicDefinitions:
    measurement_units: list[MeasurementUnit]


@dataclass
class ProtocolName:
    _string: str


@dataclass
class StudyName:
    _string: str


@dataclass
class StudyDescription:
    _string: str


@dataclass
class GlobalVariables:
    protocol_name: ProtocolName
    study_name: StudyName
    study_description: StudyDescription


@dataclass
class Study:
    oid: Attribute
    global_variables: GlobalVariables
    basic_definitions: BasicDefinitions
    meta_data_version: MetaDataVersion


@dataclass
class ODM:
    odm_ns: Attribute
    odm_version: Attribute
    file_type: Attribute
    file_oid: Attribute
    creation_date_time: Attribute
    granularity: Attribute
    study: Study

    def __init__(
        self,
        odm_ns: Attribute,
        odm_version: Attribute,
        file_type: Attribute,
        file_oid: Attribute,
        creation_date_time: Attribute,
        granularity: Attribute,
        study: Study,
        **kwargs,
    ):
        self.odm_ns = odm_ns
        self.odm_version = odm_version
        self.file_type = file_type
        self.file_oid = file_oid
        self.creation_date_time = creation_date_time
        self.granularity = granularity
        self.study = study

        for key, val in kwargs.items():
            setattr(self, key, val)
