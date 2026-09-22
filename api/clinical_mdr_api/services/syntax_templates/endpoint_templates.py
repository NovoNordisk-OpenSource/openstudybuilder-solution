from clinical_mdr_api.domain_repositories.syntax_instances.endpoint_repository import (
    EndpointRepository,
)
from clinical_mdr_api.domain_repositories.syntax_pre_instances.endpoint_pre_instance_repository import (
    EndpointPreInstanceRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.endpoint_template_repository import (
    EndpointTemplateRepository,
)
from clinical_mdr_api.domains.syntax_templates.endpoint_template import (
    EndpointTemplateAR,
)
from clinical_mdr_api.models.syntax_templates.endpoint_template import (
    EndpointTemplate,
    EndpointTemplateCreateInput,
    EndpointTemplateVersion,
    EndpointTemplateWithCount,
)
from clinical_mdr_api.services.syntax_templates.generic_syntax_template_service import (
    GenericSyntaxTemplateService,
)


class EndpointTemplateService(GenericSyntaxTemplateService[EndpointTemplateAR]):
    aggregate_class = EndpointTemplateAR
    version_class = EndpointTemplateVersion
    repository_interface = EndpointTemplateRepository
    instance_repository_interface = EndpointRepository
    pre_instance_repository_interface = EndpointPreInstanceRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: EndpointTemplateAR
    ) -> EndpointTemplate:
        cls = (
            EndpointTemplateWithCount if item_ar.study_count != 0 else EndpointTemplate
        )
        return cls.from_endpoint_template_ar(item_ar)

    def _create_ar_from_input_values(
        self, template: EndpointTemplateCreateInput
    ) -> EndpointTemplateAR:
        template_vo, library_vo = self._create_template_vo(template)

        # Get indexings for templates from database
        (
            indications,
            categories,
            sub_categories,
            _,
            _,
            _,
            _,
        ) = self._get_indexings(template)

        # Process item to save
        item = EndpointTemplateAR.from_input_values(
            author_id=self.author_id,
            template=template_vo,
            library=library_vo,
            generate_uid_callback=self.repository.generate_uid_callback,
            next_available_sequence_id_callback=self.repository.next_available_sequence_id,
            indications=indications,
            categories=categories,
            sub_categories=sub_categories,
        )

        return item
