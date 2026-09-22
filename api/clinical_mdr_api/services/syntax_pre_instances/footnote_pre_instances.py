from neomodel import db

from clinical_mdr_api.domain_repositories.syntax_pre_instances.footnote_pre_instance_repository import (
    FootnotePreInstanceRepository,
)
from clinical_mdr_api.domains.syntax_pre_instances.footnote_pre_instance import (
    FootnotePreInstanceAR,
)
from clinical_mdr_api.models.syntax_pre_instances.footnote_pre_instance import (
    FootnotePreInstance,
    FootnotePreInstanceVersion,
)
from clinical_mdr_api.services.syntax_instances.footnotes import FootnoteService


class FootnotePreInstanceService(FootnoteService[FootnotePreInstanceAR]):
    aggregate_class = FootnotePreInstanceAR
    repository_interface = FootnotePreInstanceRepository
    version_class = FootnotePreInstanceVersion
    template_uid_property = "footnote_template_uid"

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: FootnotePreInstanceAR
    ) -> FootnotePreInstance:
        return FootnotePreInstance.from_footnote_pre_instance_ar(item_ar)

    def create_ar_from_input_values(
        self,
        template,
        generate_uid_callback=None,
        study_uid: str | None = None,
        template_uid: str | None = None,
        include_study_endpoints: bool = False,
    ) -> FootnotePreInstanceAR:
        item_ar = super().create_ar_from_input_values(
            template=template,
            generate_uid_callback=generate_uid_callback,
            next_available_sequence_id_callback=self.repository.next_available_sequence_id,
            study_uid=study_uid,
            template_uid=template_uid,
            include_study_endpoints=include_study_endpoints,
        )

        (
            indications,
            _,
            _,
            activities,
            activity_groups,
            activity_subgroups,
            template_type,
        ) = self._get_indexings(
            template,
            self.repository.get_template_type_uid(
                self._repos.footnote_template_repository.root_class.nodes.get_or_none(
                    uid=template_uid
                )
            ),
        )

        item_ar._type = template_type
        item_ar._indications = indications
        item_ar._activities = activities
        item_ar._activity_groups = activity_groups
        item_ar._activity_subgroups = activity_subgroups

        return item_ar

    @db.transaction
    def create_new_version(self, uid: str) -> FootnotePreInstance:
        item = self.repository.find_by_uid(uid, for_update=True)
        item._create_new_version(author_id=self.author_id)
        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)
