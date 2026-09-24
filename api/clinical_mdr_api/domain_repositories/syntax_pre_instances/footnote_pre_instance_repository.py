from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.syntax import (
    FootnotePreInstanceRoot,
    FootnotePreInstanceValue,
    FootnoteTemplateRoot,
)
from clinical_mdr_api.domain_repositories.syntax_instances.generic_syntax_instance_repository import (
    GenericSyntaxInstanceRepository,
)
from clinical_mdr_api.domains.syntax_pre_instances.footnote_pre_instance import (
    FootnotePreInstanceAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameAndAttributes,
    SimpleTermAttributes,
    SimpleTermModel,
    SimpleTermName,
)
from clinical_mdr_api.models.generic_models import SimpleNameModel


class FootnotePreInstanceRepository(
    GenericSyntaxInstanceRepository[FootnotePreInstanceAR]
):
    root_class = FootnotePreInstanceRoot
    value_class = FootnotePreInstanceValue
    template_class = FootnoteTemplateRoot

    def _create_ar(
        self,
        root: FootnotePreInstanceRoot,
        library: Library,
        relationship: VersionRelationship,
        value: FootnotePreInstanceValue,
        study_count: int = 0,
        **kwargs,
    ):
        return FootnotePreInstanceAR.from_repository_values(
            uid=root.uid,
            sequence_id=root.sequence_id,
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
            template=self.get_template_vo(root, value, kwargs["instance_template"]),
            footnote_type=SimpleCTTermNameAndAttributes(
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
            activities=sorted(
                [
                    SimpleNameModel(
                        uid=activity["uid"],
                        name=activity["name"],
                        name_sentence_case=activity["name_sentence_case"],
                    )
                    for activity in kwargs["activities"]
                    if activity["uid"]
                ],
                key=lambda x: x.uid,
            ),
            activity_groups=sorted(
                [
                    SimpleNameModel(
                        uid=activity_group["uid"],
                        name=activity_group["name"],
                        name_sentence_case=activity_group["name_sentence_case"],
                    )
                    for activity_group in kwargs["activity_groups"]
                    if activity_group["uid"]
                ],
                key=lambda x: x.uid,
            ),
            activity_subgroups=sorted(
                [
                    SimpleNameModel(
                        uid=activity_subgroup["uid"],
                        name=activity_subgroup["name"],
                        name_sentence_case=activity_subgroup["name_sentence_case"],
                    )
                    for activity_subgroup in kwargs["activity_subgroups"]
                    if activity_subgroup["uid"]
                ],
                key=lambda x: x.uid,
            ),
            study_count=study_count,
        )

    def _create(self, item: FootnotePreInstanceAR) -> FootnotePreInstanceAR:
        """
        This method calls the generic _create method, then extends it to add specific actions
        Specific actions are :
        * Attaching root node to indication nodes
        """
        root, item = super()._create(item)

        for indication in item.indications or []:
            root.has_indication.connect(self._get_indication(indication.term_uid))

        for activity in item.activities or []:
            root.has_activity.connect(self._get_activity(activity.uid))

        for group in item.activity_groups or []:
            root.has_activity_group.connect(self._get_activity_group(group.uid))

        for group in item.activity_subgroups or []:
            root.has_activity_subgroup.connect(self._get_activity_subgroup(group.uid))

        return item
