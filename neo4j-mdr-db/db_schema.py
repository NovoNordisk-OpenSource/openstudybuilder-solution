"""
Contains all statements definining the db schema, such as:
 - CREATE INDEX ...
 - CREATE CONSTRAINT ...
"""

SCHEMA_CLEAR_QUERY = "CALL apoc.schema.assert({}, {})"
CONSTRAINT_TYPE_NODE_KEY = "NODE KEY"
CONSTRAINT_TYPE_UNIQUE = "UNIQUE"
CONSTRAINT_TYPE_NOT_NULL = "NOT NULL"

# array of indexes to create [label, property]
INDEXES = [
    ("StudyEpoch", "uid"),
    ("OrderedStudySelection", "uid"),
    ("StudySelection", "uid"),
    ("StudyVisit", "uid"),
    ("StudyArm", "uid"),
    ("StudyCohort", "uid"),
    ("StudyElement", "uid"),
    ("StudyDesignCell", "uid"),
    ("StudyActivity", "uid"),
    ("StudyCriteria", "uid"),
    ("StudyObjective", "uid"),
    ("StudyEndpoint", "uid"),
    ("StudyCompound", "uid"),
    ("StudyActivitySchedule", "uid"),
    ("StudyBranchArm", "uid"),
    ("StudyDiseaseMilestone", "uid"),
    ("StudySoAFootnote", "uid"),
    ("OrderedStudySelectionDiseaseMilestone", "uid"),
    ("TemplateParameterTermValue", "name"),
    ("CTCodelistAttributesValue", "name"),
    ("CTCodelistNameValue", "name"),
    ("CTTermNameValue", "name"),
    ("DictionaryCodelistValue", "name"),
    ("SnomedTermValue", "name"),
    ("DictionaryTermValue", "name"),
    ("MEDRTTermValue", "name"),
    ("UCUMTermValue", "name"),
    ("UNIITermValue", "name"),
    ("UnitDefinitionValue", "name"),
    ("ConceptValue", "name"),
    ("ActivityGroupValue", "name"),
    ("ActivitySubGroupValue", "name"),
    ("ActivityValue", "name"),
    ("ActivityInstanceValue", "name"),
    ("ActivityInstanceClassValue", "name"),
    ("ActivityItemClassValue", "name"),
    ("LagTimeValue", "name"),
    ("NumericValue", "name"),
    ("SimpleConceptValue", "name"),
    ("NumericValueWithUnitValue", "name"),
    ("CompoundValue", "name"),
    ("CompoundAliasValue", "name"),
    ("MedicinalProductValue", "name"),
    ("ActiveSubstanceValue", "analyte_number"),
    ("ActiveSubstanceValue", "inn"),
    ("OdmVendorNamespaceValue", "name"),
    ("OdmVendorAttributeValue", "name"),
    ("OdmTemplateValue", "name"),
    ("OdmDescriptionValue", "name"),
    ("OdmFormValue", "name"),
    ("OdmItemGroupValue", "name"),
    ("OdmItemValue", "name"),
    ("OdmAliasValue", "name"),
    ("ObjectiveTemplateValue", "name"),
    ("ObjectiveValue", "name"),
    ("EndpointTemplateValue", "name"),
    ("EndpointValue", "name"),
    ("TimeframeTemplateValue", "name"),
    ("TimeframeValue", "name"),
    ("StudyDayValue", "name"),
    ("StudyDurationDaysValue", "name"),
    ("StudyDurationWeeksValue", "name"),
    ("StudyWeekValue", "name"),
    ("VisitNameValue", "name"),
    ("CriteriaTemplateValue", "name"),
    ("TimePointValue", "name"),
    ("CriteriaValue", "name"),
    ("ActivityInstructionTemplateValue", "name"),
    ("CTTermAttributesValue", "code_submission_value"),
    ("CTTermAttributesValue", "name_submission_value"),
    ("StudyField", "field_name"),
    ("DataModelVersion", "uid"),
    ("ActivityGrouping", "uid"),
    ("ActivityValidGroup", "uid"),
    ("StudyActivityGroup", "uid"),
    ("StudyActivitySubGroup", "uid"),
    ("StudyActivityInstance", "uid"),
    ("StudyCompoundDosing", "uid"),
    ("StudySoAGroup", "uid"),
    ("SyntaxIndexingInstanceRoot", "uid"),
    ("SyntaxIndexingTemplateRoot", "uid"),
    ("SyntaxInstanceRoot", "uid"),
    ("SyntaxPreInstanceRoot", "uid"),
    ("SyntaxTemplateRoot", "uid"),
    ("CriteriaPreInstanceValue", "name"),
    ("FootnoteTemplateValue", "name"),
    ("FootnoteValue", "name"),
    ("OdmStudyEventValue", "name"),
    ("SyntaxIndexingInstanceValue", "name"),
    ("SyntaxIndexingTemplateValue", "name"),
    ("SyntaxInstanceValue", "name"),
    ("SyntaxPreInstanceValue", "name"),
    ("SyntaxTemplateValue", "name"),
    ("TemplateParameterValue", "name"),
    ("TextValue", "name"),
    ("WeekInStudyValue", "name"),
]

# array of text indexes to create [label, property]
TEXT_INDEXES = [
    ("TemplateParameter", "name"),
    ("Library", "name"),
    ("CTCatalogue", "name"),
    ("CTPackage", "name"),
    ("ClinicalProgramme", "name"),
    ("Project", "name"),
    ("Brand", "name"),
]

