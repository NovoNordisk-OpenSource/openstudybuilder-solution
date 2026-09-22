from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.syntax import (
    TimeframeTemplateRoot,
    TimeframeTemplateValue,
)
from clinical_mdr_api.domain_repositories.syntax_templates.generic_syntax_template_repository import (
    GenericSyntaxTemplateRepository,
)
from clinical_mdr_api.domains.syntax_templates.timeframe_template import (
    TimeframeTemplateAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO


class TimeframeTemplateRepository(GenericSyntaxTemplateRepository[TimeframeTemplateAR]):
    root_class = TimeframeTemplateRoot
    value_class = TimeframeTemplateValue

    def _create_ar(
        self,
        root: TimeframeTemplateRoot,
        library: Library,
        relationship: VersionRelationship,
        value: TimeframeTemplateValue,
        study_count: int = 0,
        **kwargs,
    ) -> TimeframeTemplateAR:
        return TimeframeTemplateAR.from_repository_values(
            uid=root.uid,
            sequence_id=root.sequence_id,
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
            template=self._get_template(value),
            study_count=study_count,
        )
