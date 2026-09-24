from neomodel import db

from clinical_mdr_api.domain_repositories.syntax_pre_instances.objective_pre_instance_repository import (
    ObjectivePreInstanceRepository,
)
from clinical_mdr_api.domains.syntax_pre_instances.objective_pre_instance import (
    ObjectivePreInstanceAR,
)
from clinical_mdr_api.models.syntax_pre_instances.objective_pre_instance import (
    ObjectivePreInstance,
    ObjectivePreInstanceVersion,
)
from clinical_mdr_api.services.syntax_instances.objectives import ObjectiveService


class ObjectivePreInstanceService(ObjectiveService[ObjectivePreInstanceAR]):
    aggregate_class = ObjectivePreInstanceAR
    repository_interface = ObjectivePreInstanceRepository
    version_class = ObjectivePreInstanceVersion
    template_uid_property = "objective_template_uid"

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ObjectivePreInstanceAR
    ) -> ObjectivePreInstance:
        return ObjectivePreInstance.from_objective_pre_instance_ar(item_ar)

    def create_ar_from_input_values(
        self,
        template,
        generate_uid_callback=None,
        study_uid: str | None = None,
        template_uid: str | None = None,
        include_study_endpoints: bool = False,
    ) -> ObjectivePreInstanceAR:
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
            categories,
            _,
            _,
            _,
            _,
            _,
        ) = self._get_indexings(template)

        item_ar._indications = indications
        item_ar._categories = categories
        item_ar._is_confirmatory_testing = template.is_confirmatory_testing

        return item_ar

    @db.transaction
    def create_new_version(self, uid: str) -> ObjectivePreInstance:
        item = self.repository.find_by_uid(uid, for_update=True)
        item._create_new_version(author_id=self.author_id)
        self.repository.save(item)
        return self._transform_aggregate_root_to_pydantic_model(item)
