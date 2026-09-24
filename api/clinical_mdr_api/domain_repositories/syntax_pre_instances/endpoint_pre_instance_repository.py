from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.syntax import (
    EndpointPreInstanceRoot,
    EndpointPreInstanceValue,
    EndpointTemplateRoot,
)
from clinical_mdr_api.domain_repositories.syntax_instances.generic_syntax_instance_repository import (
    GenericSyntaxInstanceRepository,
)
from clinical_mdr_api.domains.syntax_pre_instances.endpoint_pre_instance import (
    EndpointPreInstanceAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameAndAttributes,
    SimpleTermAttributes,
    SimpleTermModel,
    SimpleTermName,
)
from common.config import settings


class EndpointPreInstanceRepository(
    GenericSyntaxInstanceRepository[EndpointPreInstanceAR]
):
    root_class = EndpointPreInstanceRoot
    value_class = EndpointPreInstanceValue
    template_class = EndpointTemplateRoot

    def _create_ar(
        self,
        root: EndpointPreInstanceRoot,
        library: Library,
        relationship: VersionRelationship,
        value: EndpointPreInstanceValue,
        study_count: int = 0,
        **kwargs,
    ):
        return EndpointPreInstanceAR.from_repository_values(
            uid=root.uid,
            sequence_id=root.sequence_id,
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
            template=self.get_template_vo(root, value, kwargs["instance_template"]),
            indications=sorted(
                [
                    SimpleTermModel(
                        term_uid=indication["term_uid"], name=indication["name"]
                    )
                    for indication in kwargs["indications"]
                    if indication["term_uid"]
                ],
                key=lambda x: x.term_uid,
            ),
            categories=sorted(
                [
                    SimpleCTTermNameAndAttributes(
                        term_uid=category["term_uid"],
                        name=SimpleTermName(
                            sponsor_preferred_name=category["name"],
                            sponsor_preferred_name_sentence_case=category[
                                "name_sentence_case"
                            ],
                        ),
                        attributes=SimpleTermAttributes(
                            nci_preferred_name=category["preferred_term"],
                        ),
                    )
                    for category in kwargs["categories"]
                    if category["term_uid"]
                ],
                key=lambda x: x.term_uid,
            ),
            sub_categories=sorted(
                [
                    SimpleCTTermNameAndAttributes(
                        term_uid=subcategory["term_uid"],
                        name=SimpleTermName(
                            sponsor_preferred_name=subcategory["name"],
                            sponsor_preferred_name_sentence_case=subcategory[
                                "name_sentence_case"
                            ],
                        ),
                        attributes=SimpleTermAttributes(
                            nci_preferred_name=subcategory["preferred_term"],
                        ),
                    )
                    for subcategory in kwargs["subcategories"]
                    if subcategory["term_uid"]
                ],
                key=lambda x: x.term_uid,
            ),
            study_count=study_count,
        )

    def _create(self, item: EndpointPreInstanceAR) -> EndpointPreInstanceAR:
        """
        This method calls the generic _create method, then extends it to add specific actions
        Specific actions are :
        * Attaching root node to indication nodes
        * Attaching root node to category nodes
        * Attaching root node to sub_category nodes
        """
        root, item = super()._create(item)

        for indication in item.indications or []:
            if indication:
                root.has_indication.connect(self._get_indication(indication.term_uid))

        for category in item.categories or []:
            selected_term_node = CTCodelistAttributesRepository().get_or_create_selected_term(
                self._get_category(category.term_uid),
                codelist_submission_value=settings.syntax_endpoint_category_cl_submval,
                catalogue_name=settings.sdtm_ct_catalogue_name,
            )
            root.has_category.connect(selected_term_node)

        for sub_category in item.sub_categories or []:
            selected_term_node = CTCodelistAttributesRepository().get_or_create_selected_term(
                self._get_category(sub_category.term_uid),
                codelist_submission_value=settings.syntax_endpoint_sub_category_cl_submval,
                catalogue_name=settings.sdtm_ct_catalogue_name,
            )
            root.has_subcategory.connect(selected_term_node)

        return item
