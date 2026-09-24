from neomodel import RelationshipFrom, RelationshipTo, ZeroOrMore, db

from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGroupRoot,
    ActivityRoot,
    ActivitySubGroupRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermContext,
)
from clinical_mdr_api.domain_repositories.models.dictionary import DictionaryTermRoot
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrRel,
    Conjunction,
    ConjunctionRelation,
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameter,
    TemplateParameterTermRoot,
    TemplateParameterTermValue,
)
from common.neomodel import BooleanProperty, IntegerProperty, StringProperty


#########################
##### Common Syntax #####
#########################
# pylint: disable=abstract-method
class UsesParameterRelation(ClinicalMdrRel):
    position = IntegerProperty()
    allow_multiple = BooleanProperty()
    allow_none = BooleanProperty()


# pylint: disable=abstract-method
class UsesValueRelation(ClinicalMdrRel):
    position = IntegerProperty()
    index = IntegerProperty()
    set_number = IntegerProperty()


###########################
##### Syntax Template #####
###########################
class SyntaxTemplateValue(VersionValue):
    name = StringProperty()
    name_plain = StringProperty()
    guidance_text = StringProperty()

    has_conjunction = RelationshipTo(
        Conjunction,
        "HAS_CONJUNCTION",
        cardinality=ZeroOrMore,
        model=ConjunctionRelation,
    )

    def get_study_count(
        self,
        template_rel: str | None = None,
        study_selection_rel: str | None = None,
        study_rel: str | None = None,
    ) -> int:
        cypher_query = f"""
MATCH (n)<--(:SyntaxTemplateRoot)-[:{template_rel}]->(:SyntaxInstanceRoot)-->(:SyntaxInstanceValue)
<-[:{study_selection_rel}]-(:StudySelection)<-[:{study_rel}]-(:StudyValue)<-[:HAS_VERSION|LATEST_DRAFT|LATEST_FINAL|LATEST_RETIRED]-(sr:StudyRoot)
WHERE elementId(n)=$element_id
RETURN count(DISTINCT sr)
"""

        count, _ = db.cypher_query(cypher_query, {"element_id": self.element_id})
        return count[0][0]


class SyntaxTemplateRoot(VersionRoot):
    LIBRARY_REL_LABEL = "CONTAINS_SYNTAX_TEMPLATE"
    PARAMETERS_LABEL = "USES_PARAMETER"

    sequence_id = StringProperty()

    has_pre_instance = RelationshipFrom("SyntaxPreInstanceRoot", "CREATED_FROM")
    has_indication = RelationshipTo(DictionaryTermRoot, "HAS_INDICATION")
    # uses_parameter
    has_parameters = RelationshipTo(
        TemplateParameter,
        PARAMETERS_LABEL,
        cardinality=ZeroOrMore,
        model=UsesParameterRelation,
    )

    has_library = RelationshipFrom(Library, LIBRARY_REL_LABEL)
    has_version = RelationshipTo(
        SyntaxTemplateValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        SyntaxTemplateValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        SyntaxTemplateValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        SyntaxTemplateValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        SyntaxTemplateValue, "LATEST_RETIRED", model=VersionRelationship
    )


class SyntaxIndexingTemplateValue(SyntaxTemplateValue): ...


class SyntaxIndexingTemplateRoot(SyntaxTemplateRoot):
    has_category = RelationshipTo(CTTermContext, "HAS_CATEGORY")
    has_subcategory = RelationshipTo(CTTermContext, "HAS_SUBCATEGORY")


class CriteriaTemplateValue(SyntaxIndexingTemplateValue):
    def get_study_count(
        self,
        template_rel: str | None = None,
        study_selection_rel: str | None = None,
        study_rel: str | None = None,
    ) -> int:
        return super().get_study_count(
            CriteriaTemplateRoot.TEMPLATE_REL_LABEL,
            "HAS_SELECTED_CRITERIA",
            "HAS_STUDY_CRITERIA",
        )


class CriteriaTemplateRoot(SyntaxIndexingTemplateRoot):
    TEMPLATE_REL_LABEL = "HAS_CRITERIA"

    has_template = RelationshipTo("CriteriaRoot", TEMPLATE_REL_LABEL)
    has_type = RelationshipTo(CTTermContext, "HAS_TYPE")


