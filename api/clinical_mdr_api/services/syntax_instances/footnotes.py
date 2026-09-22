from clinical_mdr_api.domain_repositories.syntax_instances.footnote_repository import (
    FootnoteRepository,
)
from clinical_mdr_api.domain_repositories.syntax_pre_instances.footnote_pre_instance_repository import (
    FootnotePreInstanceRepository,
)
from clinical_mdr_api.domain_repositories.syntax_templates.footnote_template_repository import (
    FootnoteTemplateRepository,
)
from clinical_mdr_api.domains.syntax_instances.footnote import FootnoteAR
from clinical_mdr_api.domains.syntax_pre_instances.footnote_pre_instance import (
    FootnotePreInstanceAR,
)
from clinical_mdr_api.models.syntax_instances.footnote import (
    Footnote,
    FootnoteVersion,
    FootnoteWithType,
)
from clinical_mdr_api.models.syntax_pre_instances.footnote_pre_instance import (
    FootnotePreInstanceVersion,
)
from clinical_mdr_api.services.syntax_instances.generic_syntax_instance_service import (
    GenericSyntaxInstanceService,
    _AggregateRootType,
)


class FootnoteService(GenericSyntaxInstanceService[FootnoteAR | _AggregateRootType]):
    aggregate_class: type[FootnoteAR] | type[FootnotePreInstanceAR] = FootnoteAR
    repository_interface: (
        type[FootnoteRepository] | type[FootnotePreInstanceRepository]
    ) = FootnoteRepository
    template_repository_interface = FootnoteTemplateRepository
    version_class: type[FootnoteVersion] | type[FootnotePreInstanceVersion] = (
        FootnoteVersion
    )
    template_uid_property = "footnote_template_uid"

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: FootnoteAR
    ) -> Footnote:
        return FootnoteWithType.from_footnote_ar(
            item_ar,
            syntax_template_node=self._repos.footnote_template_repository.root_class.nodes.get_or_none(
                uid=item_ar.template_uid
            ),
            get_footnote_type_name=self._repos.ct_term_name_repository.get_syntax_template_type,
            get_footnote_type_attributes=self._repos.ct_term_attributes_repository.get_syntax_template_type,
        )
