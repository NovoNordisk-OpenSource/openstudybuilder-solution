from clinical_mdr_api.domain_repositories.generic_repository import (
    _manage_versioning_with_relations,
)
from clinical_mdr_api.domain_repositories.models._utils import ListDistinct
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import Create, Edit
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyArm,
    StudyCohort,
)
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyDesignClass as StudyDesignClassNeomodel,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    StudyDesignClassInput,
)
from common import exceptions


class StudyDesignClassRepository:

    def get_study_design_class(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> StudyDesignClassNeomodel | None:

        if study_value_version:
            filters = {
                "has_study_design_class__has_version__uid": study_uid,
                "has_study_design_class__has_version|version": study_value_version,
            }
        else:
            filters = {
                "has_study_design_class__latest_value__uid": study_uid,
            }

        nodes = (
            ListDistinct(
                StudyDesignClassNeomodel.nodes.traverse(
                    "has_after__audit_trail",
                )
                .filter(**filters)
                .resolve_subgraph()
            )
        ).distinct()
        exceptions.BusinessLogicException.raise_if(
            len(nodes) > 1,
            msg=f"Found more than one StudyDesignClass node for Study with UID '{study_uid}'.",
        )
        return nodes[0] if len(nodes) > 0 else None

    def is_study_design_class_edition_allowed(
        self,
        study_uid: str,
    ) -> bool:
        """
        Check if StudyDesignClass edition is allowed.
        If there exists some StudyArms or StudyCohorts in given Study it returns False, otherwise it returns True.
        """

        study_arms = (
            StudyArm.nodes.has(has_before=False)
            .filter(study_value__latest_value__uid=study_uid)
            .resolve_subgraph()
        )
        study_cohorts = (
            StudyCohort.nodes.has(has_before=False)
            .filter(study_value__latest_value__uid=study_uid)
            .resolve_subgraph()
        )
        return len(study_arms) == 0 and len(study_cohorts) == 0

    def post_study_design_class(
        self,
        study_uid: str,
        study_design_class_input: StudyDesignClassInput,
        author_id: str,
    ) -> StudyDesignClassNeomodel:
        """Creates StudyDesignClass node if none are present"""

        study_root = StudyRoot.nodes.get(uid=study_uid)
        latest_study_value: StudyValue = study_root.latest_value.single()

        study_design_class_node = StudyDesignClassNeomodel(
            value=study_design_class_input.value.value
        ).save()
        latest_study_value.has_study_design_class.connect(study_design_class_node)

        _manage_versioning_with_relations(
            study_root=study_root,
            action_type=Create,
            before=None,
            after=study_design_class_node,
            author_id=author_id,
        )

        return self.get_study_design_class(study_uid=study_uid)

    def edit_study_design_class(
        self,
        study_uid: str,
        study_design_class_input: StudyDesignClassInput,
        previous_node: StudyDesignClassNeomodel,
        author_id: str,
    ) -> StudyDesignClassNeomodel:
        """Replaces StudyDesignClass node"""

        study_root = StudyRoot.nodes.get(uid=study_uid)
        latest_study_value: StudyValue = study_root.latest_value.single()

        # disconnect the previous version from StudyValue
        latest_study_value.has_study_design_class.disconnect(previous_node)

        study_design_class_node = StudyDesignClassNeomodel(
            value=study_design_class_input.value.value
        ).save()
        latest_study_value.has_study_design_class.connect(study_design_class_node)

        _manage_versioning_with_relations(
            study_root=study_root,
            action_type=Edit,
            before=previous_node,
            after=study_design_class_node,
            exclude_relationships=[],
            author_id=author_id,
        )

        return self.get_study_design_class(study_uid=study_uid)
