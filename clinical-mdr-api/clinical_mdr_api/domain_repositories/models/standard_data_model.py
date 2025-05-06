from neomodel import (
    ArrayProperty,
    BooleanProperty,
    IntegerProperty,
    One,
    OneOrMore,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    StructuredRel,
    ZeroOrOne,
)

from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCodelistRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    ClinicalMdrRel,
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)


class DataModelCatalogue(ClinicalMdrNode):
    has_library = RelationshipFrom(Library, "CONTAINS_CATALOGUE", model=ClinicalMdrRel)
    name = StringProperty()
    data_model_type = StringProperty()


class DataModelIGValue(VersionValue):
    name = StringProperty()
    description = StringProperty()
    version_number = StringProperty()
    implements = RelationshipTo(
        "DataModelValue", "IMPLEMENTS", model=ClinicalMdrRel, cardinality=One
    )

    extended_by = RelationshipFrom(
        "SponsorModelValue", "EXTENDS_VERSION", model=ClinicalMdrRel
    )


class SponsorModelValue(VersionValue):
    name = StringProperty()
    extends_version = RelationshipTo(
        DataModelIGValue, "EXTENDS_VERSION", model=ClinicalMdrRel, cardinality=One
    )
    has_sponsor_model_version = RelationshipFrom(
        "DataModelIGRoot", "HAS_VERSION", model=VersionRelationship
    )


