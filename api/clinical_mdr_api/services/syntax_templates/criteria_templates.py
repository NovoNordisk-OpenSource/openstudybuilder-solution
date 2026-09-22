from neomodel import db

from clinical_mdr_api.domain_repositories.syntax_instances.criteria_repository import (
    CriteriaRepository,
)
from clinical_mdr_api.domain_repositories.syntax_pre_instances.criteria_pre_instance_repository import (
    CriteriaPreInstanceRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.criteria_template_repository import (
    CriteriaTemplateRepository,
)
from clinical_mdr_api.domains.syntax_templates.criteria_template import (
    CriteriaTemplateAR,
)
from clinical_mdr_api.domains.syntax_templates.template import TemplateVO
from clinical_mdr_api.models.syntax_templates.criteria_template import (
    CriteriaTemplate,
    CriteriaTemplateCreateInput,
    CriteriaTemplateEditInput,
    CriteriaTemplateVersion,
    CriteriaTemplateWithCount,
)
from clinical_mdr_api.services.syntax_templates.generic_syntax_template_service import (
    GenericSyntaxTemplateService,
)
from common.exceptions import AlreadyExistsException


class CriteriaTemplateService(GenericSyntaxTemplateService[CriteriaTemplateAR]):
    aggregate_class = CriteriaTemplateAR
    version_class = CriteriaTemplateVersion
    repository_interface = CriteriaTemplateRepository
    instance_repository_interface = CriteriaRepository
    pre_instance_repository_interface = CriteriaPreInstanceRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: CriteriaTemplateAR
    ) -> CriteriaTemplate:
        cls = (
            CriteriaTemplateWithCount if item_ar.study_count != 0 else CriteriaTemplate
        )
        return cls.from_criteria_template_ar(item_ar)

    def _create_ar_from_input_values(
        self, template: CriteriaTemplateCreateInput
    ) -> CriteriaTemplateAR:
        template_vo, library_vo = self._create_template_vo(template)

        # Get indexings for templates from database
        (
            indications,
            categories,
            sub_categories,
            _,
            _,
            _,
            criteria_type,
        ) = self._get_indexings(template)

        # Process item to save
        item = CriteriaTemplateAR.from_input_values(
            author_id=self.author_id,
            template=template_vo,
            library=library_vo,
            generate_uid_callback=self.repository.generate_uid_callback,
            next_available_sequence_id_callback=self.repository.next_available_sequence_id,
            indications=indications,
            criteria_type=criteria_type,
            categories=categories,
            sub_categories=sub_categories,
        )

        return item

    @db.transaction
    def edit_draft(
        self, uid: str, template: CriteriaTemplateEditInput
    ) -> CriteriaTemplate:
        item = self.repository.find_by_uid(uid, for_update=True)

        self.authorize_user_defined_syntax_write(item.library.name)

        AlreadyExistsException.raise_if(
            self.repository.check_exists_by_name_in_library(
                name=template.name,
                library=item.library.name,
                type_uid=self.repository.get_template_type_uid(
                    self._repos.criteria_template_repository.root_class.nodes.get_or_none(
                        uid=uid
                    )
                ),
            )
            and template.name != item.name,
            field_value=template.name,
            field_name="Name",
        )

        template_vo = TemplateVO.from_input_values_2(
            template_name=template.name,
            guidance_text=template.guidance_text,
            parameter_name_exists_callback=self._parameter_name_exists,
        )

        item.edit_draft(
            author_id=self.author_id,
            change_description=template.change_description,
            template=template_vo,
        )

        # Save item
        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)
