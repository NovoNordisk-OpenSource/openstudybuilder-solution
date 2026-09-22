from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.syntax import (
    CriteriaPreInstanceRoot,
    CriteriaPreInstanceValue,
    CriteriaTemplateRoot,
)
from clinical_mdr_api.domain_repositories.syntax_instances.generic_syntax_instance_repository import (
    GenericSyntaxInstanceRepository,
)
from clinical_mdr_api.domains.syntax_pre_instances.criteria_pre_instance import (
    CriteriaPreInstanceAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameAndAttributes,
    SimpleTermAttributes,
    SimpleTermModel,
    SimpleTermName,
)
from clinical_mdr_api.utils import strip_html
from common.config import settings


class CriteriaPreInstanceRepository(
    GenericSyntaxInstanceRepository[CriteriaPreInstanceAR]
):
    root_class = CriteriaPreInstanceRoot
    value_class = CriteriaPreInstanceValue
    template_class = CriteriaTemplateRoot

    def _create_ar(
        self,
        root: CriteriaPreInstanceRoot,
        library: Library,
        relationship: VersionRelationship,
        value: CriteriaPreInstanceValue,
        study_count: int = 0,
        **kwargs,
    ):
        return CriteriaPreInstanceAR.from_repository_values(
            uid=root.uid,
            sequence_id=root.sequence_id,
            guidance_text=getattr(value, "guidance_text", None),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
            template=self.get_template_vo(root, value, kwargs["instance_template"]),
            criteria_type=SimpleCTTermNameAndAttributes(
                term_uid=kwargs["template_type"]["term_uid"],
                name=SimpleTermName(
                    sponsor_preferred_name=kwargs["template_type"]["name"],
                    sponsor_preferred_name_sentence_case=kwargs["template_type"][
                        "name_sentence_case"
                    ],
                ),
                attributes=SimpleTermAttributes(
                    nci_preferred_name=kwargs["template_type"]["preferred_term"],
                ),
            ),
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

    def _create(self, item: CriteriaPreInstanceAR) -> CriteriaPreInstanceAR:
        """
        This method calls the generic _create method, then extends it to add specific actions
        Specific actions are :
        * Attaching root node to indication nodes
        * Attaching root node to category nodes
        * Attaching root node to sub_category nodes
        """
        root, item = super()._create(item)

        for indication in item.indications or []:
            root.has_indication.connect(self._get_indication(indication.term_uid))

        for category in item.categories or []:
            selected_term_node = CTCodelistAttributesRepository().get_or_create_selected_term(
                self._get_category(category.term_uid),
                codelist_submission_value=settings.syntax_criteria_category_cl_submval,
                catalogue_name=settings.sdtm_ct_catalogue_name,
            )
            root.has_category.connect(selected_term_node)

        for sub_category in item.sub_categories or []:
            selected_term_node = CTCodelistAttributesRepository().get_or_create_selected_term(
                self._get_category(sub_category.term_uid),
                codelist_submission_value=settings.syntax_criteria_sub_category_cl_submval,
                catalogue_name=settings.sdtm_ct_catalogue_name,
            )
            root.has_subcategory.connect(selected_term_node)

        return item

    def _has_data_changed(self, ar: CriteriaPreInstanceAR, value: VersionValue) -> bool:
        return ar.name != value.name or ar.guidance_text != value.guidance_text

    def _get_or_create_value(
        self,
        root: CriteriaPreInstanceRoot,
        ar: CriteriaPreInstanceAR,
        force_new_value_node: bool = False,
    ) -> VersionValue:
        if not force_new_value_node:
            (
                has_version_rel,
                _,
                latest_draft_rel,
                latest_final_rel,
                latest_retired_rel,
            ) = self._get_version_relation_keys(root)
            for itm in has_version_rel.filter(
                name=ar.name, guidance_text=ar.guidance_text
            ):
                return itm

            latest_draft = latest_draft_rel.get_or_none()
            if latest_draft and not self._has_data_changed(ar, latest_draft):
                return latest_draft
            latest_final = latest_final_rel.get_or_none()
            if latest_final and not self._has_data_changed(ar, latest_final):
                return latest_final
            latest_retired = latest_retired_rel.get_or_none()
            if latest_retired and not self._has_data_changed(ar, latest_retired):
                return latest_retired

        new_value = self.value_class(
            name=ar.name, guidance_text=ar.guidance_text, name_plain=strip_html(ar.name)
        )

        self._db_save_node(new_value)

        return new_value