class DataModelIGRoot(VersionRoot):
    has_library = RelationshipFrom(
        Library, "CONTAINS_DATA_MODEL_IG", model=ClinicalMdrRel
    )
    has_version = RelationshipTo(
        DataModelIGValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(DataModelIGValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(
        DataModelIGValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        DataModelIGValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        DataModelIGValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )

    has_sponsor_model_version = RelationshipTo(
        SponsorModelValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_sponsor_model_value = RelationshipTo(
        SponsorModelValue, "LATEST", model=ClinicalMdrRel
    )
    latest_sponsor_model_draft = RelationshipTo(
        SponsorModelValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_sponsor_model_final = RelationshipTo(
        SponsorModelValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_sponsor_model_retired = RelationshipTo(
        SponsorModelValue, "LATEST_RETIRED", model=VersionRelationship
    )


class DataModelValue(VersionValue):
    name = StringProperty()
    description = StringProperty()
    implements = RelationshipFrom(
        DataModelIGValue, "IMPLEMENTS", model=ClinicalMdrRel, cardinality=OneOrMore
    )


class DataModelRoot(VersionRoot):
    has_library = RelationshipFrom(Library, "CONTAINS_DATA_MODEL", model=ClinicalMdrRel)
    has_version = RelationshipTo(
        DataModelValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(DataModelValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(DataModelValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    latest_final = RelationshipTo(DataModelValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(
        DataModelValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
    has_data_model = RelationshipFrom(
        DataModelCatalogue, "HAS_DATA_MODEL", model=ClinicalMdrRel
    )


# pylint: disable=abstract-method
class CatalogueVerRel(ClinicalMdrRel):
    version_number = StringProperty()
    catalogue = StringProperty()


class HasDatasetClassRel(ClinicalMdrRel):
    ordinal = StringProperty()


class HasDatasetRel(HasDatasetClassRel):
    pass


class DatasetClassInstance(VersionValue):
    description = StringProperty()
    label = StringProperty()
    title = StringProperty()
    has_dataset_class = RelationshipFrom(
        DataModelValue, "HAS_DATASET_CLASS", model=HasDatasetClassRel, cardinality=One
    )
    has_parent_class = RelationshipTo(
        "DatasetClassInstance",
        "HAS_PARENT_CLASS",
        model=CatalogueVerRel,
        cardinality=ZeroOrOne,
    )
    is_instance_of = RelationshipFrom(
        "DatasetClass", "HAS_INSTANCE", model=ClinicalMdrRel
    )


class DatasetClass(VersionRoot):
    has_instance = RelationshipTo(
        DatasetClassInstance, "HAS_INSTANCE", model=ClinicalMdrRel
    )
    has_dataset_class = RelationshipFrom(
        DataModelCatalogue, "HAS_DATASET_CLASS", model=ClinicalMdrRel, cardinality=One
    )


class DatasetInstance(VersionValue):
    description = StringProperty()
    label = StringProperty()
    title = StringProperty()
    has_dataset = RelationshipFrom(
        DataModelIGValue, "HAS_DATASET", model=HasDatasetRel, cardinality=One
    )
    implements_dataset_class = RelationshipTo(
        DatasetClassInstance,
        "IMPLEMENTS_DATASET_CLASS",
        model=ClinicalMdrRel,
        cardinality=One,
    )


class HasKeyRel(StructuredRel):
    order = IntegerProperty()


class SponsorModelDatasetInstance(VersionValue):
    is_basic_std = BooleanProperty()
    xml_path = StringProperty()
    xml_title = StringProperty()
    structure = StringProperty()
    purpose = StringProperty()
    is_cdisc_std = BooleanProperty()
    source_ig = StringProperty()
    standard_ref = StringProperty()
    comment = StringProperty()
    ig_comment = StringProperty()
    map_domain_flag = BooleanProperty()
    suppl_qual_flag = BooleanProperty()
    include_in_raw = BooleanProperty()
    gen_raw_seqno_flag = BooleanProperty()
    label = StringProperty()
    state = StringProperty()
    extended_domain = StringProperty()

    is_instance_of = RelationshipFrom("Dataset", "HAS_INSTANCE", model=ClinicalMdrRel)
    has_dataset = RelationshipFrom(
        SponsorModelValue, "HAS_DATASET", model=HasDatasetRel
    )
    has_key = RelationshipTo(
        "DatasetVariable",
        "HAS_KEY",
        model=HasKeyRel,
        cardinality=OneOrMore,
    )
    has_sort_key = RelationshipTo(
        "DatasetVariable",
        "HAS_SORT_KEY",
        model=HasKeyRel,
        cardinality=OneOrMore,
    )
    implements_dataset_class = RelationshipTo(
        DatasetClassInstance,
        "IMPLEMENTS_DATASET_CLASS",
        model=ClinicalMdrRel,
        cardinality=One,
    )


class Dataset(VersionRoot):
    has_instance = RelationshipTo(DatasetInstance, "HAS_INSTANCE", model=ClinicalMdrRel)
    has_dataset = RelationshipFrom(
        DataModelCatalogue, "HAS_DATASET", model=ClinicalMdrRel, cardinality=One
    )

    has_sponsor_model_instance = RelationshipTo(
        SponsorModelDatasetInstance, "HAS_INSTANCE", model=ClinicalMdrRel
    )


class DatasetScenarioInstance(VersionValue):
    label = StringProperty()


class DatasetScenario(VersionRoot):
    has_version = RelationshipTo(
        DatasetScenarioInstance, "HAS_INSTANCE", model=ClinicalMdrRel
    )
    has_dataset_scenario = RelationshipFrom(
        DataModelCatalogue,
        "HAS_DATASET_SCENARIO",
        model=ClinicalMdrRel,
        cardinality=One,
    )


# pylint: disable=abstract-method
class HasVariableClassRel(ClinicalMdrRel):
    ordinal = StringProperty()
    version_number = StringProperty()


# pylint: disable=abstract-method
class HasMappingTargetRel(ClinicalMdrRel):
    version_number = StringProperty()


class VariableClassInstance(VersionValue):
    description = StringProperty()
    implementation_notes = StringProperty()
    title = StringProperty()
    label = StringProperty()
    core = StringProperty()
    completion_instructions = StringProperty()
    mapping_instructions = StringProperty()
    prompt = StringProperty()
    question_text = StringProperty()
    simple_datatype = StringProperty()
    role = StringProperty()
    described_value_domain = StringProperty()
    notes = StringProperty()
    usage_restrictions = StringProperty()
    examples = StringProperty()
    is_instance_of = RelationshipFrom(
        "VariableClass", "HAS_INSTANCE", model=ClinicalMdrRel
    )
    has_variable_class = RelationshipFrom(
        DatasetClassInstance,
        "HAS_VARIABLE_CLASS",
        model=HasVariableClassRel,
        cardinality=One,
    )
    implements_variable = RelationshipFrom(
        "DatasetVariableInstance",
        "IMPLEMENTS_VARIABLE",
        model=ClinicalMdrRel,
        cardinality=One,
    )
    has_version = RelationshipFrom(
        "VariableClass", "HAS_VERSION", model=VersionRelationship
    )
    references_codelist = RelationshipTo(
        CTCodelistRoot, "REFERENCES_CODELIST", model=ClinicalMdrRel
    )
    qualifies_variable = RelationshipTo(
        "VariableClassInstance", "QUALIFIES_VARIABLE", model=ClinicalMdrRel
    )
    has_mapping_target = RelationshipTo(
        "VariableClassInstance",
        "HAS_MAPPING_TARGET",
        model=HasMappingTargetRel,
        cardinality=ZeroOrOne,
    )


class VariableClass(VersionRoot):
    has_instance = RelationshipTo(
        VariableClassInstance, "HAS_INSTANCE", model=ClinicalMdrRel
    )

    has_variable_class = RelationshipFrom(
        DataModelCatalogue,
        "HAS_VARIABLE_CLASS",
        model=HasVariableClassRel,
        cardinality=One,
    )


# pylint: disable=abstract-method
class HasDatasetVariableRel(HasVariableClassRel):
    pass


class DatasetVariableInstance(VersionValue):
    description = StringProperty()
    title = StringProperty()
    label = StringProperty()
    simple_datatype = StringProperty()
    role = StringProperty()
    core = StringProperty()
    question_text = StringProperty()
    prompt = StringProperty()
    completion_instructions = StringProperty()
    implementation_notes = StringProperty()
    mapping_instructions = StringProperty()
    described_value_domain = StringProperty()
    value_list = ArrayProperty()
    has_dataset_variable = RelationshipFrom(
        DatasetInstance,
        "HAS_DATASET_VARIABLE",
        model=HasDatasetVariableRel,
        cardinality=One,
    )
    implements_variable = RelationshipTo(
        VariableClassInstance,
        "IMPLEMENTS_VARIABLE",
        model=CatalogueVerRel,
        cardinality=One,
    )
    has_mapping_target = RelationshipTo(
        "DatasetVariableInstance",
        "HAS_MAPPING_TARGET",
        model=HasMappingTargetRel,
        cardinality=ZeroOrOne,
    )
    has_version = RelationshipFrom(
        "DatasetVariable", "HAS_VERSION", model=VersionRelationship
    )
    references_codelist = RelationshipTo(
        CTCodelistRoot, "REFERENCES_CODELIST", model=ClinicalMdrRel
    )


class SponsorModelDatasetVariableInstance(VersionValue):
    is_basic_std = BooleanProperty()
    label = StringProperty()
    variable_type = StringProperty()
    length = IntegerProperty()
    display_format = StringProperty()
    xml_datatype = StringProperty()
    xml_codelist = StringProperty()
    xml_codelist_multi = ArrayProperty()
    core = StringProperty()
    origin = StringProperty()
    origin_type = StringProperty()
    origin_source = StringProperty()
    role = StringProperty()
    term = StringProperty()
    algorithm = StringProperty()
    qualifiers = ArrayProperty()
    is_cdisc_std = BooleanProperty()
    comment = StringProperty()
    ig_comment = StringProperty()
    class_table = StringProperty()
    class_column = StringProperty()
    map_var_flag = StringProperty()
    fixed_mapping = StringProperty()
    include_in_raw = BooleanProperty()
    nn_internal = BooleanProperty()
    value_lvl_where_cols = StringProperty()
    value_lvl_label_col = StringProperty()
    value_lvl_collect_ct_val = StringProperty()
    value_lvl_ct_codelist_id_col = StringProperty()
    enrich_build_order = IntegerProperty()
    enrich_rule = StringProperty()
    xml_codelist_values = BooleanProperty()

    implemented_variable_class_inconsistency = BooleanProperty()
    implemented_variable_class_uid = StringProperty()
    implemented_parent_dataset_class_uid = StringProperty()

    has_variable = RelationshipFrom(
        SponsorModelDatasetInstance, "HAS_DATASET_VARIABLE", model=HasDatasetVariableRel
    )
    implements_variable_class = RelationshipTo(
        VariableClassInstance,
        "IMPLEMENTS_VARIABLE_CLASS",
        model=ClinicalMdrRel,
        cardinality=One,
    )

    is_instance_of = RelationshipFrom(
        "DatasetVariable", "HAS_INSTANCE", model=ClinicalMdrRel
    )


class DatasetVariable(VersionRoot):
    has_instance = RelationshipTo(
        DatasetVariableInstance, "HAS_INSTANCE", model=ClinicalMdrRel
    )
    has_dataset_variable = RelationshipFrom(
        DataModelCatalogue,
        "HAS_DATASET_VARIABLE",
        model=HasDatasetVariableRel,
        cardinality=One,
    )

    has_sponsor_model_instance = RelationshipTo(
        SponsorModelDatasetVariableInstance, "HAS_INSTANCE", model=ClinicalMdrRel
    )
