import datetime

from neomodel import db

from clinical_mdr_api.domain_repositories.generic_repository import (
    manage_previous_connected_study_selection_relationships,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
)
from clinical_mdr_api.domain_repositories.models.study_epoch import StudyEpoch
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_epoch import (
    StudyEpochEpoch,
    StudyEpochHistoryVO,
    StudyEpochSubType,
    StudyEpochType,
    StudyEpochVO,
)
from common import config as settings
from common.exceptions import ValidationException


def get_ctlist_terms_by_name(
    codelist_names: str, effective_date: datetime.datetime | None = None
):
    if not effective_date:
        ctterm_name_match = "(:CTTermNameRoot)-[:LATEST_FINAL]->(ctnv:CTTermNameValue) WHERE codelist_name_value.name IN $codelist_names"
    else:
        ctterm_name_match = """(ctnr:CTTermNameRoot)-[hv:HAS_VERSION]->(ctnv:CTTermNameValue)
            WHERE codelist_name_value.name IN $codelist_names AND 
                (hv.start_date<= datetime($effective_date) < datetime(hv.end_date)) OR (hv.end_date IS NULL AND (hv.start_date <= datetime($effective_date)))
        """
    cypher_query = f"""
        MATCH (codelist_name_value:CTCodelistNameValue)<-[:LATEST_FINAL]-(:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-
        (:CTCodelistRoot)-[:HAS_TERM]->
        (tr:CTTermRoot)-[:HAS_NAME_ROOT]->
        {ctterm_name_match}
        WITH tr.uid as term_uid, collect(codelist_name_value.name) as codelist_names
        RETURN term_uid, codelist_names
        """
    items, _ = db.cypher_query(
        cypher_query,
        {
            "codelist_names": codelist_names,
            "effective_date": (
                effective_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                if effective_date
                else None
            ),
        },
    )
    return {a[0]: a[1] for a in items}


