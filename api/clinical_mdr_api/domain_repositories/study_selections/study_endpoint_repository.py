from typing import Any

from neomodel import db

from clinical_mdr_api import utils
from clinical_mdr_api.domain_repositories._utils.helpers import (
    acquire_write_lock_study_value,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.generic_repository import (
    _manage_versioning_with_relations,
)
from clinical_mdr_api.domain_repositories.models.concepts import UnitDefinitionRoot
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermContext,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import Conjunction
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
    StudyAction,
)
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyEndpoint,
    StudyObjective,
)
from clinical_mdr_api.domain_repositories.models.syntax import (
    EndpointRoot,
    EndpointTemplateRoot,
    EndpointTemplateValue,
    EndpointValue,
    TimeframeRoot,
    TimeframeValue,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameter,
)
from clinical_mdr_api.domains.study_selections.study_selection_endpoint import (
    StudyEndpointSelectionHistory,
    StudySelectionEndpointsAR,
    StudySelectionEndpointVO,
)
from common.config import settings
from common.exceptions import BusinessLogicException
from common.utils import convert_to_datetime


class StudySelectionEndpointRepository:

    def _retrieves_all_data(
        self,
        study_uids: str | list[str] | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        study_value_version: str | None = None,
    ) -> tuple[StudySelectionEndpointVO]:
        query = ""
        query_parameters: dict[str, Any] = {}

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

        query += """
            WITH sr, sv
            MATCH (sv)-[:HAS_STUDY_ENDPOINT]->(se:StudyEndpoint)
            OPTIONAL MATCH (se)-[:HAS_SELECTED_ENDPOINT]->(ev:EndpointValue)
            CALL (ev,se) {
                OPTIONAL MATCH (ev) <-[ver]-(er:EndpointRoot) 
                WHERE ver.status = "Final"
                RETURN ver as ver, er as obj, true as is_instance
                ORDER BY ver.start_date DESC
                LIMIT 1
            UNION
                MATCH (se)-[:HAS_SELECTED_ENDPOINT_TEMPLATE]->(:EndpointTemplateValue)<-[ver]-(etr:EndpointTemplateRoot)
                WHERE ver.status = "Final"
                RETURN ver as ver, etr as obj, false as is_instance
                ORDER BY ver.start_date DESC
                LIMIT 1
            }
            OPTIONAL MATCH (se)-[:HAS_SELECTED_TIMEFRAME]->(tv:TimeframeValue)
            CALL (tv) {
              OPTIONAL MATCH (tv) <-[ver]-(tr:TimeframeRoot) 
              WHERE ver.status = "Final"
              RETURN ver as timeframe_ver, tr as tr
              ORDER BY ver.start_date DESC
              LIMIT 1
            }
            WITH DISTINCT sr, se, obj, tr, timeframe_ver, ver, is_instance

            OPTIONAL MATCH (se)-[:HAS_ENDPOINT_LEVEL]->(level_term_context:CTTermContext)-[:HAS_SELECTED_TERM]->(elr:CTTermRoot)
            OPTIONAL MATCH (level_term_context)-[:HAS_SELECTED_CODELIST]->(:CTCodelistRoot)-[has_term:HAS_TERM WHERE has_term.end_date IS NULL]->(:CTCodelistTerm)-[:HAS_TERM_ROOT]->(elr)
            OPTIONAL MATCH (se)-[:HAS_ENDPOINT_SUB_LEVEL]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(endpoint_sublevel_root:CTTermRoot)
        """
        if study_value_version:
            query += """
                OPTIONAL MATCH (se)-[:STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE]->(so:StudyObjective)--(:StudyValue)-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]-(:StudyRoot)
            """
        else:
            query += """
                OPTIONAL MATCH (se)-[:STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE]->(so:StudyObjective)--(:StudyValue)-[:LATEST]-(:StudyRoot)
            """

        query += """
            //OPTIONAL MATCH (se)-[:STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE]->(so:StudyObjective)--(sv)
            WITH sr, se, obj, tr, elr, so, timeframe_ver, ver, has_term, endpoint_sublevel_root, is_instance
            CALL (se) {
                OPTIONAL MATCH (se)-[rel:HAS_UNIT]->(un:UnitDefinitionRoot)-[:LATEST_FINAL]->(unv:UnitDefinitionValue)
                WITH rel, un, unv, se ORDER BY rel.index
                WITH collect({uid: un.uid, name: unv.name}) as units, se
                OPTIONAL MATCH (se)-[:HAS_CONJUNCTION]->(co:Conjunction) 
                WITH  units, co
                RETURN {units :units, separator : co.string} as values 
            }

            MATCH (se)<-[:AFTER]-(sa:StudyAction)

            RETURN DISTINCT
                sr.uid AS study_uid,
                se.uid AS study_endpoint_uid,
                se.order AS order,
                se.accepted_version AS accepted_version,
                obj.uid AS endpoint_uid,
                has_term.order AS endpoint_order,
                tr.uid AS timeframe_uid,
                ver.version AS endpoint_version,
                timeframe_ver.version AS timeframe_version,
                elr.uid AS endpoint_level_uid,
                endpoint_sublevel_root.uid AS endpoint_sublevel_uid,
                so.uid AS study_objective_uid,
                se.text AS text,
                sa.date AS start_date,
                is_instance AS is_instance,
                sa.author_id AS author_id,
                values
                ORDER BY order
            """

        all_endpoint_selections = db.cypher_query(query, query_parameters)
        all_selections = []

        for selection in utils.db_result_to_list(all_endpoint_selections):
            if not selection["endpoint_uid"]:
                continue

            if selection["values"] is not None:
                if "units" in selection["values"]:
                    units = selection["values"]["units"]
                else:
                    units = None
                if "separator" in selection["values"]:
                    separator = selection["values"]["separator"]
                else:
                    separator = None
            else:
                units = None
                separator = None
            acv = selection.get("accepted_version", False)
            if acv is None:
                acv = False
            selection_vo = StudySelectionEndpointVO.from_input_values(
                study_uid=selection["study_uid"],
                endpoint_uid=selection["endpoint_uid"],
                endpoint_version=selection["endpoint_version"],
                endpoint_level_uid=selection["endpoint_level_uid"],
                endpoint_sublevel_uid=selection["endpoint_sublevel_uid"],
                endpoint_level_order=selection["endpoint_order"],
                endpoint_units=units,
                timeframe_uid=selection["timeframe_uid"],
                timeframe_version=selection["timeframe_version"],
                unit_separator=separator,
                study_objective_uid=selection["study_objective_uid"],
                study_selection_uid=selection["study_endpoint_uid"],
                is_instance=selection["is_instance"],
                start_date=convert_to_datetime(value=selection["start_date"]),
                author_id=selection["author_id"],
                accepted_version=acv,
            )
            all_selections.append(selection_vo)
        return tuple(all_selections)

    def find_all(
        self,
        project_name: str | None = None,
        project_number: str | None = None,
        study_uids: list[str] | None = None,
    ) -> list[StudySelectionEndpointsAR]:
        """
        Finds all the selected study endpoints for all studies, and create the aggregate
        :return: List of StudySelectionEndpointsAR, potentially empty
        """
        all_selections = self._retrieves_all_data(
            project_name=project_name,
            project_number=project_number,
            study_uids=study_uids,
        )
        # Create a dictionary, with study_uid as key, and list of selections as value
        selection_aggregate_dict: dict[str, Any] = {}
        selection_aggregates = []
        for selection in all_selections:
            if selection.study_uid in selection_aggregate_dict:
                selection_aggregate_dict[selection.study_uid].append(selection)
            else:
                selection_aggregate_dict[selection.study_uid] = [selection]  # type: ignore[index]
        # Then, create the list of VO from the dictionary
        for study_uid, selections in selection_aggregate_dict.items():
            selection_aggregates.append(
                StudySelectionEndpointsAR.from_repository_values(
                    study_uid=study_uid, study_endpoints_selection=selections
                )
            )
        return selection_aggregates

    def find_by_study(
        self,
        study_uid: str,
        for_update: bool = False,
        study_value_version: str | None = None,
    ) -> StudySelectionEndpointsAR:
        """
        Finds all the selected study endpoints for a given study, and creates the aggregate
        :param study_uid:
        :param for_update:
        :return:
        """
        if for_update:
            acquire_write_lock_study_value(study_uid)
        all_selections = self._retrieves_all_data(
            study_uid, study_value_version=study_value_version
        )
        selection_aggregate = StudySelectionEndpointsAR.from_repository_values(
            study_uid=study_uid, study_endpoints_selection=all_selections
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def _get_audit_node(
        self, study_selection: StudySelectionEndpointsAR, study_selection_uid: str
    ):
        all_current_ids = []
        for item in study_selection.study_endpoints_selection:
            all_current_ids.append(item.study_selection_uid)
        all_closure_ids = []
        for item in study_selection.repository_closure_data:
            all_closure_ids.append(item.study_selection_uid)
        # if uid is in current data
        if study_selection_uid in all_current_ids:
            # if uid is in closure data
            if study_selection_uid in all_closure_ids:
                return Edit()
            return Create()
        return Delete()

    # pylint: disable=unused-argument
    def save(self, study_selection: StudySelectionEndpointsAR, author_id: str) -> None:
        """
        Persist the set of selected study endpoints from the aggregate to the database
        :param study_selection:
        :param author_id:
        """
        assert study_selection.repository_closure_data is not None

        # get the closure_data
        closure_data = study_selection.repository_closure_data
        closure_data_length = len(closure_data)

        # getting the latest study value node
        study_root_node = StudyRoot.nodes.get(uid=study_selection.study_uid)
        latest_study_value_node = study_root_node.latest_value.single()

        BusinessLogicException.raise_if(
            study_root_node.latest_locked.get_or_none() == latest_study_value_node,
            msg="You cannot add or reorder a study selection when the study is in a locked state.",
        )

        selections_to_remove = []
        selections_to_add = []

        # check if object is removed from the selection list - delete have been called
        if len(closure_data) > len(study_selection.study_endpoints_selection):
            # remove the last item from old list, as there will no longer be any study objective with that high order
            selections_to_remove.append((len(closure_data), closure_data[-1]))

        # loop through new data - start=1 as order starts at 1 not at 0 and find what needs to be removed and added
        for order, selection in enumerate(
            study_selection.study_endpoints_selection, start=1
        ):
            # check whether something new is added
            if closure_data_length > order - 1:
                # check if anything has changed
                if selection is not closure_data[order - 1]:
                    # update the selection by removing the old if the old exists, and adding new selection
                    selections_to_remove.append((order, closure_data[order - 1]))
                    selections_to_add.append((order, selection))
            else:
                # else something new have been added
                selections_to_add.append((order, selection))

        # audit trail nodes dictionary, holds the new nodes created for the audit trail
        audit_trail_nodes = {}
        # dictionary of last nodes to traverse to their old connections
        last_nodes = {}

        # loop through and remove selections
        for order, selection in selections_to_remove:
            last_study_selection_node = latest_study_value_node.has_study_endpoint.get(
                uid=selection.study_selection_uid
            )
            self._remove_old_selection_if_exists(study_selection.study_uid, selection)
            audit_node = self._get_audit_node(
                study_selection, selection.study_selection_uid
            )
            audit_trail_nodes[selection.study_selection_uid] = audit_node
            last_nodes[selection.study_selection_uid] = last_study_selection_node
            if isinstance(audit_node, Delete):
                self._add_new_selection(
                    study_root_node,
                    latest_study_value_node,
                    order,
                    selection,
                    audit_node,
                    True,
                    last_study_selection_node,
                )

        # loop through and add selections
        for order, selection in selections_to_add:
            last_study_selection_node = None
            if selection.study_selection_uid in audit_trail_nodes:
                audit_node = audit_trail_nodes[selection.study_selection_uid]
                last_study_selection_node = last_nodes[selection.study_selection_uid]
            else:
                audit_node = Create()
            self._add_new_selection(
                study_root_node,
                latest_study_value_node,
                order,
                selection,
                audit_node,
                False,
                last_study_selection_node,
            )

            # If some objectives already used this study endpoint
            # Update the parameter relationship
            self._maintain_parameters(selection.study_selection_uid)

    def _maintain_parameters(self, study_endpoint_uid: str):
        query = """
            MATCH (old:StudyEndpoint {uid: $uid})<-[rel:USES_VALUE]-()
            WHERE NOT (old)<--(:StudyValue)
            MATCH (new:StudyEndpoint {uid: $uid})<--(:StudyValue)
            CALL apoc.refactor.to(rel, new)
            YIELD input, output
            RETURN input, output
        """

        db.cypher_query(query, {"uid": study_endpoint_uid})

    @staticmethod
    def _remove_old_selection_if_exists(
        study_uid: str, study_selection: StudySelectionEndpointVO
    ) -> None:
        """
        Removal is taking both new and old uid. When a study selection is deleted, we do no longer need to use the uid
        on that study selection node anymore, however do to database constraint the node needs to have a uid. So we are
        overwriting a deleted node uid, with a new never used dummy uid.

        We are doing this to be able to maintain the selection instead of removing it, instead a removal will only
        detach the selection from the study value node. So we keep the old selection to have full audit trail available
        in the database.
        :param study_uid:
        :param old_uid:
        :param new_uid:
        :return:
        """
        db.cypher_query(
            """
            MATCH (:StudyRoot { uid: $study_uid})-[:LATEST]->(:StudyValue)-[rel:HAS_STUDY_ENDPOINT]->(se:StudyEndpoint { uid: $selection_uid})
            REMOVE se:TemplateParameterTermRoot
            DELETE rel
            WITH se
            MATCH (se)<-[tp_rel:HAS_PARAMETER_TERM]-(:TemplateParameter)
            DELETE tp_rel
            """,
            {
                "study_uid": study_uid,
                "selection_uid": study_selection.study_selection_uid,
            },
        )

    @staticmethod
    def _add_new_selection(
        study_root: StudyRoot,
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionEndpointVO,
        audit_node: StudyAction,
        for_deletion: bool = False,
        before_node: StudyEndpoint | None = None,
    ):
        # Create new endpoint selection
        study_endpoint_selection_node = StudyEndpoint(
            order=order,
            uid=selection.study_selection_uid,
            accepted_version=selection.accepted_version,
        ).save()

        # Connect new node with StudyEndpoint template parameter
        _ = TemplateParameter.nodes.get(name=settings.study_endpoint_tp_name)
        db.cypher_query(
            """
            MATCH (se:StudyEndpoint) WHERE elementId(se)=$element_id SET se:TemplateParameterTermRoot
            WITH se
            MATCH (tp:TemplateParameter {name: $tp_name})
            MERGE (tp)-[:HAS_PARAMETER_TERM]->(se)
        """,
            {
                "element_id": study_endpoint_selection_node.element_id,
                "tp_name": settings.study_endpoint_tp_name,
            },
        )

        # Connect new node with study value
        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_endpoint.connect(
                study_endpoint_selection_node
            )

        # check if endpoint is set
        if selection.endpoint_uid:
            if selection.is_instance:
                # Get the endpoint value and connect new node with endpoint value
                endpoint_root_node: EndpointRoot = EndpointRoot.nodes.get(
                    uid=selection.endpoint_uid
                )
                if selection.endpoint_version is None:
                    raise ValueError("endpoint_version must not be None")
                latest_endpoint_value_node = endpoint_root_node.get_value_for_version(
                    selection.endpoint_version
                )
                study_endpoint_selection_node.has_selected_endpoint.connect(
                    latest_endpoint_value_node
                )
            else:
                # Get the endpoint template value
                endpoint_template_root_node: EndpointTemplateRoot = (
                    EndpointTemplateRoot.nodes.get(uid=selection.endpoint_uid)
                )
                if selection.endpoint_version is None:
                    raise ValueError("endpoint_version must not be None")
                latest_endpoint_template_value_node = (
                    endpoint_template_root_node.get_value_for_version(
                        selection.endpoint_version
                    )
                )
                study_endpoint_selection_node.has_selected_endpoint_template.connect(
                    latest_endpoint_template_value_node
                )

        # check if timeframe is set
        if selection.timeframe_uid:
            # find the timeframe value
            timeframe_root_node = TimeframeRoot.nodes.get(uid=selection.timeframe_uid)
            latest_timeframe_value_node = timeframe_root_node.get_value_for_version(
                version=selection.timeframe_version
            )
            # Connect new node with timeframe value
            study_endpoint_selection_node.has_selected_timeframe.connect(
                latest_timeframe_value_node
            )
        # check if study objective is set
        if selection.study_objective_uid:
            # find the objective
            study_objective = latest_study_value_node.has_study_objective.get(
                uid=selection.study_objective_uid
            )
            # connect to node
            study_endpoint_selection_node.study_endpoint_has_study_objective.connect(
                study_objective
            )
        # Set endpoint level if exists
        if selection.endpoint_level_uid:
            ct_term_root = CTTermRoot.nodes.get(uid=selection.endpoint_level_uid)
            selected_term_node = (
                CTCodelistAttributesRepository().get_or_create_selected_term(
                    ct_term_root,
                    codelist_submission_value=settings.study_endpoint_level_cl_submval,
                    catalogue_name=settings.sdtm_ct_catalogue_name,
                )
            )
            study_endpoint_selection_node.has_endpoint_level.connect(selected_term_node)
        # Set endpoint sub level if exists
        if selection.endpoint_sublevel_uid:
            ct_term_root = CTTermRoot.nodes.get(uid=selection.endpoint_sublevel_uid)
            selected_term_node = CTCodelistAttributesRepository().get_or_create_selected_term(
                ct_term_root,
                codelist_submission_value=settings.study_endpoint_sublevel_cl_submval,
                catalogue_name=settings.sdtm_ct_catalogue_name,
            )
            study_endpoint_selection_node.has_endpoint_sublevel.connect(
                selected_term_node
            )
        # for all units which was set
        for index, unit in enumerate(selection.endpoint_units, start=1):
            # get unit definition node
            endpoint_unit_node = UnitDefinitionRoot.nodes.get_or_none(uid=unit["uid"])

            # connect to the unit node
            rel = study_endpoint_selection_node.has_unit.connect(endpoint_unit_node)
            rel.index = index
            rel.save()
        # check if any separator is selected
        if selection.unit_separator:
            # create new conjunction if it does not all ready exists
            conjunction_node = Conjunction.nodes.first_or_none(
                string=selection.unit_separator
            )
            if conjunction_node is None:
                conjunction_node = Conjunction(string=selection.unit_separator).save()
            # connect to conjunction which is used as a separator for the units
            rel = study_endpoint_selection_node.has_conjunction.connect(
                conjunction_node
            )
            # We add a meaningless position value, as there can always only be 1. However we do this to follow the
            #  data model
            rel.position = 1
            rel.save()

        _manage_versioning_with_relations(
            study_root=study_root,
            action_type=type(audit_node),
            before=before_node,
            after=study_endpoint_selection_node,
            exclude_relationships=[
                EndpointValue,
                EndpointTemplateValue,
                TimeframeValue,
                StudyObjective,
                CTTermContext,
                UnitDefinitionRoot,
                Conjunction,
            ],
            author_id=selection.author_id,
        )

    def is_used_as_parameter(self, study_selection_uid: str) -> bool:
        result = db.cypher_query(
            """
                MATCH (:StudyValue)--(se:StudyEndpoint {uid:$uid})<-[:USES_VALUE]-(v:ObjectiveValue)--(:StudyObjective)--(:StudyValue)
                RETURN count(v) > 0
            """,
            {"uid": study_selection_uid},
        )

        return result[0][0][0]

    def generate_uid(self) -> str:
        return StudyEndpoint.get_next_free_uid_and_increment_counter()

    def _get_selection_with_history(
        self, study_uid: str, study_selection_uid: str | None = None
    ):
        """
        returns the audit trail for study endpoints either for a specific selection or for all study endpoints for the study
        """
        if study_selection_uid:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(se:StudyEndpoint { uid: $study_selection_uid})
            WITH se
            MATCH (se)-[:AFTER|BEFORE*0..]-(all_se:StudyEndpoint)
            WITH distinct all_se
            """
        else:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_se:StudyEndpoint)
            WITH DISTINCT all_se
            """
        specific_objective_selections_audit_trail = db.cypher_query(
            cypher + """
            MATCH (all_se)-[:HAS_SELECTED_ENDPOINT]->(ev:EndpointValue)

            CALL (ev) {
              OPTIONAL MATCH (ev) <-[ver]-(er:EndpointRoot) 
              WHERE ver.status = "Final"
              RETURN ver as endpoint_ver, er as er
              ORDER BY ver.start_date DESC
              LIMIT 1
            }
            OPTIONAL MATCH (all_se)-[:HAS_SELECTED_TIMEFRAME]->(tv:TimeframeValue)
            CALL (tv) {
              OPTIONAL MATCH (tv) <-[ver]-(tr:TimeframeRoot) 
              WHERE ver.status = "Final"
              RETURN ver as timeframe_ver, tr as tr
              ORDER BY ver.start_date DESC
              LIMIT 1
            }
            WITH DISTINCT all_se, er, tr, timeframe_ver, endpoint_ver

            OPTIONAL MATCH (all_se)-[:HAS_ENDPOINT_LEVEL]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(elr:CTTermRoot)
            OPTIONAL MATCH (all_se)-[:HAS_ENDPOINT_SUB_LEVEL]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(endpoint_sublevel:CTTermRoot)
            OPTIONAL MATCH (all_se)-[:STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE]->(so:StudyObjective)

            WITH all_se, er, tr, elr, so, timeframe_ver, endpoint_ver, endpoint_sublevel
            CALL (all_se) {
                OPTIONAL MATCH (all_se)-[rel:HAS_UNIT]->(un:UnitDefinitionRoot)-[:LATEST_FINAL]->(unv:UnitDefinitionValue)
                WITH rel, un, unv, all_se ORDER BY rel.index
                WITH collect({uid: un.uid, name: unv.name}) as units, all_se
                OPTIONAL MATCH (all_se)-[:HAS_CONJUNCTION]->(co:Conjunction) 
                WITH  units, co
                RETURN {units :units, separator : co.string} as values 
            }

            MATCH (all_se)<-[:AFTER]-(sa:StudyAction)
            OPTIONAL MATCH (all_se)<-[:BEFORE]-(bsa:StudyAction)

            WITH all_se, er, elr, sa, bsa , endpoint_ver, timeframe_ver, tr, so, values, endpoint_sublevel
            ORDER BY all_se.uid, sa.date DESC
            RETURN DISTINCT
                all_se.uid AS study_endpoint_uid,
                all_se.order AS order,
                er.uid AS endpoint_uid,
                tr.uid AS timeframe_uid,
                endpoint_ver.version AS endpoint_version,
                timeframe_ver.version AS timeframe_version,
                elr.uid AS endpoint_level,
                endpoint_sublevel.uid AS endpoint_sublevel,
                so.uid AS study_objective_uid,
                all_se.text AS text,
                values,
                sa.date AS start_date,
                sa.status AS status,
                sa.author_id AS author_id,
                labels(sa) AS change_type,
                bsa.date AS end_date""",
            {"study_uid": study_uid, "study_selection_uid": study_selection_uid},
        )
        result = []
        for res in utils.db_result_to_list(specific_objective_selections_audit_trail):
            change_type = ""
            for action in res["change_type"]:
                if "StudyAction" not in action:
                    change_type = action
            if res["end_date"]:
                end_date = convert_to_datetime(value=res["end_date"])
            else:
                end_date = None
            if res["values"] is not None:
                if "units" in res["values"]:
                    units = res["values"]["units"]
                else:
                    units = None
                if "separator" in res["values"]:
                    separator = res["values"]["separator"]
                else:
                    separator = None
            else:
                units = None
                separator = None
            result.append(
                StudyEndpointSelectionHistory(
                    study_selection_uid=res["study_endpoint_uid"],
                    endpoint_uid=res["endpoint_uid"],
                    endpoint_version=res["endpoint_version"],
                    endpoint_level=res["endpoint_level"],
                    endpoint_sublevel=res["endpoint_sublevel"],
                    study_objective_uid=res["study_objective_uid"],
                    timeframe_uid=res["timeframe_uid"],
                    timeframe_version=res["timeframe_version"],
                    endpoint_units=units,
                    unit_separator=separator,
                    start_date=convert_to_datetime(value=res["start_date"]),
                    author_id=res["author_id"],
                    change_type=change_type,
                    end_date=end_date,
                    order=res["order"],
                    status=res["status"],
                )
            )
        return result

    def find_selection_history(
        self, study_uid: str, study_selection_uid: str | None = None
    ) -> list[StudyEndpointSelectionHistory]:
        """
        Simple method to return all versions of a study objectives for a study.
        Optionally a specific selection uid is given to see only the response for a specific selection.
        """
        if study_selection_uid:
            return self._get_selection_with_history(
                study_uid=study_uid, study_selection_uid=study_selection_uid
            )
        return self._get_selection_with_history(study_uid=study_uid)

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass

    def quantity_of_study_endpoints_in_study_objective_uid(
        self,
        study_uid: str,
        study_objective_uid: str,
        study_value_version: str | None = None,
    ) -> int:
        if study_value_version:
            root_match = "MATCH (sr:StudyRoot{uid:$study_uid})-[:HAS_VERSION{version:$study_value_version}]-(sv:StudyValue)"
        else:
            root_match = (
                "MATCH (sr:StudyRoot{uid:$study_uid})-[:LATEST]-(sv:StudyValue)"
            )
        result = db.cypher_query(
            root_match + """
                MATCH (sv)--(se:StudyEndpoint)-[:STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE]->(so:StudyObjective{uid:$study_objective_uid})--(sv)
                RETURN count(distinct se)
            """,
            {
                "study_objective_uid": study_objective_uid,
                "study_uid": study_uid,
                "study_value_version": study_value_version,
            },
        )

        return result[0][0][0]