# array of relation indexes to create [type, property]
REL_INDEXES = [
    ("CONTAINS_DATASET", "href"),
    ("CONTAINS_DATASET_CLASS", "href"),
    ("CONTAINS_VARIABLE_CLASS", "href"),
    ("CONTAINS_DATASET_VARIABLE", "href"),
    ("CONTAINS_DATASET_SCENARIO", "href"),
    ("HAS_VARIABLE_CLASS", "version_number"),
    ("HAS_DATASET_VARIABLE", "version_number"),
    ("HAS_VERSION", "start_date"),
    ("HAS_VERSION", "end_date"),
]

# array of constraints to create [label, property, type["NODE KEY", "UNIQUE", "NOT NULL"]]
CONSTRAINTS = [
    ("TemplateParameterTermRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("CTCodelistRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("CTTermRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("DictionaryCodelistRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("DictionaryTermRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("SnomedTermRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("MEDRTTermRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("UCUMTermRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("UNIITermRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("CTConfigRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("ConceptRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("UnitDefinitionRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("ActivityGroupRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("ActivitySubGroupRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("ActivityRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("ActivityInstanceRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("ActivityInstanceClassRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("ActivityItemClassRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("ActivityInstructionRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("ActivityInstructionTemplateRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("NumericValueRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("LagTimeRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("SimpleConceptRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("NumericValueWithUnitRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("CompoundRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("CompoundAliasRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("ActiveSubstanceRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("PharmaceuticalProductRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("MedicinalProductRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("OdmTemplateRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("OdmDescriptionRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("OdmFormRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("OdmItemGroupRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("OdmItemRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("OdmAliasRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("StudyRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("ObjectiveTemplateRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("ObjectiveRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("EndpointTemplateRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("EndpointRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("TimeframeTemplateRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("TimeframeRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("StudyDayRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("StudyDurationDaysRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("StudyDurationWeeksRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("StudyWeekRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("VisitNameRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("CriteriaTemplateRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("TimePointRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("CriteriaRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("CTPackage", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("CTPackageCodelist", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("CTPackageTerm", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("ClinicalProgramme", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("Project", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("CTTermNameRoot", "uid", CONSTRAINT_TYPE_UNIQUE),
    ("Counter", "counterId", CONSTRAINT_TYPE_NODE_KEY),
    ("Brand", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("OdmVendorAttributeRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("OdmVendorNamespaceRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("DataModelCatalogue", "name", CONSTRAINT_TYPE_NODE_KEY),
    ("DataModelPackage", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("DataModelVersion", "href", CONSTRAINT_TYPE_NODE_KEY),
    ("DataModelRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("DataModelIGRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("DataModelValue", "name", CONSTRAINT_TYPE_NODE_KEY),
    ("DataModelIGValue", "name", CONSTRAINT_TYPE_NODE_KEY),
    ("DatasetClass", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("Dataset", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("VariableClass", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("DatasetVariable", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("CommentTopic", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("CommentTopic", "topic_path", CONSTRAINT_TYPE_NODE_KEY),
    ("CommentThread", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("CommentReply", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("CriteriaPreInstanceRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("FootnoteRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("FootnoteTemplateRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("OdmStudyEventRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("TemplateParameterValueRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("TextValueRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
    ("User", "user_id", CONSTRAINT_TYPE_NODE_KEY),
    ("WeekInStudyRoot", "uid", CONSTRAINT_TYPE_NODE_KEY),
]


def build_create_node_index_query(data):
    label, prop = data
    name = label + "_" + prop
    query = f"CREATE INDEX index_{name} IF NOT EXISTS FOR (n:{label}) ON (n.{prop})"
    return query


def build_create_node_text_index_query(data):
    label, prop = data
    name = label + "_" + prop
    query = (
        f"CREATE TEXT INDEX index_{name} IF NOT EXISTS FOR (n:{label}) ON (n.{prop})"
    )
    return query


def build_create_rel_index_query(data):
    label, prop = data
    name = label + "_" + prop
    query = (
        f"CREATE INDEX index_{name} IF NOT EXISTS  FOR ()-[r:{label}]-() ON r.{prop}"
    )
    return query


def build_create_constraint_query(label: str, property: str, type: str):
    """
    Queries the constraints creation, where the type of the constraint could be key, unique or not null.
    The constraint will be added on the specified label and property
    input:
        label: str
        property: str
        type: str ["NODE_KEY", "UNIQUE", "NOT NULL"]
    """
    if type not in [
        CONSTRAINT_TYPE_NODE_KEY,
        CONSTRAINT_TYPE_UNIQUE,
        CONSTRAINT_TYPE_NOT_NULL,
    ]:
        raise TypeError(
            f"Constraint type '{type}' for label '{label}' and property '{property}' must be 'NODE KEY', 'UNIQUE' or 'NOT NULL' "
        )
    query = f"CREATE CONSTRAINT constraint_{label}_{property} IF NOT EXISTS FOR (n:{label}) REQUIRE (n.{property}) IS {type}"
    return query


def build_schema_queries():
    queries = []
    for idx in INDEXES:
        query = build_create_node_index_query(idx)
        queries.append(query)

    for idx in TEXT_INDEXES:
        query = build_create_node_text_index_query(idx)
        queries.append(query)

    for idx in REL_INDEXES:
        query = build_create_rel_index_query(idx)
        queries.append(query)

    for cst in CONSTRAINTS:
        query = build_create_constraint_query(
            label=cst[0], property=cst[1], type=cst[2]
        )
        queries.append(query)

    return queries


def drop_indexes_and_constraints(session):
    """Drops all indexes and constraints"""
    for constraint in session.run("SHOW ALL CONSTRAINTS YIELD name"):
        drop_statement = "DROP CONSTRAINT " + constraint[0]
        print(drop_statement)
        session.run(drop_statement)

    for index in session.run("SHOW ALL INDEXES YIELD name"):
        drop_statement = "DROP INDEX " + index[0]
        print(drop_statement)
        session.run(drop_statement)