class StudyEpochRepository:
    def __init__(self, author_id: str):
        self.author_id = author_id

    def fetch_ctlist(
        self, codelist_names: str, effective_date: datetime.datetime | None = None
    ):
        return get_ctlist_terms_by_name(codelist_names, effective_date=effective_date)

    def get_allowed_configs(self, effective_date: datetime.datetime | None = None):
        if effective_date:
            subtype_name_value_match = """MATCH (term_subtype_name_root)-[hv:HAS_VERSION]->(term_subtype_name_value:CTTermNameValue)
                WHERE (hv.start_date<= datetime($effective_date) < hv.end_date) OR (hv.end_date IS NULL AND (hv.start_date <= datetime($effective_date)))
            """
            type_name_value_match = """MATCH (term_type_name_root)-[hv_type:HAS_VERSION]->(term_type_name_value:CTTermNameValue)
                WHERE (hv_type.start_date<= datetime($effective_date) < hv_type.end_date) OR (hv_type.end_date IS NULL AND (hv_type.start_date <= datetime($effective_date)))
            """
        else:
            subtype_name_value_match = "MATCH (term_subtype_name_root:CTTermNameRoot)-[:LATEST_FINAL]->(term_subtype_name_value:CTTermNameValue)"
            type_name_value_match = "MATCH (term_type_name_root)-[:LATEST_FINAL]->(term_type_name_value:CTTermNameValue)"

        cypher_query = f"""
            MATCH (:CTCodelistNameValue {{name: $code_list_name}})<-[:LATEST_FINAL]-(:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]
            -(:CTCodelistRoot)-[:HAS_TERM]->(term_subtype_root:CTTermRoot)-[:HAS_NAME_ROOT]->(term_subtype_name_root:CTTermNameRoot)
            {subtype_name_value_match}
            MATCH (term_subtype_root)-[:HAS_PARENT_TYPE]->(term_type_root:CTTermRoot)-
            [:HAS_NAME_ROOT]->(term_type_name_root)
            {type_name_value_match}

            return term_subtype_root.uid, term_subtype_name_value.name, term_type_root.uid, term_type_name_value.name
        """
        items, _ = db.cypher_query(
            cypher_query,
            {
                "code_list_name": settings.STUDY_EPOCH_SUBTYPE_NAME,
                "effective_date": (
                    effective_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                    if effective_date
                    else None
                ),
            },
        )
        return items

    def get_basic_epoch(self, study_uid: str) -> str | None:
        cypher_query = """
        MATCH (study_root:StudyRoot {uid:$study_uid})-[:LATEST]->(:StudyValue)-[:HAS_STUDY_EPOCH]->(study_epoch:StudyEpoch)-[:HAS_EPOCH_SUB_TYPE]->(:CTTermRoot)-
        [:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:HAS_VERSION]->(:CTTermNameValue {name:$basic_epoch_name})
        WHERE NOT exists((:Delete)-[:BEFORE]->(study_epoch))
        return study_epoch.uid
        """
        basic_visit, _ = db.cypher_query(
            cypher_query,
            {"basic_epoch_name": settings.BASIC_EPOCH_NAME, "study_uid": study_uid},
        )
        return basic_visit[0][0] if len(basic_visit) > 0 else None

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict, audit_trail: bool = False
    ) -> StudyEpochVO | StudyEpochHistoryVO:
        study_epoch_vo = StudyEpochVO(
            uid=input_dict.get("study_epoch").get("uid"),
            study_uid=input_dict.get("study_uid"),
            start_rule=input_dict.get("study_epoch").get("start_rule"),
            end_rule=input_dict.get("study_epoch").get("end_rule"),
            description=input_dict.get("study_epoch").get("description"),
            epoch=StudyEpochEpoch[input_dict.get("epoch_ct_term_uid")],
            subtype=StudyEpochSubType[input_dict.get("epoch_subtype_ct_term_uid")],
            epoch_type=StudyEpochType[input_dict.get("epoch_type_ct_term_uid")],
            order=input_dict.get("study_epoch").get("order"),
            status=StudyStatus(input_dict.get("study_epoch").get("status")),
            start_date=input_dict.get("study_action").get("date"),
            author_id=input_dict.get("study_action").get("author_id"),
            author_username=input_dict.get("author_username"),
            color_hash=input_dict.get("study_epoch").get("color_hash"),
            number_of_assigned_visits=input_dict.get("count_vists"),
        )
        if not audit_trail:
            return study_epoch_vo
        return self.from_study_epoch_vo_to_history_vo(
            study_epoch_vo=study_epoch_vo, input_dict=input_dict
        )

    def _retrieve_concepts_from_cypher_res(
        self, result_array, attribute_names, audit_trail: bool = False
    ) -> list[StudyEpochVO]:
        """
        Method maps the result of the cypher query into real aggregate objects.
        :param result_array:
        :param attribute_names:
        :return Iterable[_AggregateRootType]:
        """
        concept_ars = []
        for concept in result_array:
            concept_dictionary = {}
            for concept_property, attribute_name in zip(concept, attribute_names):
                concept_dictionary[attribute_name] = concept_property
            concept_ars.append(
                self._create_aggregate_root_instance_from_cypher_result(
                    concept_dictionary, audit_trail=audit_trail
                )
            )
        return concept_ars

    def find_all_epochs_query(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        study_epoch_uid: str | None = None,
        audit_trail: bool = False,
    ) -> tuple[str, dict]:
        params = {}
        if not audit_trail:
            if study_value_version:
                query = "MATCH (study_root:StudyRoot {uid: $study_uid})-[:HAS_VERSION{status: $study_status, version: $study_value_version}]->(study_value:StudyValue)"
                params["study_value_version"] = study_value_version
                params["study_status"] = StudyStatus.RELEASED.value
            else:
                query = "MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)"
            params["study_uid"] = study_uid
            if study_epoch_uid:
                query += "MATCH (study_value)-[:HAS_STUDY_EPOCH]->(study_epoch:StudyEpoch {uid: $study_epoch_uid})<-[:AFTER]-(study_action:StudyAction)"
                params["study_epoch_uid"] = study_epoch_uid
            else:
                query += "MATCH (study_value)-[:HAS_STUDY_EPOCH]->(study_epoch:StudyEpoch)<-[:AFTER]-(study_action:StudyAction)"
        else:
            if study_epoch_uid:
                query = "MATCH (study_epoch:StudyEpoch {uid: $study_epoch_uid})<-[:AFTER]-(study_action:StudyAction)<-[:AUDIT_TRAIL]-(study_root:StudyRoot)"
                params["study_epoch_uid"] = study_epoch_uid
            else:
                query = "MATCH (study_epoch:StudyEpoch)<-[:AFTER]-(study_action:StudyAction)<-[:AUDIT_TRAIL]-(study_root:StudyRoot {uid:$study_uid})"
                params["study_uid"] = study_uid
        if not (study_value_version or audit_trail):
            query += "WHERE NOT (study_epoch)-[:BEFORE]-()"

        query += """
            WITH 
                study_root.uid AS study_uid,
                study_action,
                study_epoch,
                head([(study_epoch)-[:HAS_EPOCH]->(epoch_ct_term_root:CTTermRoot) | epoch_ct_term_root.uid]) AS epoch_ct_term_uid,
                head([(study_epoch)-[:HAS_EPOCH_SUB_TYPE]->(epoch_subtype_ct_term_root:CTTermRoot) | epoch_subtype_ct_term_root.uid]) AS epoch_subtype_ct_term_uid,
                head([(study_epoch)-[:HAS_EPOCH_TYPE]->(epoch_type_ct_term_root:CTTermRoot) | epoch_type_ct_term_root.uid]) AS epoch_type_ct_term_uid,
                size([(study_epoch)-[:STUDY_EPOCH_HAS_STUDY_VISIT]->(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(:StudyValue) | study_visit]) AS count_vists,
                coalesce(head([(user:User)-[*0]-() WHERE user.user_id=study_action.author_id | user.username]), study_action.author_id) AS author_username
        """
        if audit_trail:
            query += """,head([(study_epoch:StudyEpoch)<-[:BEFORE]-(study_action_before:StudyAction) | study_action_before]) AS study_action_before,
                labels(study_action) AS change_type
                RETURN * ORDER BY study_epoch.uid, study_action.date DESC
            """
        else:
            query += "RETURN * ORDER BY study_epoch.order"
        return query, params

    def find_all_epochs_by_study(
        self, study_uid: str, study_value_version: str | None = None
    ) -> list[StudyEpochVO]:
        query, params = self.find_all_epochs_query(
            study_uid=study_uid, study_value_version=study_value_version
        )

        study_epochs, attributes_names = db.cypher_query(query=query, params=params)

        extracted_items = self._retrieve_concepts_from_cypher_res(
            study_epochs, attributes_names
        )
        return extracted_items

    def epoch_specific_has_connected_design_cell(
        self, study_uid: str, epoch_uid: str
    ) -> bool:
        """
        Returns True if StudyEpoch with specified uid has connected at least one StudyDesignCell.
        :return:
        """

        sdc_node = (
            StudyEpoch.nodes.fetch_relations(
                "has_design_cell__study_value",
                "has_after",
                "has_after__audit_trail",
            )
            .filter(study_value__latest_value__uid=study_uid, uid=epoch_uid)
            .resolve_subgraph()
        )
        return len(sdc_node) > 0

    def find_by_uid(
        self, uid: str, study_uid: str, study_value_version: str | None = None
    ) -> StudyEpochVO:
        query, params = self.find_all_epochs_query(
            study_uid=study_uid,
            study_value_version=study_value_version,
            study_epoch_uid=uid,
        )
        study_epochs, attributes_names = db.cypher_query(query=query, params=params)
        extracted_items = self._retrieve_concepts_from_cypher_res(
            study_epochs, attributes_names
        )
        ValidationException.raise_if(
            len(extracted_items) > 1,
            msg=f"Found more than one StudyEpoch node with UID '{uid}'.",
        )
        ValidationException.raise_if(
            len(extracted_items) == 0,
            msg=f"StudyEpoch with UID '{uid}' doesn't exist.",
        )
        return extracted_items[0]

    def get_all_versions(
        self,
        study_uid,
        uid: str | None = None,
    ) -> list[StudyEpochHistoryVO]:
        query, params = self.find_all_epochs_query(
            study_uid=study_uid, study_epoch_uid=uid, audit_trail=True
        )
        study_visits, attributes_names = db.cypher_query(query=query, params=params)
        extracted_items = self._retrieve_concepts_from_cypher_res(
            study_visits, attributes_names, audit_trail=True
        )
        return extracted_items

    def from_study_epoch_vo_to_history_vo(
        self, study_epoch_vo: StudyEpochVO, input_dict: dict
    ) -> StudyEpochHistoryVO:
        change_type = input_dict.get("change_type")
        for action in change_type:
            if "StudyAction" not in action:
                change_type = action
        study_action_before = input_dict.get("study_action_before") or {}

        return StudyEpochHistoryVO(
            uid=study_epoch_vo.uid,
            study_uid=study_epoch_vo.study_uid,
            start_rule=study_epoch_vo.start_rule,
            end_rule=study_epoch_vo.end_rule,
            description=study_epoch_vo.description,
            epoch=study_epoch_vo.epoch,
            subtype=study_epoch_vo.subtype,
            epoch_type=study_epoch_vo.epoch_type,
            order=study_epoch_vo.order,
            status=study_epoch_vo.status,
            start_date=study_epoch_vo.start_date,
            author_id=study_epoch_vo.author_id,
            author_username=study_epoch_vo.author_username,
            color_hash=study_epoch_vo.color_hash,
            number_of_assigned_visits=study_epoch_vo.number_of_assigned_visits,
            change_type=change_type,
            end_date=study_action_before.get("date"),
        )

    def save(self, epoch: StudyEpochVO):
        # if exists
        if epoch.uid is not None:
            return self._update(epoch, create=False)
        # if has to be created
        return self._update(epoch, create=True)

    def _update(self, item: StudyEpochVO, create: bool = False):
        study_root = StudyRoot.nodes.get(uid=item.study_uid)
        study_value: StudyValue = study_root.latest_value.get_or_none()
        ValidationException.raise_if(
            study_value is None, msg="Study doesn't have draft version."
        )
        if not create:
            previous_item = study_value.has_study_epoch.get(uid=item.uid)
        new_study_epoch = StudyEpoch(
            uid=item.uid,
            accepted_version=item.accepted_version,
            order=item.order,
            name=item.name,
            short_name=item.short_name,
            description=item.description,
            start_rule=item.start_rule,
            end_rule=item.end_rule,
            color_hash=item.color_hash,
            status=item.status.value,
        )
        if item.uid is not None:
            new_study_epoch.uid = item.uid
        new_study_epoch.save()
        if item.uid is None:
            item.uid = new_study_epoch.uid
        ct_epoch_subtype = CTTermRoot.nodes.get(uid=item.subtype.term_uid)
        new_study_epoch.has_epoch_subtype.connect(ct_epoch_subtype)
        ct_epoch_type = CTTermRoot.nodes.get(uid=item.epoch_type.term_uid)
        new_study_epoch.has_epoch_type.connect(ct_epoch_type)
        ct_epoch = CTTermRoot.nodes.get(uid=item.epoch.term_uid)
        new_study_epoch.has_epoch.connect(ct_epoch)
        if create:
            new_study_epoch.study_value.connect(study_value)
            self.manage_versioning_create(
                study_root=study_root, item=item, new_item=new_study_epoch
            )
        else:
            if item.is_deleted:
                self.manage_versioning_delete(
                    study_root=study_root,
                    item=item,
                    # pylint: disable=possibly-used-before-assignment
                    previous_item=previous_item,
                    new_item=new_study_epoch,
                )
            else:
                new_study_epoch.study_value.connect(study_value)
                self.manage_versioning_update(
                    study_root=study_root,
                    item=item,
                    previous_item=previous_item,
                    new_item=new_study_epoch,
                )
            manage_previous_connected_study_selection_relationships(
                previous_item=previous_item,
                study_value_node=study_value,
                new_item=new_study_epoch,
                exclude_study_selection_relationships=[],
            )

        return item

    def manage_versioning_create(
        self, study_root: StudyRoot, item: StudyEpochVO, new_item: StudyEpoch
    ):
        action = Create(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=item.status.value,
            author_id=item.author_id,
        )
        action.save()
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)

    def manage_versioning_update(
        self,
        study_root: StudyRoot,
        item: StudyEpochVO,
        previous_item: StudyEpoch,
        new_item: StudyEpoch,
    ):
        action = Edit(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=item.status.value,
            author_id=item.author_id,
        )
        action.save()
        action.has_before.connect(previous_item)
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)

    def manage_versioning_delete(
        self,
        study_root: StudyRoot,
        item: StudyEpochVO,
        previous_item: StudyEpoch,
        new_item: StudyEpoch,
    ):
        action = Delete(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=item.status.value,
            author_id=item.author_id,
        )
        action.save()
        action.has_before.connect(previous_item)
        action.has_after.connect(new_item)
        study_root.audit_trail.connect(action)
