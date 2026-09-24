from neomodel import db

from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.syntax import (
    CriteriaRoot,
    CriteriaTemplateRoot,
    CriteriaValue,
)
from clinical_mdr_api.domain_repositories.syntax_instances.generic_syntax_instance_repository import (
    GenericSyntaxInstanceRepository,
)
from clinical_mdr_api.domains.syntax_instances.criteria import CriteriaAR
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO


class CriteriaRepository(GenericSyntaxInstanceRepository[CriteriaAR]):
    root_class = CriteriaRoot
    value_class = CriteriaValue
    template_class = CriteriaTemplateRoot

    def _create_ar(
        self,
        root: CriteriaRoot,
        library: Library,
        relationship: VersionRelationship,
        value: CriteriaValue,
        study_count: int = 0,
        **kwargs,
    ) -> CriteriaAR:
        return CriteriaAR.from_repository_values(
            uid=root.uid,
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
            template=self.get_template_vo(root, value, kwargs["instance_template"]),
            study_count=study_count,
        )

    def check_exists_by_name_for_type(self, name: str, criteria_type_uid: str) -> bool:
        query = f"""
MATCH (term:CTTermRoot WHERE term.uid=$type_uid)<-[:HAS_SELECTED_TERM]-(:CTTermContext)<-[:HAS_TYPE]-(:CriteriaTemplateRoot)-->(:{self.root_class.__label__})
-[:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED|LATEST]->(v:{self.value_class.__label__} WHERE v.name=$name)
RETURN count(DISTINCT v)
"""

        result, _ = db.cypher_query(
            query, {"type_uid": criteria_type_uid, "name": name}
        )
        return len(result) > 0 and result[0][0] > 0
