from neomodel import RelationshipFrom, RelationshipTo, db

from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    ClinicalMdrRel,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from common.neomodel import StringProperty


class TemplateParameter(ClinicalMdrNode):
    RELATION_LABEL = "HAS_PARAMETER_TERM"
    has_parameter_term = RelationshipTo(
        "TemplateParameterTermRoot", RELATION_LABEL, model=ClinicalMdrRel
    )

    name = StringProperty()


class TemplateParameterTermValue(VersionValue):
    name = StringProperty()


class TemplateParameterTermRoot(VersionRoot):
    RELATION_LABEL = "HAS_PARAMETER_TERM"
    PARAMETERS_LABEL = "USES_DEFAULT_VALUE"

    uid = StringProperty()

    has_parameter_term = RelationshipFrom(TemplateParameter, RELATION_LABEL)

    has_version = RelationshipTo(
        TemplateParameterTermValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        TemplateParameterTermValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        TemplateParameterTermValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        TemplateParameterTermValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        TemplateParameterTermValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )

    @classmethod
    def check_parameter_term_exists(
        cls, parameter_name: str, parameter_term_uid: str
    ) -> bool:
        cypher_query = """
            RETURN
                CASE 
                    WHEN EXISTS((:TemplateParameter {name: $name})<-[:HAS_PARENT_PARAMETER*0..]-()-[:HAS_PARAMETER_TERM]->(:TemplateParameterTermRoot{uid: $uid})) THEN TRUE
                    WHEN EXISTS((:TemplateParameter {name: $name})-[:HAS_PARAMETER_TERM]->(:CTTermNameRoot{uid: $uid})) THEN TRUE
                    ELSE FALSE
                END AS RESULT
            """
        dataset, _ = db.cypher_query(
            cypher_query, {"uid": parameter_term_uid, "name": parameter_name}
        )
        return dataset[0][0]


class ParameterTemplateValue(TemplateParameterTermValue):
    template_string = StringProperty()

    def get_all(self):
        cypher_query = """
            MATCH (otv:ParameterTemplateValue)<-[:LATEST_FINAL]-(ot:ParameterTemplateRoot)<-[rel:TPCV_USES_TPV]-(pt)
            WHERE elementId(pt) = $element_id
            RETURN
                pt.name AS name, ot.uid AS uid, rel.position as position, otv.value as value, otv.name as param_value

            """
        dataset, _ = db.cypher_query(cypher_query, {"element_id": self.element_id})
        return dataset


class ParameterTemplateRoot(TemplateParameterTermRoot):
    has_version = RelationshipTo(
        ParameterTemplateValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        ParameterTemplateValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        ParameterTemplateValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        ParameterTemplateValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        ParameterTemplateValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )

    has_parameter_term = RelationshipFrom(
        TemplateParameter, "HAS_PARAMETER_TERM", model=ClinicalMdrRel
    )
