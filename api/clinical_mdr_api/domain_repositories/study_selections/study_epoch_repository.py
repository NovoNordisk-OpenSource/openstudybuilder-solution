import datetime
from textwrap import dedent
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories._utils.helpers import (
    acquire_write_lock_study_value,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.generic_repository import (
    _manage_versioning_with_relations,
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
    LAG_TIME_EVENT_TYPES,
    StudyEpochHistoryVO,
    StudyEpochVO,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameWithConflictFlag,
)
from common import exceptions, queries
from common.auth.user import user
from common.config import settings
from common.exceptions import ValidationException
from common.telemetry import trace_calls


def get_ctlist_terms_by_name(
    codelist_names: list[str], effective_date: datetime.datetime | None = None
) -> dict[str, list[str]]:
    if not effective_date:
        ctterm_name_match = "(:CTTermNameRoot)-[:LATEST_FINAL]->(ctnv:CTTermNameValue) WHERE codelist_name_value.name IN $codelist_names"
    else:
        ctterm_name_match = """(ctnr:CTTermNameRoot)-[hv:HAS_VERSION]->(ctnv:CTTermNameValue)
            WHERE codelist_name_value.name IN $codelist_names AND 
                (hv.start_date<= datetime($effective_date) < datetime(hv.end_date)) OR (hv.end_date IS NULL AND (hv.start_date <= datetime($effective_date)))
        """
    # TODO use effective date on HAS_TERM relationship as well
    cypher_query = f"""
        MATCH (codelist_name_value:CTCodelistNameValue)<-[:LATEST_FINAL]-(:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]-
        (:CTCodelistRoot)-[:HAS_TERM]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->
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
    def __init__(self):
        self.author_id = user().id()

    def fetch_ctlist(
        self, codelist_names: list[str], effective_date: datetime.datetime | None = None
    ):
        return get_ctlist_terms_by_name(codelist_names, effective_date=effective_date)

    def get_allowed_configs(self, effective_date: datetime.datetime | None = None):
        if effective_date:
            subtype_name_value_match = """MATCH (term_subtype_name_root)-[hv:HAS_VERSION]->(term_subtype_name_value:CTTermNameValue)
                WHERE (hv.start_date<= datetime($effective_date) < hv.end_date) OR (hv.end_date IS NULL AND (hv.start_date <= datetime($effective_date)))
                AND ht.start_date <= datetime($effective_date) AND (ht.end_date IS NULL OR ht.end_date > datetime($effective_date))
            """
            type_name_value_match = """MATCH (term_type_name_root)-[hv_type:HAS_VERSION]->(term_type_name_value:CTTermNameValue)
                WHERE (hv_type.start_date<= datetime($effective_date) < hv_type.end_date) OR (hv_type.end_date IS NULL AND (hv_type.start_date <= datetime($effective_date)))
            """
        else:
            subtype_name_value_match = """MATCH (term_subtype_name_root:CTTermNameRoot)-[:LATEST_FINAL]->(term_subtype_name_value:CTTermNameValue)
                WHERE ht.end_date IS NULL
            """
            type_name_value_match = "MATCH (term_type_name_root)-[:LATEST_FINAL]->(term_type_name_value:CTTermNameValue)"

        cypher_query = f"""
            MATCH (:CTCodelistNameValue {{name: $code_list_name}})<-[:LATEST_FINAL]-(:CTCodelistNameRoot)<-[:HAS_NAME_ROOT]
            -(:CTCodelistRoot)-[ht:HAS_TERM]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(term_subtype_root:CTTermRoot)-[:HAS_NAME_ROOT]->(term_subtype_name_root:CTTermNameRoot)
            {subtype_name_value_match}
            MATCH (term_subtype_root)-[:HAS_PARENT_TYPE]->(term_type_root:CTTermRoot)-
            [:HAS_NAME_ROOT]->(term_type_name_root)
            {type_name_value_match}

            return term_subtype_root.uid, term_subtype_name_value.name, term_type_root.uid, term_type_name_value.name
        """
        items, _ = db.cypher_query(
            cypher_query,
            {
                "code_list_name": settings.study_epoch_subtype_name,
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
        MATCH (study_root:StudyRoot {uid:$study_uid})-[:LATEST]->(:StudyValue)-[:HAS_STUDY_EPOCH]->(study_epoch:StudyEpoch)-[:HAS_EPOCH_SUB_TYPE]->(CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-
        [:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:HAS_VERSION]->(:CTTermNameValue {name:$basic_epoch_name})
        WHERE NOT exists((:Delete)-[:BEFORE]->(study_epoch))
        return study_epoch.uid
        """
        basic_visit, _ = db.cypher_query(
            cypher_query,
            {"basic_epoch_name": settings.basic_epoch_name, "study_uid": study_uid},
        )
        return basic_visit[0][0] if len(basic_visit) > 0 else None

    @classmethod
    def _create_aggregate_root_instance_from_cypher_result(
        cls, input_dict: dict[str, Any], audit_trail: bool = False
    ) -> StudyEpochVO | StudyEpochHistoryVO:
        study_epoch_vo = StudyEpochVO(
            uid=input_dict.get("study_epoch").get("uid"),
            study_uid=input_dict["study_uid"],
            start_rule=input_dict.get("study_epoch").get("start_rule"),
            end_rule=input_dict.get("study_epoch").get("end_rule"),
            description=input_dict.get("study_epoch").get("description"),
            short_name=input_dict.get("study_epoch").get("short_name"),
            epoch=(
                SimpleCTTermNameWithConflictFlag(**input_dict["epoch_term"])
                if input_dict.get("epoch_term")
                else None
            ),
            subtype=(
                SimpleCTTermNameWithConflictFlag(**input_dict["epoch_subtype_term"])
                if input_dict.get("epoch_subtype_term")
                else None
            ),
            epoch_type=(
                SimpleCTTermNameWithConflictFlag(**input_dict["epoch_type_term"])
                if input_dict.get("epoch_type_term")
                else None
            ),
            order=input_dict.get("study_epoch").get("order"),
            status=StudyStatus(input_dict.get("study_epoch").get("status")),
            start_date=input_dict.get("study_action").get("date"),
            author_id=input_dict.get("study_action").get("author_id"),
            author_username=input_dict["author_username"],
            color_hash=input_dict.get("study_epoch").get("color_hash"),
            number_of_assigned_visits=input_dict["count_visits"],
            **cls._lag_times_from_cypher_result(input_dict),
        )
        if not audit_trail:
            return study_epoch_vo
        return cls.from_study_epoch_vo_to_history_vo(
            study_epoch_vo=study_epoch_vo, input_dict=input_dict
        )

    @staticmethod
    def _lag_times_from_cypher_result(input_dict: dict[str, Any]) -> dict[str, Any]:
        study_epoch = input_dict.get("study_epoch")
        lag_times: dict[str, Any] = {}
        for event_type in LAG_TIME_EVENT_TYPES:
            unit = input_dict.get(f"{event_type}_lag_time_unit") or {}
            lag_times[f"{event_type}_lag_time"] = study_epoch.get(
                f"{event_type}_lag_time"
            )
            lag_times[f"{event_type}_lag_time_unit_uid"] = unit.get("uid")
            lag_times[f"{event_type}_lag_time_unit_name"] = unit.get("name")
        return lag_times

    @staticmethod
    def _lag_times_from_vo(study_epoch_vo: StudyEpochVO) -> dict[str, Any]:
        return {
            f"{event_type}_lag_time{suffix}": getattr(
                study_epoch_vo, f"{event_type}_lag_time{suffix}"
            )
            for event_type in LAG_TIME_EVENT_TYPES
            for suffix in ("", "_unit_uid", "_unit_name")
        }

    @classmethod
    @trace_calls
    def _retrieve_concepts_from_cypher_res(
        cls, result_array, attribute_names, audit_trail: bool = False
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
                cls._create_aggregate_root_instance_from_cypher_result(
                    concept_dictionary, audit_trail=audit_trail
                )
            )
        return concept_ars

    @staticmethod
    @trace_calls
    def find_all_epochs_query(
        study_uid: str,
        study_value_version: str | None = None,
        study_epoch_uid: str | None = None,
        audit_trail: bool = False,
    ) -> tuple[str, dict[Any, Any]]:
        query = []
        params = {"study_uid": study_uid}

        if audit_trail:
            if study_epoch_uid:
                query.append(
                    "MATCH (study_epoch:StudyEpoch {uid: $study_epoch_uid})<-[:AFTER]-(study_action:StudyAction)<-[:AUDIT_TRAIL]-(study_root:StudyRoot {uid: $study_uid})"
                )
                params["study_epoch_uid"] = study_epoch_uid

            else:
                query.append(
                    "MATCH (study_epoch:StudyEpoch)<-[:AFTER]-(study_action:StudyAction)<-[:AUDIT_TRAIL]-(study_root:StudyRoot {uid: $study_uid})"
                )

        else:
            if study_value_version:
                query.append(
                    "MATCH (study_root:StudyRoot {uid: $study_uid})-[:HAS_VERSION{status: $study_status, version: $study_value_version}]->(study_value:StudyValue)"
                )
                params["study_value_version"] = study_value_version
                params["study_status"] = StudyStatus.RELEASED.value

            else:
                query.append(
                    "MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)"
                )

            query.append(queries.study_standard_version_ct_terms_datetime)

            if study_epoch_uid:
                query.append(
                    "MATCH (study_value)-[:HAS_STUDY_EPOCH]->(study_epoch:StudyEpoch {uid: $study_epoch_uid})<-[:AFTER]-(study_action:StudyAction)"
                )
                params["study_epoch_uid"] = study_epoch_uid

            else:
                query.append(
                    "MATCH (study_value)-[:HAS_STUDY_EPOCH]->(study_epoch:StudyEpoch)<-[:AFTER]-(study_action:StudyAction)"
                )

            if not study_value_version:
                query.append("WHERE NOT (study_epoch)-[:BEFORE]-()")

        query.append(dedent("""
            MATCH (study_epoch)-[:HAS_EPOCH]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(epoch_ct_term_root:CTTermRoot)
            MATCH (study_epoch)-[:HAS_EPOCH_SUB_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(epoch_subtype_ct_term_root:CTTermRoot)
            MATCH (study_epoch)-[:HAS_EPOCH_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(epoch_type_ct_term_root:CTTermRoot)
        """))

        if audit_trail:
            query.append(dedent("""
                WITH *,
                    {term_uid: epoch_ct_term_root.uid} AS epoch_term,
                    {term_uid: epoch_subtype_ct_term_root.uid} AS epoch_subtype_term,
                    {term_uid: epoch_type_ct_term_root.uid} AS epoch_type_term
            """))

        else:
            query.append(
                queries.ct_term_name_at_datetime.format(
                    root="epoch_ct_term_root", value="epoch_term"
                )
            )
            query.append(
                queries.ct_term_name_at_datetime.format(
                    root="epoch_subtype_ct_term_root", value="epoch_subtype_term"
                )
            )
            query.append(
                queries.ct_term_name_at_datetime.format(
                    root="epoch_type_ct_term_root", value="epoch_type_term"
                )
            )

        query.append(dedent("""
            WITH 
                study_root.uid AS study_uid,
                study_action,
                study_epoch,
                epoch_term,
                epoch_subtype_term,
                epoch_type_term,
                size([(study_epoch)-[:STUDY_EPOCH_HAS_STUDY_VISIT]->(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(study_value:StudyValue) | study_visit]) AS count_visits,
                head([(study_epoch)-[:HAS_AE_LAG_TIME_UNIT]->(unit_root:UnitDefinitionRoot)-[:LATEST]->(unit_value:UnitDefinitionValue) | {uid: unit_root.uid, name: unit_value.name}]) AS ae_lag_time_unit,
                head([(study_epoch)-[:HAS_HYPO_LAG_TIME_UNIT]->(unit_root:UnitDefinitionRoot)-[:LATEST]->(unit_value:UnitDefinitionValue) | {uid: unit_root.uid, name: unit_value.name}]) AS hypo_lag_time_unit,
                head([(study_epoch)-[:HAS_CE_LAG_TIME_UNIT]->(unit_root:UnitDefinitionRoot)-[:LATEST]->(unit_value:UnitDefinitionValue) | {uid: unit_root.uid, name: unit_value.name}]) AS ce_lag_time_unit,
                coalesce(head([(user:User)-[*0]-() WHERE user.user_id=study_action.author_id | user.username]), study_action.author_id) AS author_username
        """))
        if audit_trail:
            query.append(
                dedent(
                    """,head([(study_epoch:StudyEpoch)<-[:BEFORE]-(study_action_before:StudyAction) | study_action_before]) AS study_action_before,
                labels(study_action) AS change_type
                RETURN * ORDER BY study_epoch.uid, study_action.date DESC
            """
                )
            )
        else:
            query.append("RETURN * ORDER BY study_epoch.order")

        return "\n".join(query), params

    @classmethod
    @trace_calls
    def find_all_epochs_by_study(
        cls, study_uid: str, study_value_version: str | None = None
    ) -> list[StudyEpochVO]:
        query, params = cls.find_all_epochs_query(
            study_uid=study_uid, study_value_version=study_value_version
        )

        study_epochs, attributes_names = db.cypher_query(query=query, params=params)

        extracted_items = cls._retrieve_concepts_from_cypher_res(
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
            StudyEpoch.nodes.traverse(
                "has_design_cell__study_value",
                "has_after",
                "has_after__audit_trail",
            )
            .filter(study_value__latest_value__uid=study_uid, uid=epoch_uid)
            .resolve_subgraph()
        )
        return len(sdc_node) > 0

    @classmethod
    def find_by_uid(
        cls,
        uid: str,
        study_uid: str,
        study_value_version: str | None = None,
        for_update: bool = False,
    ) -> StudyEpochVO:
        if for_update:
            acquire_write_lock_study_value(uid=study_uid)
        query, params = cls.find_all_epochs_query(
            study_uid=study_uid,
            study_value_version=study_value_version,
            study_epoch_uid=uid,
        )
        study_epochs, attributes_names = db.cypher_query(query=query, params=params)
        extracted_items = cls._retrieve_concepts_from_cypher_res(
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

    @classmethod
    @trace_calls
    def get_all_versions(
        cls,
        study_uid,
        uid: str | None = None,
    ) -> list[StudyEpochHistoryVO]:
        query, params = cls.find_all_epochs_query(
            study_uid=study_uid, study_epoch_uid=uid, audit_trail=True
        )
        study_visits, attributes_names = db.cypher_query(query=query, params=params)
        extracted_items = cls._retrieve_concepts_from_cypher_res(
            study_visits, attributes_names, audit_trail=True
        )
        return extracted_items

    @staticmethod
    def from_study_epoch_vo_to_history_vo(
        study_epoch_vo: StudyEpochVO, input_dict: dict[str, Any]
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
            **StudyEpochRepository._lag_times_from_vo(study_epoch_vo),
        )

    def save(self, epoch: StudyEpochVO):
        # if exists
        if epoch.uid is not None:
            return self._update(epoch, create=False)
        # if has to be created
        return self._update(epoch, create=True)

    def _update(self, item: StudyEpochVO, create: bool = False):

        # Fetch nodes referenced by uids
        query = [
            "MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(latest_value:StudyValue)",
            "MATCH (epoch:CTTermRoot {uid: $epoch_uid})",
            "MATCH (epoch_subtype:CTTermRoot {uid: $epoch_subtype_uid})",
            "MATCH (epoch_type:CTTermRoot {uid: $epoch_type_uid})",
        ]
        params = {
            "study_uid": item.study_uid,
            "epoch_uid": item.epoch.term_uid,
            "epoch_subtype_uid": item.subtype.term_uid,
            "epoch_type_uid": item.epoch_type.term_uid,
        }
        returns = [
            "study_root",
            "latest_value",
            "epoch",
            "epoch_subtype",
            "epoch_type",
        ]

        for event_type in LAG_TIME_EVENT_TYPES:
            # A unit on its own says nothing, so clearing the value drops the unit too.
            # Without this, PATCHing only the value to null leaves the old unit attached,
            # because the partial-payload merge copies the unit uid back in.
            if getattr(item, f"{event_type}_lag_time") is None:
                setattr(item, f"{event_type}_lag_time_unit_uid", None)
            unit_uid = getattr(item, f"{event_type}_lag_time_unit_uid")
            if unit_uid:
                node_name = f"{event_type}_lag_time_unit"
                query.append(
                    f"MATCH ({node_name}:UnitDefinitionRoot {{uid: ${node_name}_uid}})"
                    f"-[:LATEST]->({node_name}_value:UnitDefinitionValue)"
                )
                params[f"{node_name}_uid"] = unit_uid
                returns.extend([node_name, f"{node_name}_value"])

        if not create and item.uid:
            query.append(
                "MATCH (latest_value)-[:HAS_STUDY_EPOCH]->(study_epoch:StudyEpoch {uid: $study_epoch_uid})"
            )
            params["study_epoch_uid"] = item.uid
            returns.append("study_epoch")

        query.append(f"RETURN {', '.join(returns)}")
        query_str = "\n".join(query)
        results, keys = db.cypher_query(query_str, params, resolve_objects=True)
        if len(results) != 1:
            raise exceptions.BusinessLogicException(
                msg=f"There should be one row returned with dependencies for StudyEpoch '{item.uid}'."
            )

        nodes = dict(zip(keys, results[0]))
        study_root: StudyRoot = nodes["study_root"]
        study_value: StudyValue = nodes["latest_value"]
        epoch: CTTermRoot = nodes["epoch"]
        epoch_subtype: CTTermRoot = nodes["epoch_subtype"]
        epoch_type: CTTermRoot = nodes["epoch_type"]
        previous_item: StudyEpoch | None = nodes.get("study_epoch")

        allow_removed_terms = not create

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
            ae_lag_time=item.ae_lag_time,
            hypo_lag_time=item.hypo_lag_time,
            ce_lag_time=item.ce_lag_time,
        )
        if item.uid is not None:
            new_study_epoch.uid = item.uid
        new_study_epoch.save()
        if item.uid is None:
            item.uid = new_study_epoch.uid

        # connect to lag time units
        for event_type in LAG_TIME_EVENT_TYPES:
            unit_node = nodes.get(f"{event_type}_lag_time_unit")
            unit_value = nodes.get(f"{event_type}_lag_time_unit_value")
            setattr(
                item,
                f"{event_type}_lag_time_unit_name",
                unit_value.name if unit_value is not None else None,
            )
            if unit_node is not None:
                getattr(new_study_epoch, f"has_{event_type}_lag_time_unit").connect(
                    unit_node
                )

        # connect to epoch subtype
        # ct_epoch_subtype = CTTermRoot.nodes.get(uid=item.subtype.term_uid)
        selected_epoch_subtype_node = (
            CTCodelistAttributesRepository().get_or_create_selected_term(
                epoch_subtype,
                codelist_submission_value=settings.study_epoch_subtype_cl_submval,
                catalogue_name=settings.sdtm_ct_catalogue_name,
                allow_removed_terms=allow_removed_terms,
            )
        )
        new_study_epoch.has_epoch_subtype.connect(selected_epoch_subtype_node)

        # connect to epoch type
        # ct_epoch_type = CTTermRoot.nodes.get(uid=item.epoch_type.term_uid)
        selected_epoch_type_node = (
            CTCodelistAttributesRepository().get_or_create_selected_term(
                epoch_type,
                codelist_submission_value=settings.study_epoch_type_cl_submval,
                catalogue_name=settings.sdtm_ct_catalogue_name,
                allow_removed_terms=allow_removed_terms,
            )
        )
        new_study_epoch.has_epoch_type.connect(selected_epoch_type_node)

        # connect to epoch
        # ct_epoch = CTTermRoot.nodes.get(uid=item.epoch.term_uid)
        selected_epoch_node = (
            CTCodelistAttributesRepository().get_or_create_selected_term(
                epoch,
                codelist_submission_value=settings.study_epoch_cl_submval,
                catalogue_name=settings.sdtm_ct_catalogue_name,
                allow_removed_terms=allow_removed_terms,
            )
        )
        new_study_epoch.has_epoch.connect(selected_epoch_node)

        if create:
            new_study_epoch.study_value.connect(study_value)
            _manage_versioning_with_relations(
                study_root=study_root,
                action_type=Create,
                before=None,
                after=new_study_epoch,
                author_id=self.author_id,
            )
        else:
            exclude_relations = (
                StudyEpoch.has_epoch_type,
                StudyEpoch.has_epoch_subtype,
                StudyEpoch.has_epoch,
                StudyEpoch.has_ae_lag_time_unit,
                StudyEpoch.has_hypo_lag_time_unit,
                StudyEpoch.has_ce_lag_time_unit,
            )
            # previous_item = study_value.has_study_epoch.get(uid=item.uid)
            if item.is_deleted:
                _manage_versioning_with_relations(
                    study_root=study_root,
                    action_type=Delete,
                    before=previous_item,
                    after=new_study_epoch,
                    exclude_relationships=exclude_relations,
                    author_id=self.author_id,
                )
            else:
                new_study_epoch.study_value.connect(study_value)
                _manage_versioning_with_relations(
                    study_root=study_root,
                    action_type=Edit,
                    before=previous_item,
                    after=new_study_epoch,
                    exclude_relationships=exclude_relations,
                    author_id=self.author_id,
                )

        return item