class FootnoteTemplateValue(SyntaxTemplateValue):
    def get_study_count(
        self,
        template_rel: str | None = None,
        study_selection_rel: str | None = None,
        study_rel: str | None = None,
    ) -> int:
        return super().get_study_count(
            FootnoteTemplateRoot.TEMPLATE_REL_LABEL,
            "HAS_SELECTED_FOOTNOTE",
            "HAS_STUDY_FOOTNOTE",
        )

    has_version = RelationshipFrom(
        "FootnoteTemplateRoot", "HAS_VERSION", model=VersionRelationship
    )


class FootnoteTemplateRoot(SyntaxTemplateRoot):
    TEMPLATE_REL_LABEL = "HAS_FOOTNOTE"

    has_template = RelationshipTo("FootnoteRoot", TEMPLATE_REL_LABEL)
    has_type = RelationshipTo(CTTermContext, "HAS_TYPE")
    has_activity = RelationshipTo(ActivityRoot, "HAS_ACTIVITY")
    has_activity_group = RelationshipTo(ActivityGroupRoot, "HAS_ACTIVITY_GROUP")
    has_activity_subgroup = RelationshipTo(
        ActivitySubGroupRoot, "HAS_ACTIVITY_SUBGROUP"
    )


class EndpointTemplateValue(SyntaxIndexingTemplateValue):
    def get_study_count(
        self,
        template_rel: str | None = None,
        study_selection_rel: str | None = None,
        study_rel: str | None = None,
    ) -> int:
        return super().get_study_count(
            EndpointTemplateRoot.TEMPLATE_REL_LABEL,
            "HAS_SELECTED_ENDPOINT",
            "HAS_STUDY_ENDPOINT",
        )


class EndpointTemplateRoot(SyntaxIndexingTemplateRoot):
    TEMPLATE_REL_LABEL = "HAS_ENDPOINT"

    has_template = RelationshipTo("EndpointRoot", TEMPLATE_REL_LABEL)


class ObjectiveTemplateValue(SyntaxIndexingTemplateValue):
    def get_study_count(
        self,
        template_rel: str | None = None,
        study_selection_rel: str | None = None,
        study_rel: str | None = None,
    ) -> int:
        return super().get_study_count(
            ObjectiveTemplateRoot.TEMPLATE_REL_LABEL,
            "HAS_SELECTED_OBJECTIVE",
            "HAS_STUDY_OBJECTIVE",
        )


class ObjectiveTemplateRoot(SyntaxIndexingTemplateRoot):
    TEMPLATE_REL_LABEL = "HAS_OBJECTIVE"

    is_confirmatory_testing = BooleanProperty()

    has_template = RelationshipTo("ObjectiveRoot", TEMPLATE_REL_LABEL)


class ActivityInstructionTemplateValue(SyntaxTemplateValue):
    def get_study_count(
        self,
        template_rel: str | None = None,
        study_selection_rel: str | None = None,
        study_rel: str | None = None,
    ) -> int:
        return super().get_study_count(
            ActivityInstructionTemplateRoot.TEMPLATE_REL_LABEL,
            "HAS_SELECTED_ACTIVITY_INSTRUCTION",
            "HAS_STUDY_ACTIVITY_INSTRUCTION",
        )


class ActivityInstructionTemplateRoot(SyntaxTemplateRoot):
    TEMPLATE_REL_LABEL = "HAS_ACTIVITY_INSTRUCTION"

    has_template = RelationshipTo("ActivityInstructionRoot", TEMPLATE_REL_LABEL)
    has_activity = RelationshipTo(ActivityRoot, "HAS_ACTIVITY")
    has_activity_group = RelationshipTo(ActivityGroupRoot, "HAS_ACTIVITY_GROUP")
    has_activity_subgroup = RelationshipTo(
        ActivitySubGroupRoot, "HAS_ACTIVITY_SUBGROUP"
    )


class TimeframeTemplateValue(SyntaxTemplateValue):
    def get_study_count(
        self,
        template_rel: str | None = None,
        study_selection_rel: str | None = None,
        study_rel: str | None = None,
    ): ...


class TimeframeTemplateRoot(SyntaxTemplateRoot):
    TEMPLATE_REL_LABEL = "HAS_TIMEFRAME"

    has_template = RelationshipTo("TimeframeRoot", TEMPLATE_REL_LABEL)


