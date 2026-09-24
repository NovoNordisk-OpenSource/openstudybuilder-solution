from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.syntax import (
    EndpointRoot,
    EndpointTemplateRoot,
    EndpointValue,
)
from clinical_mdr_api.domain_repositories.syntax_instances.generic_syntax_instance_repository import (
    GenericSyntaxInstanceRepository,
)
from clinical_mdr_api.domains.syntax_instances.endpoint import EndpointAR
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO


class EndpointRepository(GenericSyntaxInstanceRepository[EndpointAR]):
    root_class = EndpointRoot
    value_class = EndpointValue
    template_class = EndpointTemplateRoot

    def _create_ar(
        self,
        root: EndpointRoot,
        library: Library,
        relationship: VersionRelationship,
        value: EndpointValue,
        study_count: int = 0,
        **kwargs,
    ) -> EndpointAR:
        return EndpointAR.from_repository_values(
            uid=root.uid,
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
            template=self.get_template_vo(root, value, kwargs["instance_template"]),
            study_count=study_count,
        )
