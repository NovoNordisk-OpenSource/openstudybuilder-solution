from neomodel import (
    ArrayProperty,
    BooleanProperty,
    IntegerProperty,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
    ZeroOrMore,
    db,
)

from clinical_mdr_api.domain_repositories.models.concepts import UnitDefinitionRoot
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.dictionary import DictionaryTermRoot
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    ClinicalMdrRel,
)
from clinical_mdr_api.domain_repositories.models.project import Project
from clinical_mdr_api.domain_repositories.models.study_selections import AuditTrailMixin


class StudyField(ClinicalMdrNode, AuditTrailMixin):
    has_type = RelationshipTo(CTTermRoot, "HAS_TYPE", model=ClinicalMdrRel)
    has_dictionary_type = RelationshipTo(
        DictionaryTermRoot,
        "HAS_DICTIONARY_TYPE",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    has_reason_for_null_value = RelationshipTo(
        CTTermRoot, "HAS_REASON_FOR_NULL_VALUE", model=ClinicalMdrRel
    )

    @classmethod
    def get_specific_field_currently_used_in_study(
        cls,
        field_name: str,
        value: any,
        study_uid: str,
        null_value_code: str | None = None,
    ):
        """
        Checks whether the StudyField with a given value has historically already been used in this study.
        """
        if not null_value_code:
            # StudyField value can be a scalar type (e.g. string, int, bool etc.) or a list of strings.
            # In case of a list type, there is no guarantee that the order of items in the supplied `value` list
            # is the same as in the corresponding`StudyField.value` DB field.
            #
            # Therefore, to ensure proper searching, we need to:
            #   - Convert the supplied `value` to a list if it is not already a list.
            #   - Convert the `StudyField.value` field in the DB to a list if it is not already a list.
            #   - Compare the two lists after sorting them.

            if not isinstance(value, list):
                value = [value]

            query = """
                MATCH (f:StudyField {field_name:$field_name})<--(:StudyValue)<-[:HAS_VERSION]-(s:StudyRoot{uid: $study_uid}) 
                WITH *,
                CASE apoc.meta.cypher.isType(f.value, "LIST OF STRING")
                    WHEN  True THEN f.value            
                    ELSE [f.value]
                END AS value_as_list
                WHERE apoc.coll.sort(value_as_list) = apoc.coll.sort($value)
                RETURN f
                """
        else:
            query = (
                "MATCH (term_root {uid:$null_value_code})<-[:HAS_REASON_FOR_NULL_VALUE]-"
                "(f:StudyField {field_name:$field_name})<--(:StudyValue)<-[:HAS_VERSION]-"
                "(s:StudyRoot{uid: $study_uid}) "
                "RETURN f"
            )
        result, _ = db.cypher_query(
            query,
            params={
                "study_uid": study_uid,
                "value": value,
                "field_name": field_name,
                "null_value_code": null_value_code,
            },
            resolve_objects=True,
        )
        if len(result) > 0 and len(result[0]) > 0:
            return result[0][0]
        return None


class StudyProjectField(StudyField):
    has_field = RelationshipFrom(Project, "HAS_FIELD", model=ClinicalMdrRel)


class StudyTextField(StudyField):
    value = StringProperty()
    field_name = StringProperty()

    def is_used(self, study_number: str) -> bool:
        cypher_query = """
        MATCH (stf:StudyField:StudyTextField{field_name: $field_name, value: $value})<-[HAS_TEXT_FIELD]-(sv:StudyValue)<-[:LATEST]-(s:StudyRoot)
        where sv.study_number <> $study_number
        return id(s)
        """
        result, _ = db.cypher_query(
            cypher_query,
            params={
                "field_name": self.field_name,
                "value": self.value,
                "study_number": study_number,
            },
        )
        return len(result) > 0


class StudyIntField(StudyField):
    value = IntegerProperty()
    field_name = StringProperty()


class StudyArrayField(StudyField):
    value = ArrayProperty()
    field_name = StringProperty()


class StudyBooleanField(StudyField):
    value = BooleanProperty()
    field_name = StringProperty()
    has_boolean_field = RelationshipFrom(
        ".study.StudyValue", "HAS_BOOLEAN_FIELD", model=ClinicalMdrRel
    )


class StudyTimeField(StudyField):
    value = StringProperty()
    field_name = StringProperty()
    has_unit_definition = RelationshipTo(
        UnitDefinitionRoot,
        "HAS_UNIT_DEFINITION",
        model=ClinicalMdrRel,
        cardinality=ZeroOrMore,
    )
    has_time_field = RelationshipFrom(
        ".study.StudyValue", "HAS_TIME_FIELD", model=ClinicalMdrRel
    )
