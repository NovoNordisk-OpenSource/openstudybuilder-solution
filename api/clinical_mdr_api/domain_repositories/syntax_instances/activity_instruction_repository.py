from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.syntax import (
    ActivityInstructionRoot,
    ActivityInstructionTemplateRoot,
    ActivityInstructionValue,
)
from clinical_mdr_api.domain_repositories.syntax_instances.generic_syntax_instance_repository import (
    GenericSyntaxInstanceRepository,
)
from clinical_mdr_api.domains.syntax_instances.activity_instruction import (
    ActivityInstructionAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO


class ActivityInstructionRepository(
    GenericSyntaxInstanceRepository[ActivityInstructionAR]
):
    root_class = ActivityInstructionRoot
    value_class = ActivityInstructionValue
    template_class = ActivityInstructionTemplateRoot

    def _create_ar(
        self,
        root: ActivityInstructionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: ActivityInstructionValue,
        study_count: int = 0,
        **kwargs,
    ) -> ActivityInstructionAR:
        return ActivityInstructionAR.from_repository_values(
            uid=root.uid,
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
            template=self.get_template_vo(root, value, kwargs["instance_template"]),
            study_count=study_count,
        )
