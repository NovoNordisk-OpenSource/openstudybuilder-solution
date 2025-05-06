import abc
import datetime
from typing import Generic, TypeVar

from neomodel import db

from clinical_mdr_api import utils
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
    StudyAction,
)
from clinical_mdr_api.domain_repositories.models.study_selections import StudySelection
from clinical_mdr_api.domains.study_selections.study_selection_base import (
    StudySelectionBaseAR,
    StudySelectionBaseVO,
)
from common.utils import convert_to_datetime, validate_max_skip_clause

_AggregateRootType = TypeVar("_AggregateRootType")


class StudySelectionActivityBaseRepository(Generic[_AggregateRootType], abc.ABC):
    _aggregate_root_type: StudySelectionBaseAR

    @staticmethod
    def _acquire_write_lock_study_value(uid: str) -> None:
        db.cypher_query(
            """
             MATCH (sr:StudyRoot {uid: $uid})
             REMOVE sr.__WRITE_LOCK__
             RETURN true
            """,
            {"uid": uid},
        )

    @abc.abstractmethod
    def _create_value_object_from_repository(self, selection: dict, acv: bool):
        raise NotImplementedError

    @abc.abstractmethod
    def _additional_match(self):
        raise NotImplementedError

    @abc.abstractmethod
    def _filter_clause(
        self,
        query_parameters: dict,
        **kwargs,
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def _return_clause(self):
        raise NotImplementedError

    @abc.abstractmethod
    def generate_uid(self) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def get_selection_history(
        self, selection: dict, change_type: str, end_date: datetime
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def get_audit_trail_query(self, study_selection_uid: str):
        raise NotImplementedError

    @abc.abstractmethod
    def get_study_selection_node_from_latest_study_value(
        self, study_value: StudyValue, study_selection: StudySelection
    ):
        raise NotImplementedError

    @abc.abstractmethod
    def _add_new_selection(
        self,
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionBaseVO,
        audit_node: StudyAction,
        last_study_selection_node: StudySelection,
        for_deletion: bool = False,
    ):
        raise NotImplementedError

    def _versioning_query(self):
        return """
        WITH DISTINCT *
            CALL {
                WITH ar, av
                MATCH (ar)-[hv:HAS_VERSION]-(av)
                WHERE hv.status in ['Final', 'Retired']
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.end_date ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) as hv_ver
            }
        """

    def _order_by_query(self):
        return """
            WITH DISTINCT *
            ORDER BY sa.order ASC
            MATCH (sa)<-[:AFTER]-(sac:StudyAction)
        """

    def _retrieves_all_data(
        self,
        study_uids: str | list[str] | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        study_value_version: str | None = None,
        **kwargs,
    ) -> tuple[_AggregateRootType]:
        query_parameters = {}
        if study_uids:
            if isinstance(study_uids, str):
                study_uid_statement = "{uid: $uids}"
            else:
                study_uid_statement = "WHERE sr.uid IN $uids"
            if study_value_version:
                query = f"""
                    MATCH (sr:StudyRoot {study_uid_statement})-[l:HAS_VERSION{{status:'RELEASED', version:$study_value_version}}]->(sv:StudyValue)
                    """
                query_parameters["study_value_version"] = study_value_version
                query_parameters["uids"] = study_uids
            else:
                query = f"MATCH (sr:StudyRoot {study_uid_statement})-[l:LATEST]->(sv:StudyValue)"
                query_parameters["uids"] = study_uids
        else:
            if study_value_version:
                query = "MATCH (sr:StudyRoot)-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]->(sv:StudyValue)"
                query_parameters["study_value_version"] = study_value_version
            else:
                query = "MATCH (sr:StudyRoot)-[l:LATEST]->(sv:StudyValue)"

        # Add project related filters if applicable
        if project_name is not None or project_number is not None:
            query += (
                "-[:HAS_PROJECT]->(:StudyProjectField)<-[:HAS_FIELD]-(proj:Project)"
            )
            filter_list = []
            if project_name is not None:
                filter_list.append("proj.name=$project_name")
                query_parameters["project_name"] = project_name
            if project_number is not None:
                filter_list.append("proj.project_number=$project_number")
                query_parameters["project_number"] = project_number
            query += " WHERE "
            query += " AND ".join(filter_list)

        # Then, match other things for instance Activity
        query += self._additional_match()

        # Filter on extra parameters, for instance ActivityGroupNames
        query += self._filter_clause(query_parameters=query_parameters, **kwargs)
        query += self._versioning_query()
        query += self._order_by_query()
        query += self._return_clause()
        all_activity_selections = db.cypher_query(query, query_parameters)
        all_selections = []
        for selection in utils.db_result_to_list(all_activity_selections):
            acv = selection.get("accepted_version", False)
            if acv is None:
                acv = False
            selection_vo = self._create_value_object_from_repository(
                selection=selection, acv=acv
            )
            all_selections.append(selection_vo)
        return tuple(all_selections)

    def find_all(
        self,
        project_name: str | None = None,
        project_number: str | None = None,
        study_uids: list[str] | None = None,
        **kwargs,
    ) -> list[StudySelectionBaseAR]:
        """
        Finds all the selected study activities for all studies, and create the aggregate
        :return: List of StudySelectionActivityAR, potentially empty
        """
        all_selections = self._retrieves_all_data(
            project_name=project_name,
            project_number=project_number,
            study_uids=study_uids,
            **kwargs,
        )
        # Create a dictionary, with study_uid as key, and list of selections as value
        selection_aggregate_dict = {}
        selection_aggregates = []
        for selection in all_selections:
            if selection.study_uid in selection_aggregate_dict:
                selection_aggregate_dict[selection.study_uid].append(selection)
            else:
                selection_aggregate_dict[selection.study_uid] = [selection]
        # Then, create the list of AR from the dictionary
        for study_uid, selections in selection_aggregate_dict.items():
            selection_aggregates.append(
                self._aggregate_root_type.from_repository_values(
                    study_uid=study_uid, study_objects_selection=selections
                )
            )
        return selection_aggregates

    def find_by_study(
        self,
        study_uid: str,
        for_update: bool = False,
        study_value_version: str | None = None,
        **kwargs,
    ) -> StudySelectionBaseAR | None:
        if for_update:
            self._acquire_write_lock_study_value(study_uid)
        all_selections = self._retrieves_all_data(
            study_uid,
            study_value_version=study_value_version,
            **kwargs,
        )
        selection_aggregate = self._aggregate_root_type.from_repository_values(
            study_uid=study_uid, study_objects_selection=all_selections
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def _get_audit_node(
        self, study_selection: _AggregateRootType, study_selection_uid: str
    ):
        if not any(
            item.study_selection_uid == study_selection_uid
            for item in study_selection.study_objects_selection
        ):
            return Delete()

        if any(
            item.study_selection_uid == study_selection_uid
            for item in study_selection.repository_closure_data
        ) or (
            study_selection.closure_from_other_ar
            and study_selection_uid
            == study_selection.closure_from_other_ar.study_selection_uid
        ):
            return Edit()
        return Create()

    def is_repository_based_on_ordered_selection(self):
        return True

    def _get_audit_trail_nodes_to_reference(
        self,
        study_root_node: StudyRoot,
        latest_study_value_node: StudyValue,
        author_id: str,
        study_activity: StudySelectionBaseVO,
        study_selection: StudySelectionBaseAR,
    ):
        last_study_selection_node = (
            self.get_study_selection_node_from_latest_study_value(
                study_value=latest_study_value_node, study_selection=study_activity
            )
        )

        audit_node = self._get_audit_node(
            study_selection, study_activity.study_selection_uid
        )
        audit_node = self._set_before_audit_info(
            last_study_selection_node, audit_node, study_root_node, author_id
        )
        return audit_node, last_study_selection_node

    def save(
        self,
        study_selection: StudySelectionBaseAR,
        author_id: str,
        make_order_check=True,
    ) -> None:
        assert study_selection.repository_closure_data is not None
        # get the closure_data
        closure_data = study_selection.repository_closure_data
        closure_data_length = len(closure_data)

        # getting the latest study value node
        study_root_node: StudyRoot = StudyRoot.nodes.get(uid=study_selection.study_uid)
        latest_study_value_node: StudyValue = study_root_node.latest_value.get_or_none()

        # process new/changed/deleted elements for each activity
        selections_to_remove = []
        selections_to_add = []

        # check if object is removed from the selection list - delete has been called
        if closure_data_length > len(study_selection.study_objects_selection):
            # remove the last item from old list, as there will no longer be any study activity with that high order
            if self.is_repository_based_on_ordered_selection():
                selections_to_remove.append((len(closure_data), closure_data[-1]))
            else:
                for order, closure_item in enumerate(closure_data, start=1):
                    if closure_item not in study_selection.study_objects_selection:
                        selections_to_remove.append((order, closure_item))

        # loop through new data - start=1 as order starts at 1 not at 0 and find what needs to be removed and added
        for order, selection in enumerate(
            study_selection.study_objects_selection, start=1
        ):
            # check whether something new is added
            if closure_data_length > order - 1:
                # check if anything has changed
                if selection is not closure_data[order - 1]:
                    # don't modify the item if the change is the order change,
                    # if the item is actually changed (the uid is the same) we should modify it
                    if (
                        self.is_repository_based_on_ordered_selection()
                        or selection.study_selection_uid
                        == closure_data[order - 1].study_selection_uid
                    ):
                        # update the selection by removing the old if the old exists, and adding new selection
                        selections_to_remove.append((order, closure_data[order - 1]))
                        selections_to_add.append((order, selection))
            else:
                # else something new have been added
                selections_to_add.append((order, selection))

        # audit trail nodes dictionary, holds the new nodes created for the audit trail
        audit_trail_nodes = {}

        # loop through and remove selections
        for order, study_activity in selections_to_remove:

            if not (
                study_selection.closure_from_other_ar
                and study_selection.closure_from_other_ar.study_selection_uid
                == study_activity.study_selection_uid
            ):
                audit_node, last_study_selection_node = (
                    self._get_audit_trail_nodes_to_reference(
                        study_root_node=study_root_node,
                        latest_study_value_node=latest_study_value_node,
                        author_id=author_id,
                        study_activity=study_activity,
                        study_selection=study_selection,
                    )
                )
                audit_trail_nodes[study_activity.study_selection_uid] = (
                    audit_node,
                    last_study_selection_node,
                )

                if isinstance(audit_node, Delete):
                    self._add_new_selection(
                        latest_study_value_node,
                        order,
                        study_activity,
                        audit_node,
                        last_study_selection_node,
                        True,
                    )

        # loop through and add selections
        for order, selection in selections_to_add:
            last_study_selection_node = None
            if selection.study_selection_uid in audit_trail_nodes:
                audit_node, last_study_selection_node = audit_trail_nodes[
                    selection.study_selection_uid
                ]
            elif (
                study_selection.closure_from_other_ar
                and selection.study_selection_uid
                == study_selection.closure_from_other_ar.study_selection_uid
            ):
                audit_node, last_study_selection_node = (
                    self._get_audit_trail_nodes_to_reference(
                        study_root_node=study_root_node,
                        latest_study_value_node=latest_study_value_node,
                        author_id=author_id,
                        study_activity=selection,
                        study_selection=study_selection,
                    )
                )
            else:
                audit_node = Create()
                audit_node.author_id = selection.author_id
                audit_node.date = selection.start_date
                audit_node.save()
                study_root_node.audit_trail.connect(audit_node)
            new_order = order
            if not make_order_check:
                new_order = selection.order
            self._add_new_selection(
                latest_study_value_node,
                new_order,
                selection,
                audit_node,
                last_study_selection_node,
                False,
            )

    @staticmethod
    def _set_before_audit_info(
        study_activity_selection_node: StudySelection,
        audit_node: StudyAction,
        study_root_node: StudyRoot,
        author_id: str,
    ) -> StudyAction:
        audit_node.author_id = author_id
        audit_node.date = datetime.datetime.now(datetime.timezone.utc)
        audit_node.save()

        audit_node.has_before.connect(study_activity_selection_node)
        study_root_node.audit_trail.connect(audit_node)
        return audit_node

    def _get_selection_with_history(
        self, study_uid: str, study_selection_uid: str = None
    ):
        """
        returns the audit trail for study activity either for a specific selection or for all study activity for the study
        """

        audit_trail_query = self.get_audit_trail_query(
            study_selection_uid=study_selection_uid
        )
        specific_activity_selections_audit_trail = db.cypher_query(
            audit_trail_query,
            {"study_uid": study_uid, "study_selection_uid": study_selection_uid},
        )
        result = []
        for res in utils.db_result_to_list(specific_activity_selections_audit_trail):
            change_type = ""
            for action in res["change_type"]:
                if "StudyAction" not in action:
                    change_type = action
            end_date = (
                convert_to_datetime(value=res["end_date"]) if res["end_date"] else None
            )
            result.append(
                self.get_selection_history(
                    selection=res, change_type=change_type, end_date=end_date
                )
            )
        return result

    def find_selection_history(
        self, study_uid: str, study_selection_uid: str | None = None
    ) -> list[dict | None]:
        if study_selection_uid:
            return self._get_selection_with_history(
                study_uid=study_uid, study_selection_uid=study_selection_uid
            )
        return self._get_selection_with_history(study_uid=study_uid)

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass

    def get_detailed_soa_history(
        self, study_uid: str, page_number: int, page_size: int, total_count: bool
    ) -> tuple[list[dict], int]:
        detailed_soa_audit_trail = """
        CALL {
        MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyActivity)
            -[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(fgr:CTTermRoot)
            -[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(fgr_value:CTTermNameValue)
        MATCH (study_soa_group:StudySoAGroup)<-[:AFTER]-(asa:StudyAction)
        OPTIONAL MATCH (study_soa_group:StudySoAGroup)<-[:BEFORE]-(bsa:StudyAction)
        WITH DISTINCT all_sa, fgr_value, asa, bsa, study_soa_group
        ORDER BY asa.date DESC
        RETURN
            all_sa.uid as sa_uid,
            'visibility flag' AS object_type,
            fgr_value.name + ' ' + coalesce(study_soa_group.show_soa_group_in_protocol_flowchart, false)  AS description,
            asa.date AS start_date,
            asa.author_id AS author_id,
            labels(asa) AS change_type,
            bsa.date AS end_date
        UNION
        MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyActivity)
            -[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
            -[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)
        MATCH (all_sa:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
            -[:HAS_FLOWCHART_GROUP]->(fgr:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(fgr_value:CTTermNameValue)
        MATCH (study_activity_group:StudyActivityGroup)<-[:AFTER]-(asa:StudyAction)
        OPTIONAL MATCH (study_activity_group:StudyActivityGroup)<-[:BEFORE]-(bsa:StudyAction)
        WITH DISTINCT all_sa, fgr_value, activity_group_value, asa, bsa, study_activity_group
        ORDER BY asa.date DESC
        RETURN DISTINCT
            all_sa.uid as sa_uid,
            'visibility flag' AS object_type,
            fgr_value.name + '/' + activity_group_value.name + ' ' +  study_activity_group.show_activity_group_in_protocol_flowchart  AS description,
            asa.date AS start_date,
            asa.author_id AS author_id,
            labels(asa) AS change_type,
            bsa.date AS end_date
        UNION
        MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyActivity)
            -[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
            -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)
        MATCH (all_sa:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
            -[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)
        MATCH (all_sa:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
            -[:HAS_FLOWCHART_GROUP]->(fgr:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(fgr_value:CTTermNameValue)
        MATCH (study_activity_subgroup:StudyActivitySubGroup)<-[:AFTER]-(asa:StudyAction)
        OPTIONAL MATCH (study_activity_subgroup:StudyActivitySubGroup)<-[:BEFORE]-(bsa:StudyAction)
        WITH DISTINCT all_sa, fgr_value, activity_group_value, activity_subgroup_value, asa, bsa, study_activity_subgroup
        ORDER BY asa.date DESC
        RETURN DISTINCT
            all_sa.uid as sa_uid,
            'visibility flag' AS object_type,
            fgr_value.name + '/' + activity_group_value.name+ '/' + activity_subgroup_value.name + ' ' +  study_activity_subgroup.show_activity_subgroup_in_protocol_flowchart  AS description,
            asa.date AS start_date,
            asa.author_id AS author_id,
            labels(asa) AS change_type,
            bsa.date AS end_date

        UNION
        MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyActivity)
            -[:HAS_SELECTED_ACTIVITY]->(av:ActivityValue)

        MATCH (all_sa:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
            -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)
        MATCH (all_sa:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
            -[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)
        MATCH (all_sa:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
            -[:HAS_FLOWCHART_GROUP]->(fgr:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(fgr_value:CTTermNameValue)
        MATCH (all_sa:StudyActivity)<-[:AFTER]-(asa:StudyAction)
        OPTIONAL MATCH (all_sa:StudyActivity)<-[:BEFORE]-(bsa:StudyAction)
        WITH DISTINCT all_sa, fgr_value, activity_group_value, activity_subgroup_value, av, asa, bsa
        ORDER BY asa.date DESC
        RETURN DISTINCT
            all_sa.uid as sa_uid,
            'visibility flag' AS object_type,
            fgr_value.name + '/' + activity_group_value.name+ '/' + activity_subgroup_value.name+ '/' + av.name  + ' ' +  all_sa.show_activity_in_protocol_flowchart  AS description,
            asa.date AS start_date,
            asa.author_id AS author_id,
            labels(asa) AS change_type,
            bsa.date AS end_date

        UNION
        MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyActivity)
            -[:STUDY_ACTIVITY_HAS_SCHEDULE]->(sas:StudyActivitySchedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(visit:StudyVisit)
        MATCH (all_sa:StudyActivity)-[:HAS_SELECTED_ACTIVITY]->(av:ActivityValue)
        MATCH (sas:StudyActivitySchedule)<-[:AFTER]-(asa:StudyAction)
        OPTIONAL MATCH (sas:StudyActivitySchedule)<-[:BEFORE]-(bsa:StudyAction)
        WITH DISTINCT all_sa, visit, asa, bsa, av
        ORDER BY asa.date DESC
        RETURN DISTINCT
            all_sa.uid as sa_uid,
            'schedule' AS object_type,
            av.name +" " +  coalesce(visit.short_visit_label,"") as description,
            asa.date AS start_date,
            asa.author_id AS author_id,
            labels(asa) AS change_type,
            bsa.date AS end_date
        UNION
        MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(soaf:UpdateSoASnapshot)
        RETURN DISTINCT
            soaf.uid as sa_uid,
            soaf.object_type AS object_type,
            'SoA snapshot updated' as description,
            soaf.date AS start_date,
            soaf.author_id AS author_id,
            labels(soaf) AS change_type,
            soaf.date AS end_date
        }
        
        WITH *
            CALL {
                WITH author_id
                OPTIONAL MATCH (author: User)
                WHERE author.user_id = author_id
                RETURN coalesce(author.username, author_id) as author_username
            }  
        RETURN DISTINCT
            sa_uid,
            object_type,
            description,
            start_date,
            author_id,
            change_type,
            end_date,
            author_username
        ORDER BY start_date DESC
        """
        total_count_query = """
               PROFILE CALL {
        MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyActivity)
            -[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(fgr:CTTermRoot)
            -[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(fgr_value:CTTermNameValue)
        MATCH (study_soa_group:StudySoAGroup)<-[:AFTER]-(asa:StudyAction)
        RETURN count(distinct study_soa_group) as ct
        UNION ALL
        MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyActivity)
            -[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
            -[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)
        MATCH (all_sa:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
            -[:HAS_FLOWCHART_GROUP]->(fgr:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(fgr_value:CTTermNameValue)
        MATCH (study_activity_group:StudyActivityGroup)<-[:AFTER]-(asa:StudyAction)
        RETURN count(distinct study_activity_group) as ct
        UNION ALL
        MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyActivity)
            -[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
            -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)
        MATCH (all_sa:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
            -[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)
        MATCH (all_sa:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
            -[:HAS_FLOWCHART_GROUP]->(fgr:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(fgr_value:CTTermNameValue)
        MATCH (study_activity_subgroup:StudyActivitySubGroup)<-[:AFTER]-(asa:StudyAction)
        RETURN count(distinct study_activity_subgroup) as ct
        UNION ALL
        MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyActivity)
            -[:HAS_SELECTED_ACTIVITY]->(av:ActivityValue)
        MATCH (all_sa:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
            -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)
        MATCH (all_sa:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
            -[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)
        MATCH (all_sa:StudyActivity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)
            -[:HAS_FLOWCHART_GROUP]->(fgr:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(fgr_value:CTTermNameValue)
        MATCH (all_sa:StudyActivity)<-[:AFTER]-(asa:StudyAction)
        RETURN count(distinct all_sa) as ct
        UNION ALL
        MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyActivity)
            -[:STUDY_ACTIVITY_HAS_SCHEDULE]->(sas:StudyActivitySchedule)<-[:STUDY_VISIT_HAS_SCHEDULE]-(visit:StudyVisit)
        MATCH (all_sa:StudyActivity)-[:HAS_SELECTED_ACTIVITY]->(av:ActivityValue)
        MATCH (sas:StudyActivitySchedule)<-[:AFTER]-(asa:StudyAction)
        RETURN count(distinct sas) as ct
        }
        return sum(ct)
        """
        detailed_soa_audit_trail += (
            "SKIP $page_number * $page_size LIMIT $page_size" if page_size > 0 else ""
        )
        validate_max_skip_clause(page_number=page_number, page_size=page_size)

        detailed_soa_audit_trail = db.cypher_query(
            detailed_soa_audit_trail,
            {
                "study_uid": study_uid,
                "page_number": page_number - 1,
                "page_size": page_size,
            },
        )
        result = []
        for res in utils.db_result_to_list(detailed_soa_audit_trail):
            change_type = ""
            for action in res["change_type"]:
                if "StudyAction" not in action:
                    change_type = action
            start_date = (
                convert_to_datetime(value=res["start_date"])
                if res["start_date"]
                else None
            )
            end_date = (
                convert_to_datetime(value=res["end_date"]) if res["end_date"] else None
            )
            res["change_type"] = change_type
            res["end_date"] = end_date
            res["start_date"] = start_date
            result.append(res)
        amount_of_detailed_soa_history_items = []
        if total_count:
            amount_of_detailed_soa_history_items, _ = db.cypher_query(
                total_count_query,
                {
                    "study_uid": study_uid,
                },
            )
        total_amount = (
            amount_of_detailed_soa_history_items[0][0]
            if total_count and len(amount_of_detailed_soa_history_items) > 0
            else 0
        )

        return result, total_amount
