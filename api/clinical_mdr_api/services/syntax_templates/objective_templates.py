from clinical_mdr_api.domain_repositories.syntax_instances.objective_repository import (
    ObjectiveRepository,
)
from clinical_mdr_api.domain_repositories.syntax_pre_instances.objective_pre_instance_repository import (
    ObjectivePreInstanceRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.objective_template_repository import (
    ObjectiveTemplateRepository,
)
from clinical_mdr_api.domains.syntax_templates.objective_template import (
    ObjectiveTemplateAR,
)
from clinical_mdr_api.models.syntax_templates.objective_template import (
    ObjectiveTemplate,
    ObjectiveTemplateCreateInput,
    ObjectiveTemplateVersion,
    ObjectiveTemplateWithCount,
)
from clinical_mdr_api.services.syntax_templates.generic_syntax_template_service import (
    GenericSyntaxTemplateService,
)


class ObjectiveTemplateService(GenericSyntaxTemplateService[ObjectiveTemplateAR]):
    aggregate_class = ObjectiveTemplateAR
    version_class = ObjectiveTemplateVersion
    repository_interface = ObjectiveTemplateRepository
    instance_repository_interface = ObjectiveRepository
    pre_instance_repository_interface = ObjectivePreInstanceRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ObjectiveTemplateAR
    ) -> ObjectiveTemplate:
        cls = ObjectiveTemplateWithCount if item_ar.counts != 0 else ObjectiveTemplate
        return cls.from_objective_template_ar(item_ar)

    def _create_ar_from_input_values(
        self, template: ObjectiveTemplateCreateInput
    ) -> ObjectiveTemplateAR:
        template_vo, library_vo = self._create_template_vo(template)

        # Get indexings for templates from database
        (
            indications,
            categories,
            _,
            _,
            _,
            _,
            _,
        ) = self._get_indexings(template)

        # Process item to save
        item = ObjectiveTemplateAR.from_input_values(
            author_id=self.author_id,
            template=template_vo,
            library=library_vo,
            generate_uid_callback=self.repository.generate_uid_callback,
            next_available_sequence_id_callback=self.repository.next_available_sequence_id,
            is_confirmatory_testing=template.is_confirmatory_testing,
            indications=indications,
            categories=categories,
        )

        return item