###############################
##### Syntax Pre-Instance #####
###############################
class SyntaxPreInstanceValue(VersionValue):
    PARAMETERS_LABEL = "USES_VALUE"

    name = StringProperty()
    name_plain = StringProperty()
    guidance_text = StringProperty()

    # uses_value
    has_parameters = RelationshipTo(
        TemplateParameterTermValue,
        PARAMETERS_LABEL,
        cardinality=ZeroOrMore,
        model=UsesValueRelation,
    )
    has_conjunction = RelationshipTo(
        Conjunction,
        "HAS_CONJUNCTION",
        cardinality=ZeroOrMore,
        model=ConjunctionRelation,
    )


class SyntaxPreInstanceRoot(VersionRoot):
    LIBRARY_REL_LABEL = "CONTAINS_SYNTAX_PRE_INSTANCE"

    sequence_id = StringProperty()

    has_indication = RelationshipTo(DictionaryTermRoot, "HAS_INDICATION")

    created_from = RelationshipTo("SyntaxTemplateRoot", "CREATED_FROM")
    has_library = RelationshipFrom(Library, LIBRARY_REL_LABEL)
    has_version = RelationshipTo(
        SyntaxPreInstanceValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        SyntaxPreInstanceValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        SyntaxPreInstanceValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        SyntaxPreInstanceValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        SyntaxPreInstanceValue, "LATEST_RETIRED", model=VersionRelationship
    )


class CriteriaPreInstanceValue(SyntaxPreInstanceValue):
    def get_study_count(self): ...


class CriteriaPreInstanceRoot(SyntaxPreInstanceRoot):
    has_category = RelationshipTo(CTTermContext, "HAS_CATEGORY")
    has_subcategory = RelationshipTo(CTTermContext, "HAS_SUBCATEGORY")


class FootnotePreInstanceValue(SyntaxPreInstanceValue):
    def get_study_count(self): ...


class FootnotePreInstanceRoot(SyntaxPreInstanceRoot):
    has_activity = RelationshipTo(ActivityRoot, "HAS_ACTIVITY")
    has_activity_group = RelationshipTo(ActivityGroupRoot, "HAS_ACTIVITY_GROUP")
    has_activity_subgroup = RelationshipTo(
        ActivitySubGroupRoot, "HAS_ACTIVITY_SUBGROUP"
    )


class EndpointPreInstanceValue(SyntaxPreInstanceValue):
    def get_study_count(self): ...


class EndpointPreInstanceRoot(SyntaxPreInstanceRoot):
    has_category = RelationshipTo(CTTermContext, "HAS_CATEGORY")
    has_subcategory = RelationshipTo(CTTermContext, "HAS_SUBCATEGORY")


class ObjectivePreInstanceValue(SyntaxPreInstanceValue):
    def get_study_count(self): ...


class ObjectivePreInstanceRoot(SyntaxPreInstanceRoot):
    is_confirmatory_testing = BooleanProperty()
    has_category = RelationshipTo(CTTermContext, "HAS_CATEGORY")


class ActivityInstructionPreInstanceValue(SyntaxPreInstanceValue):
    def get_study_count(self): ...


class ActivityInstructionPreInstanceRoot(SyntaxPreInstanceRoot):
    has_activity = RelationshipTo(ActivityRoot, "HAS_ACTIVITY")
    has_activity_group = RelationshipTo(ActivityGroupRoot, "HAS_ACTIVITY_GROUP")
    has_activity_subgroup = RelationshipTo(
        ActivitySubGroupRoot, "HAS_ACTIVITY_SUBGROUP"
    )


###########################
##### Syntax Instance #####
###########################
class SyntaxInstanceValue(VersionValue):
    PARAMETERS_LABEL = "USES_VALUE"

    name = StringProperty()
    name_plain = StringProperty()

    # uses_value
    has_parameters = RelationshipTo(
        TemplateParameterTermRoot,
        PARAMETERS_LABEL,
        cardinality=ZeroOrMore,
        model=UsesValueRelation,
    )
    has_conjunction = RelationshipTo(
        Conjunction,
        "HAS_CONJUNCTION",
        cardinality=ZeroOrMore,
        model=ConjunctionRelation,
    )


class SyntaxInstanceRoot(VersionRoot):
    LIBRARY_REL_LABEL = "CONTAINS_SYNTAX_INSTANCE"

    has_library = RelationshipFrom(Library, LIBRARY_REL_LABEL)
    has_version = RelationshipTo(
        SyntaxInstanceValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        SyntaxInstanceValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        SyntaxInstanceValue, "LATEST_DRAFT", model=VersionRelationship
    )
    latest_final = RelationshipTo(
        SyntaxInstanceValue, "LATEST_FINAL", model=VersionRelationship
    )
    latest_retired = RelationshipTo(
        SyntaxInstanceValue, "LATEST_RETIRED", model=VersionRelationship
    )


