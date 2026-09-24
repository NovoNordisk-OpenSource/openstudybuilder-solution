from neomodel import db

from clinical_mdr_api.domain_repositories.syntax_instances.footnote_repository import (
    FootnoteRepository,
)
from clinical_mdr_api.domain_repositories.syntax_pre_instances.footnote_pre_instance_repository import (
    FootnotePreInstanceRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.footnote_template_repository import (
    FootnoteTemplateRepository,
)
from clinical_mdr_api.domains.syntax_templates.footnote_template import (
    FootnoteTemplateAR,
)
from clinical_mdr_api.domains.syntax_templates.template import TemplateVO
from clinical_mdr_api.models.syntax_templates.footnote_template import (
    FootnoteTemplate,
    FootnoteTemplateCreateInput,
    FootnoteTemplateEditInput,
    FootnoteTemplateVersion,
    FootnoteTemplateWithCount,
)
from clinical_mdr_api.services.syntax_templates.generic_syntax_template_service import (
    GenericSyntaxTemplateService,
)
from common.exceptions import AlreadyExistsException


class FootnoteTemplateService(GenericSyntaxTemplateService[FootnoteTemplateAR]):
    aggregate_class = FootnoteTemplateAR
    version_class = FootnoteTemplateVersion
    repository_interface = FootnoteTemplateRepository
    instance_repository_interface = FootnoteRepository
    pre_instance_repository_interface = FootnotePreInstanceRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: FootnoteTemplateAR
    ) -> FootnoteTemplate:
        cls = (
            FootnoteTemplateWithCount if item_ar.study_count != 0 else FootnoteTemplate
        )
        return cls.from_footnote_template_ar(item_ar)

    def _create_ar_from_input_values(
        self, template: FootnoteTemplateCreateInput
    ) -> FootnoteTemplateAR:
        template_vo, library_vo = self._create_template_vo(template)

        # Get indexings for templates from database
        (
            indications,
            _,
            _,
            activities,
            activity_groups,
            activity_subgroups,
            footnote_type,
        ) = self._get_indexings(template)

        # Process item to save
        item = FootnoteTemplateAR.from_input_values(
            author_id=self.author_id,
            template=template_vo,
            library=library_vo,
            generate_uid_callback=self.repository.generate_uid_callback,
            next_available_sequence_id_callback=self.repository.next_available_sequence_id,
            indications=indications,
            activities=activities,
            activity_groups=activity_groups,
            activity_subgroups=activity_subgroups,
            footnote_type=footnote_type,
        )

        return item

    @db.transaction
    def edit_draft(
        self, uid: str, template: FootnoteTemplateEditInput
    ) -> FootnoteTemplate:
        item = self.repository.find_by_uid(uid, for_update=True)

        self.authorize_user_defined_syntax_write(item.library.name)

        AlreadyExistsException.raise_if(
            self.repository.check_exists_by_name_in_library(
                name=template.name,
                library=item.library.name,
                type_uid=self.repository.get_template_type_uid(
                    self._repos.footnote_template_repository.root_class.nodes.get_or_none(
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