class SyntaxIndexingInstanceValue(SyntaxInstanceValue): ...


class SyntaxIndexingInstanceRoot(SyntaxInstanceRoot): ...


class CriteriaValue(SyntaxIndexingInstanceValue):
    ROOT_NODE_LABEL = "CriteriaRoot"
    VALUE_NODE_LABEL = "CriteriaValue"
    STUDY_SELECTION_REL_LABEL = "HAS_SELECTED_CRITERIA"
    STUDY_VALUE_REL_LABEL = "HAS_STUDY_CRITERIA"


class CriteriaRoot(SyntaxIndexingInstanceRoot):
    TEMPLATE_REL_LABEL = "HAS_CRITERIA"

    has_template = RelationshipFrom(CriteriaTemplateRoot, TEMPLATE_REL_LABEL)


class FootnoteValue(SyntaxIndexingInstanceValue):
    ROOT_NODE_LABEL = "FootnoteRoot"
    VALUE_NODE_LABEL = "FootnoteValue"
    STUDY_SELECTION_REL_LABEL = "HAS_SELECTED_FOOTNOTE"
    STUDY_VALUE_REL_LABEL = "HAS_STUDY_FOOTNOTE"
    has_version = RelationshipFrom(
        "FootnoteRoot", "HAS_VERSION", model=VersionRelationship
    )


class FootnoteRoot(SyntaxIndexingInstanceRoot):
    TEMPLATE_REL_LABEL = "HAS_FOOTNOTE"

    has_template = RelationshipFrom(FootnoteTemplateRoot, TEMPLATE_REL_LABEL)


class EndpointValue(SyntaxIndexingInstanceValue):
    ROOT_NODE_LABEL = "EndpointRoot"
    VALUE_NODE_LABEL = "EndpointValue"
    STUDY_SELECTION_REL_LABEL = "HAS_SELECTED_ENDPOINT"
    STUDY_VALUE_REL_LABEL = "HAS_STUDY_ENDPOINT"


class EndpointRoot(SyntaxIndexingInstanceRoot):
    TEMPLATE_REL_LABEL = "HAS_ENDPOINT"

    has_template = RelationshipFrom(EndpointTemplateRoot, TEMPLATE_REL_LABEL)


class ObjectiveValue(SyntaxIndexingInstanceValue):
    ROOT_NODE_LABEL = "ObjectiveRoot"
    VALUE_NODE_LABEL = "ObjectiveValue"
    STUDY_SELECTION_REL_LABEL = "HAS_SELECTED_OBJECTIVE"
    STUDY_VALUE_REL_LABEL = "HAS_STUDY_OBJECTIVE"


class ObjectiveRoot(SyntaxIndexingInstanceRoot):
    TEMPLATE_REL_LABEL = "HAS_OBJECTIVE"

    has_template = RelationshipFrom(ObjectiveTemplateRoot, TEMPLATE_REL_LABEL)


class ActivityInstructionValue(SyntaxInstanceValue):
    ROOT_NODE_LABEL = "ActivityInstructionRoot"
    VALUE_NODE_LABEL = "ActivityInstructionValue"
    STUDY_SELECTION_REL_LABEL = "HAS_SELECTED_ACTIVITY_INSTRUCTION"
    STUDY_VALUE_REL_LABEL = "HAS_STUDY_ACTIVITY_INSTRUCTION"

    activity_instruction_root = RelationshipFrom("ActivityInstructionRoot", "LATEST")


class ActivityInstructionRoot(SyntaxInstanceRoot):
    TEMPLATE_REL_LABEL = "HAS_ACTIVITY_INSTRUCTION"

    has_template = RelationshipFrom(ActivityInstructionTemplateRoot, TEMPLATE_REL_LABEL)


class TimeframeValue(SyntaxInstanceValue):
    ROOT_NODE_LABEL = "TimeframeRoot"
    VALUE_NODE_LABEL = "TimeframeValue"
    STUDY_SELECTION_REL_LABEL = "HAS_SELECTED_TIMEFRAME"
    STUDY_VALUE_REL_LABEL = "HAS_STUDY_ENDPOINT"


class TimeframeRoot(SyntaxInstanceRoot):
    TEMPLATE_REL_LABEL = "HAS_TIMEFRAME"

    has_template = RelationshipFrom(TimeframeTemplateRoot, TEMPLATE_REL_LABEL)
