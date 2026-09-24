from textwrap import dedent
from typing import Any

from neomodel import db

from clinical_mdr_api import utils
from clinical_mdr_api.domain_repositories.generic_repository import (
    _manage_versioning_with_relations,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
)
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivityGroup,
    StudyActivitySubGroup,
    StudySoAFootnote,
    StudySoAGroup,
)
from clinical_mdr_api.domain_repositories.models.syntax import (
    FootnoteRoot,
    FootnoteTemplateRoot,
    FootnoteTemplateValue,
    FootnoteValue,
)
from clinical_mdr_api.domains.study_selections.study_selection_base import SoAItemType
from clinical_mdr_api.domains.study_selections.study_soa_footnote import (
    ReferencedItemVO,
    StudySoAFootnoteVO,
    StudySoAFootnoteVOHistory,
)
from common.exceptions import (
    BusinessLogicException,
    NotFoundException,
    ValidationException,
)
from common.telemetry import trace_calls
from common.utils import convert_to_datetime


class StudySoAFootnoteRepository:
    def generate_soa_footnote_uid(self) -> str:
        return StudySoAFootnote.get_next_free_uid_and_increment_counter()

    def where_query(self):
        return (
            "WHERE NOT (sf)<-[:BEFORE]-(:StudyAction) AND NOT (sf)<-[:AFTER]-(:Delete)"
        )

    def with_query(self, full_query: bool = True):
        query = []
        # StudyActivity part
        query.append(dedent("""WITH DISTINCT sr, sf, sa,
            [(sf)-[:REFERENCES_STUDY_ACTIVITY]->(study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(sv)
                WHERE NOT (study_activity)-[:BEFORE]-() | 
                {
                    uid:study_activity.uid,
                    epoch_order: 999999,
                    visit_order: 999999,
                    study_soa_group_order:head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group)
                        WHERE NOT (study_soa_group)-[:BEFORE]-() | study_soa_group.order]),
                    study_activity_group_order:head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group)
                        WHERE NOT (study_activity_group)-[:BEFORE]-() | study_activity_group.order]),
                    study_activity_subgroup_order:head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup)
                        WHERE NOT (study_activity_subgroup)-[:BEFORE]-() | study_activity_subgroup.order]),
                    study_activity_order: study_activity.order,
                    study_activity_schedule_order: 0, // 0 as schedule order, because StudyActivity appears in the same row in SoA as schedule but it should take priority in footnote number assignment
                    type: 'StudyActivity'
                """))
        if full_query:
            query.append(
                dedent(
                    """,name:head([(study_activity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue) | activity_value.name]),
                            visible_in_protocol_soa: study_activity.show_activity_in_protocol_flowchart
                    """
                )
            )
        query.append(dedent("}] AS referenced_study_activities, "))
        # StudyActivitySubGroup part
        query.append(
            dedent(
                """[(sf)-[:REFERENCES_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup:StudyActivitySubGroup)
                <-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]-(study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(sv)
                WHERE NOT (study_activity_subgroup)-[:BEFORE]-() |
                {
                    uid:study_activity_subgroup.uid,
                    epoch_order: 999999,
                    visit_order: 999999,
                    study_soa_group_order:head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group) WHERE NOT (study_soa_group)-[:BEFORE]-() | study_soa_group.order]),
                    study_activity_group_order:head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group)
                        WHERE NOT (study_activity_group)-[:BEFORE]-() | study_activity_group.order]),
                    study_activity_subgroup_order:study_activity_subgroup.order,
                    study_activity_order: 0,
                    study_activity_schedule_order: 0,
                    type: 'StudyActivitySubGroup'
                """
            )
        )
        if full_query:
            query.append(
                dedent(
                    """,name:head([(study_activity_subgroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue) | activity_subgroup_value.name]),
                            visible_in_protocol_soa: study_activity_subgroup.show_activity_subgroup_in_protocol_flowchart
                    """
                )
            )
        query.append(dedent("}] AS referenced_study_activity_subgroups, "))
        # StudyActivityGroup part
        query.append(
            dedent(
                """[(sf)-[:REFERENCES_STUDY_ACTIVITY_GROUP]->(study_activity_group:StudyActivityGroup)
                <-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]-(study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(sv)
                WHERE NOT (study_activity_group)-[:BEFORE]-() |
                {
                    uid:study_activity_group.uid,
                    epoch_order: 999999,
                    visit_order: 999999,
                    study_soa_group_order:head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group) WHERE NOT (study_soa_group)-[:BEFORE]-() | study_soa_group.order]),
                    study_activity_group_order:study_activity_group.order,
                    study_activity_subgroup_order:0,
                    study_activity_order: 0,
                    study_activity_schedule_order: 0,
                    type: 'StudyActivityGroup'
                """
            )
        )
        if full_query:
            query.append(
                dedent(
                    """,name:head([(study_activity_group)-[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue) | activity_group_value.name]),
                            visible_in_protocol_soa: study_activity_group.show_activity_group_in_protocol_flowchart
                    """
                )
            )
        query.append(dedent("}] AS referenced_study_activity_groups, "))
        # StudySoAGroup part
        query.append(
            dedent(
                """[(sf)-[:REFERENCES_STUDY_SOA_GROUP]->(study_soa_group:StudySoAGroup)<-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]-(:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(sv)
                WHERE NOT (study_soa_group)-[:BEFORE]-() |
                {
                    uid:study_soa_group.uid,
                    epoch_order: 999999,
                    visit_order: 999999,
                    study_soa_group_order:study_soa_group.order,
                    study_activity_group_order:0,
                    study_activity_subgroup_order:0,
                    study_activity_order: 0,
                    study_activity_schedule_order: 0,
                    type: 'StudySoAGroup'
                """
            )
        )
        if full_query:
            query.append(
                dedent(
                    """,name:head([(study_soa_group)-[:HAS_FLOWCHART_GROUP]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-
                            [:LATEST]->(term_name_value:CTTermNameValue) | term_name_value.name]),
                            visible_in_protocol_soa: study_soa_group.show_soa_group_in_protocol_flowchart
                    """
                )
            )
        query.append(dedent("}] AS referenced_study_soa_groups,"))
        # StudyEpoch part
        query.append(
            dedent(
                """[(sf)-[:REFERENCES_STUDY_EPOCH]->(study_epoch:StudyEpoch)<-[:HAS_STUDY_EPOCH]-(sv) |
                {
                    uid:study_epoch.uid,
                    epoch_order: study_epoch.order,
                    visit_order: 0,
                    study_soa_group_order:0,
                    study_activity_group_order:0,
                    study_activity_subgroup_order:0,
                    study_activity_order: 0,
                    study_activity_schedule_order: 0,
                    type: 'StudyEpoch'
                """
            )
        )
        if full_query:
            query.append(
                dedent(
                    """,name:head([(study_epoch)-[:HAS_EPOCH]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-
                            [:LATEST]->(term_value:CTTermNameValue) | term_value.name]),
                            visible_in_protocol_soa: true
                    """
                )
            )
        query.append(dedent("}] AS referenced_study_epochs, "))
        # StudyVisit part
        query.append(
            dedent(
                """[(sf)-[:REFERENCES_STUDY_VISIT]->(study_visit:StudyVisit)<-[:HAS_STUDY_VISIT]-(sv) |
                {
                    uid:study_visit.uid,
                    epoch_order: 999999,
                    visit_order: toInteger(study_visit.unique_visit_number),
                    study_soa_group_order:0,
                    study_activity_group_order:0,
                    study_activity_subgroup_order:0,
                    study_activity_order: 0,
                    study_activity_schedule_order: 0,
                    type: 'StudyVisit'
                """
            )
        )
        if full_query:
            query.append(
                dedent(
                    " ,name:study_visit.short_visit_label, visible_in_protocol_soa: study_visit.show_visit "
                )
            )
        query.append(dedent("}] AS referenced_study_visits,"))
        # StudyActivitySchedule part
        query.append(
            dedent(
                """[(sf)-[:REFERENCES_STUDY_ACTIVITY_SCHEDULE]->(study_activity_schedule:StudyActivitySchedule)<-[:HAS_STUDY_ACTIVITY_SCHEDULE]-(sv)
              -[:HAS_STUDY_VISIT]->(study_visit:StudyVisit)-[:STUDY_VISIT_HAS_SCHEDULE]->(study_activity_schedule)
              <-[:STUDY_ACTIVITY_HAS_SCHEDULE]-(study_activity:StudyActivity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue)
              WHERE (sv)-[:HAS_STUDY_ACTIVITY]->(study_activity) |
                {
                    uid:study_activity_schedule.uid,
                    epoch_order: 999999,
                    visit_order: 999999,
                    study_soa_group_order:head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group) WHERE NOT (study_soa_group)-[:BEFORE]-() | study_soa_group.order]),
                    study_activity_group_order:head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group)
                        WHERE NOT (study_activity_group)-[:BEFORE]-() | study_activity_group.order]),
                    study_activity_subgroup_order:head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup)
                        WHERE NOT (study_activity_subgroup)-[:BEFORE]-() | study_activity_subgroup.order]),
                    study_activity_order: study_activity.order,
                    study_activity_schedule_order: toInteger(study_visit.unique_visit_number),
                    type: 'StudyActivitySchedule'
            """
            )
        )
        if full_query:
            query.append(
                dedent(
                    """ ,name: activity_value.name + ' ' + study_visit.short_visit_label,
                            visible_in_protocol_soa: study_activity.show_activity_in_protocol_flowchart AND study_visit.show_visit
                    """
                )
            )
        query.append(dedent("}] AS referenced_study_activity_schedules,"))
        # Footnote part
        query.append(
            dedent(
                """ head([(sf)<-[:BEFORE]-(before_action:StudyAction) | before_action.date]) AS end_date
                    CALL (sf) {
                        OPTIONAL MATCH (sf)-[:HAS_SELECTED_FOOTNOTE]->(fv:FootnoteValue)<-[ver:HAS_VERSION]-(fr:FootnoteRoot)<-[:CONTAINS_SYNTAX_INSTANCE]-(library:Library)
                        OPTIONAL MATCH (ftv:FootnoteTemplateValue)<-[:HAS_VERSION]-(ftr:FootnoteTemplateRoot)-[:HAS_FOOTNOTE]->(fr)
                        WHERE ver.status = 'Final'
                        RETURN
                            {uid:fr.uid, name: fv.name, name_plain:fv.name_plain, status: ver.status
                """
            )
        )
        if full_query:
            query.append(
                dedent(
                    " ,version: ver.version, library_name: library.name, template_uid: ftr.uid, template_name: ftv.name "
                )
            )
        query.append(
            dedent(
                " } as footnote, fr as fr, fv as fv ORDER BY ver.start_date DESC LIMIT 1} "
            )
        )
        # Latest Footnote part
        if full_query:
            query.append(dedent("""CALL (fr, fv) {
                OPTIONAL MATCH (latest_footnote_value:FootnoteValue)<-[ver:HAS_VERSION]-(fr:FootnoteRoot)<-[:CONTAINS_SYNTAX_INSTANCE]-(library:Library)
                OPTIONAL MATCH (ftr:FootnoteTemplateRoot)-[:HAS_FOOTNOTE]->(fr)
                WHERE ver.status = 'Final' AND (fr)-[:LATEST]->(latest_footnote_value) and latest_footnote_value<>fv
                RETURN 
                    {uid:fr.uid, version: ver.version, name_plain:fv.name_plain, library_name: library.name, template_uid: ftr.uid} as latest_footnote
                ORDER BY ver.start_date DESC
                LIMIT 1}
                """))
        # Footnote template part
        query.append(dedent("""CALL(sf) {
                OPTIONAL MATCH (sf)-[:HAS_SELECTED_FOOTNOTE_TEMPLATE]->(ftv:FootnoteTemplateValue)<-[ver:HAS_VERSION]-(ftr:FootnoteTemplateRoot)<-[:CONTAINS_SYNTAX_TEMPLATE]-(library:Library)
                WHERE ver.status = 'Final'
                RETURN {
                    uid:ftr.uid, name: ftv.name, name_plain: ftv.name_plain
                """))
        if full_query:
            query.append(
                dedent(
                    ",version: ver.version, library_name: library.name, parameters: [(ftr)-[:USES_PARAMETER]->(template_parameter:TemplateParameter) | template_parameter.name] "
                )
            )
        query.append(
            dedent("} as footnote_template ORDER BY ver.start_date DESC LIMIT 1} ")
        )
        # Main Return part
        query.append(dedent("""RETURN DISTINCT
                sr.uid AS study_uid,
                sf.uid AS uid,
                footnote,
                footnote_template,
                apoc.coll.sortMulti(apoc.coll.toSet(referenced_study_activities) +
                apoc.coll.toSet(referenced_study_activity_subgroups) +
                apoc.coll.toSet(referenced_study_activity_groups) +
                apoc.coll.toSet(referenced_study_soa_groups) +
                apoc.coll.toSet(referenced_study_epochs) +
                apoc.coll.toSet(referenced_study_visits) +
                apoc.coll.toSet(referenced_study_activity_schedules),
                    [
                        '^epoch_order',
                        '^visit_order',
                        '^study_soa_group_order',
                        '^study_activity_group_order',
                        '^study_activity_subgroup_order',
                        '^study_activity_order',
                        '^study_activity_schedule_order'
                    ])  AS referenced_items
                """))
        # Extra return part
        if full_query:
            query.append(dedent(""",latest_footnote,
                    sf.accepted_version as accepted_version,
                    sa.author_id AS author_id,
                    sa.date AS modified_date,
                    end_date,
                    labels(sa) AS change_type,
                    coalesce(head([(user:User)-[*0]-() WHERE user.user_id=sa.author_id | user.username]), sa.author_id) AS author_username
                    """))
        return "\n".join(query)

    def order_by_soa_order(self):
        # The referenced_items array of each SoAFootnote is pre-sorted so that always first item of referenced_items array is the first item that appears in SoA.
        # In this ordering section we can sort SoAFootnotes based on the first item in the referenced_items array as this array was already pre sorted.
        return """ORDER BY
                referenced_items[0].epoch_order, 
                referenced_items[0].visit_order, 
                referenced_items[0].study_soa_group_order, 
                referenced_items[0].study_activity_group_order, 
                referenced_items[0].study_activity_subgroup_order, 
                referenced_items[0].study_activity_order, 
                referenced_items[0].study_activity_schedule_order"""

    def order_by_date(self):
        return "ORDER BY modified_date DESC"

    def get_referenced_items_from_selection(self, selection: dict[Any, Any]):
        referenced_items = []
        for item in selection.get("referenced_items", []):
            item_type = SoAItemType(item.get("type"))
            referenced_items.append(
                ReferencedItemVO(
                    item_uid=item.get("uid"),
                    item_type=item_type,
                    item_name=item.get("name"),
                    visible_in_protocol_soa=item.get("visible_in_protocol_soa"),
                    order=item.get("order"),
                )
            )

        referenced_items.sort(key=lambda ref_item: ref_item.item_name or "")
        return referenced_items

    def create_vo_from_db_output(self, selection: dict[str, Any]) -> StudySoAFootnoteVO:
        referenced_items = self.get_referenced_items_from_selection(selection=selection)

        selection_vo = StudySoAFootnoteVO.from_repository_values(
            study_uid=selection["study_uid"],
            footnote_uid=selection.get("footnote", {}).get("uid"),
            footnote_version=selection.get("footnote", {}).get("version"),
            footnote_name=selection.get("footnote", {}).get("name"),
            footnote_name_plain=selection.get("footnote", {}).get("name_plain"),
            footnote_library_name=selection.get("footnote", {}).get("library_name"),
            footnote_status=selection.get("footnote", {}).get("status"),
            latest_footnote_version=selection.get("latest_footnote", {}).get("version"),
            latest_footnote_name_plain=selection.get("latest_footnote", {}).get(
                "name_plain"
            ),
            footnote_template_uid=selection.get("footnote_template", {}).get("uid")
            or selection.get("footnote", {}).get("template_uid"),
            footnote_template_version=selection.get("footnote_template", {}).get(
                "version"
            ),
            footnote_template_name=selection.get("footnote_template", {}).get("name")
            or selection.get("footnote", {}).get("template_name"),
            footnote_template_name_plain=selection.get("footnote_template", {}).get(
                "name_plain"
            ),
            footnote_template_library_name=selection.get("footnote_template", {}).get(
                "library_name"
            ),
            footnote_template_parameters=selection.get("footnote_template", {}).get(
                "parameters"
            ),
            referenced_items=referenced_items,
            uid=selection["uid"],
            modified=convert_to_datetime(value=selection.get("modified_date")),
            author_id=selection.get("author_id"),
            accepted_version=selection.get("accepted_version", False),
            author_username=selection.get("author_username"),
        )
        return selection_vo

    def create_vo_history_from_db_output(
        self, selection: dict[str, Any]
    ) -> StudySoAFootnoteVOHistory:
        referenced_items = self.get_referenced_items_from_selection(selection=selection)
        change_type = ""
        for action in selection["change_type"]:
            if "StudyAction" not in action:
                change_type = action
        selection_vo = StudySoAFootnoteVOHistory(
            study_uid=selection["study_uid"],
            footnote_uid=selection.get("footnote").get("uid"),
            footnote_version=selection.get("footnote").get("version"),
            footnote_name_plain=selection.get("footnote").get("name_plain"),
            footnote_template_uid=selection.get("footnote_template").get("uid"),
            footnote_template_version=selection.get("footnote_template").get("version"),
            footnote_template_name_plain=selection.get("footnote_template").get(
                "name_plain"
            ),
            referenced_items=referenced_items,
            uid=selection["uid"],
            start_date=convert_to_datetime(value=selection["modified_date"]),
            end_date=(
                convert_to_datetime(value=selection.get("end_date"))
                if selection.get("end_date")
                else None
            ),
            change_type=change_type,
            author_id=selection["author_id"],
            accepted_version=selection["accepted_version"],
            author_username=selection.get("author_username"),
        )
        return selection_vo

    @trace_calls
    def find_all_footnotes(
        self,
        study_uids: str | list[str] | None = None,
        study_value_version: str | None = None,
        full_query: bool = True,
    ) -> list[StudySoAFootnoteVO]:
        query_parameters: dict[str, Any] = {}
        if study_uids:
            if isinstance(study_uids, str):
                study_uid_statement = "{uid: $uids}"
            else:
                study_uid_statement = "WHERE sr.uid IN $uids"
            if study_value_version:
                query = (
                    f"MATCH (sr:StudyRoot {study_uid_statement})-[l:HAS_VERSION{{status:'RELEASED', version:$study_value_version}}]->(sv:StudyValue)"
                    "-[:HAS_STUDY_FOOTNOTE]->(sf:StudySoAFootnote)<-[:AFTER]-(sa:StudyAction)"
                )
                query_parameters["study_value_version"] = study_value_version
                query_parameters["uids"] = study_uids
            else:
                query = (
                    f"MATCH (sr:StudyRoot {study_uid_statement})-[l:LATEST]->(sv:StudyValue)-[:HAS_STUDY_FOOTNOTE]->"
                    "(sf:StudySoAFootnote)<-[:AFTER]-(sa:StudyAction)"
                )
                query_parameters["uids"] = study_uids
        else:
            if study_value_version:
                query = (
                    "MATCH (sr:StudyRoot)-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]->(sv:StudyValue)"
                    "-[:HAS_STUDY_FOOTNOTE]->(sf:StudySoAFootnote)<-[:AFTER]-(sa:StudyAction)"
                )
                query_parameters["study_value_version"] = study_value_version
            else:
                query = (
                    "MATCH (sr:StudyRoot)-[l:LATEST]->(sv:StudyValue)-[:HAS_STUDY_FOOTNOTE]->(sf:StudySoAFootnote)"
                    "<-[:AFTER]-(sa:StudyAction)"
                )

        if not study_value_version:
            query += self.where_query()
        query += self.with_query(full_query=full_query)
        query += self.order_by_soa_order()
        all_study_soa_footnotes = db.cypher_query(query, query_parameters)
        all_selections: list[StudySoAFootnoteVO] = []
        for selection in utils.db_result_to_list(all_study_soa_footnotes):
            selection_vo: StudySoAFootnoteVO = self.create_vo_from_db_output(
                selection=selection
            )
            all_selections.append(selection_vo)

        return all_selections

    def find_by_uid(
        self, study_uid: str, uid: str, study_value_version: str | None = None
    ) -> StudySoAFootnoteVO:
        query_parameters: dict[str, Any] = {}
        query_parameters["uid"] = uid
        query_parameters["study_uid"] = study_uid
        if study_value_version:
            query = (
                "MATCH (sr:StudyRoot {uid: $study_uid})-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]->(sv:StudyValue)-[:HAS_STUDY_FOOTNOTE]->"
                "(sf:StudySoAFootnote {uid:$uid})<-[:AFTER]-(sa:StudyAction)"
            )
            query_parameters["study_value_version"] = study_value_version
        else:
            query = (
                "MATCH (sr:StudyRoot {uid: $study_uid})-[l:LATEST]->(sv:StudyValue)-[:HAS_STUDY_FOOTNOTE]->"
                "(sf:StudySoAFootnote {uid:$uid})<-[:AFTER]-(sa:StudyAction)"
            )
        if not study_value_version:
            query += self.where_query()
        query += self.with_query()

        db_ret = db.cypher_query(query, query_parameters)

        soa_footnote = utils.db_result_to_list(db_ret)

        NotFoundException.raise_if(len(soa_footnote) == 0, "Study SoA Footnote", uid)

        BusinessLogicException.raise_if(
            len(soa_footnote) > 1,
            msg=f"Returned more than one StudySoAFootnote with uid {uid}",
        )

        selection_vo = self.create_vo_from_db_output(selection=soa_footnote[0])
        return selection_vo

    def save(self, soa_footnote_vo: StudySoAFootnoteVO, create: bool = True):
        study_root = StudyRoot.nodes.get(uid=soa_footnote_vo.study_uid)
        study_value = study_root.latest_value.get_or_none()

        BusinessLogicException.raise_if(
            study_value is None,
            msg=f"Study with UID '{soa_footnote_vo.study_uid}' doesn't exist.",
        )

        soa_footnote_node = StudySoAFootnote(
            uid=soa_footnote_vo.uid,
            accepted_version=soa_footnote_vo.accepted_version,
        )
        soa_footnote_node.save()

        # link to selected footnote if there's no specific version
        if soa_footnote_vo.footnote_uid and not soa_footnote_vo.footnote_version:
            selected_footnote = FootnoteRoot.nodes.get(
                uid=soa_footnote_vo.footnote_uid
            ).has_latest_value.get()
            soa_footnote_node.has_footnote.connect(selected_footnote)
        # link to selected footnote with specified version
        elif soa_footnote_vo.footnote_uid and soa_footnote_vo.footnote_version:
            selected_footnote = (
                FootnoteValue.nodes.traverse("has_version")
                .filter(
                    **{
                        "has_version__uid": soa_footnote_vo.footnote_uid,
                        "has_version|version": soa_footnote_vo.footnote_version,
                    }
                )
                .get_or_none()[0]
            )
            soa_footnote_node.has_footnote.connect(selected_footnote)
        # link to selected footnote template if there's no specific version specified
        elif (
            soa_footnote_vo.footnote_template_uid
            and not soa_footnote_vo.footnote_template_version
        ):
            selected_footnote_template = FootnoteTemplateRoot.nodes.get(
                uid=soa_footnote_vo.footnote_template_uid
            ).has_latest_value.get()
            soa_footnote_node.has_footnote_template.connect(selected_footnote_template)
        # link to selected footnote template with specified version
        elif (
            soa_footnote_vo.footnote_template_uid
            and soa_footnote_vo.footnote_template_version
        ):
            selected_footnote_template = (
                FootnoteTemplateValue.nodes.traverse("has_version")
                .filter(
                    **{
                        "has_version__uid": soa_footnote_vo.footnote_template_uid,
                        "has_version|version": soa_footnote_vo.footnote_template_version,
                    }
                )
                .get_or_none()[0]
            )
            soa_footnote_node.has_footnote_template.connect(selected_footnote_template)
        not_found_items = []
        # link to referenced items by a footnote
        for referenced_item in soa_footnote_vo.referenced_items:
            # Activity
            if referenced_item.item_type.value == SoAItemType.STUDY_ACTIVITY.value:
                study_activity_referenced_node = (
                    study_value.has_study_activity.get_or_none(
                        uid=referenced_item.item_uid
                    )
                )
                if study_activity_referenced_node:
                    soa_footnote_node.references_study_activity.connect(
                        study_activity_referenced_node
                    )
                else:
                    not_found_items.append(referenced_item)
            # ActivitySubGroup
            if (
                referenced_item.item_type.value
                == SoAItemType.STUDY_ACTIVITY_SUBGROUP.value
            ):
                study_activity_subgroup_referenced_node = (
                    StudyActivitySubGroup.nodes.has(has_before=False).get_or_none(
                        uid=referenced_item.item_uid
                    )
                )
                if study_activity_subgroup_referenced_node:
                    soa_footnote_node.references_study_activity_subgroup.connect(
                        study_activity_subgroup_referenced_node
                    )
                else:
                    not_found_items.append(referenced_item)
            # Activity Group
            if (
                referenced_item.item_type.value
                == SoAItemType.STUDY_ACTIVITY_GROUP.value
            ):
                study_activity_group_referenced_node = StudyActivityGroup.nodes.has(
                    has_before=False
                ).get_or_none(uid=referenced_item.item_uid)
                if study_activity_group_referenced_node:
                    soa_footnote_node.references_study_activity_group.connect(
                        study_activity_group_referenced_node
                    )
                else:
                    not_found_items.append(referenced_item)
            # SoA Group
            if referenced_item.item_type.value == SoAItemType.STUDY_SOA_GROUP.value:
                study_soa_group_referenced_node = StudySoAGroup.nodes.has(
                    has_before=False
                ).get_or_none(uid=referenced_item.item_uid)
                if study_soa_group_referenced_node:
                    soa_footnote_node.references_study_soa_group.connect(
                        study_soa_group_referenced_node
                    )
                else:
                    not_found_items.append(referenced_item)
            # StudyActivitySchedule
            if (
                referenced_item.item_type.value
                == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value
            ):
                sas_referenced_node = (
                    study_value.has_study_activity_schedule.get_or_none(
                        uid=referenced_item.item_uid
                    )
                )
                if sas_referenced_node:
                    soa_footnote_node.references_study_activity_schedule.connect(
                        sas_referenced_node
                    )
                else:
                    not_found_items.append(referenced_item)
            # StudyVisit
            if referenced_item.item_type.value == SoAItemType.STUDY_VISIT.value:
                study_visit_referenced_node = study_value.has_study_visit.get_or_none(
                    uid=referenced_item.item_uid
                )
                if study_visit_referenced_node:
                    soa_footnote_node.references_study_visit.connect(
                        study_visit_referenced_node
                    )
                else:
                    not_found_items.append(referenced_item)
            # StudyEpoch
            if referenced_item.item_type.value == SoAItemType.STUDY_EPOCH.value:
                study_epoch_referenced_node = study_value.has_study_epoch.get_or_none(
                    uid=referenced_item.item_uid
                )
                if study_epoch_referenced_node:
                    soa_footnote_node.references_study_epoch.connect(
                        study_epoch_referenced_node
                    )
                else:
                    not_found_items.append(referenced_item)

        ValidationException.raise_if(
            not_found_items,
            msg=f"The following referenced nodes were not found "
            f"{[not_found_item.item_name if not_found_item.item_name else not_found_item.item_uid for not_found_item in not_found_items]}",
        )

        if create:
            _manage_versioning_with_relations(
                study_root=study_root,
                action_type=Create,
                before=None,
                after=soa_footnote_node,
                author_id=soa_footnote_vo.author_id,
            )
            soa_footnote_node.study_value.connect(study_value)
        else:
            previous_item = StudySoAFootnote.nodes.filter(uid=soa_footnote_vo.uid).has(
                study_value=True, has_before=False
            )[0]
            exclude_relationships = [
                FootnoteValue,
                FootnoteTemplateValue,
                StudySoAFootnote.references_study_activity,
                StudySoAFootnote.references_study_activity_subgroup,
                StudySoAFootnote.references_study_activity_group,
                StudySoAFootnote.references_study_soa_group,
                StudySoAFootnote.references_study_epoch,
                StudySoAFootnote.references_study_visit,
                StudySoAFootnote.references_study_activity_schedule,
            ]
            if soa_footnote_vo.is_deleted:
                _manage_versioning_with_relations(
                    study_root=study_root,
                    action_type=Delete,
                    before=previous_item,
                    after=soa_footnote_node,
                    exclude_relationships=exclude_relationships,
                    author_id=soa_footnote_vo.author_id,
                )
            else:
                _manage_versioning_with_relations(
                    study_root=study_root,
                    action_type=Edit,
                    before=previous_item,
                    after=soa_footnote_node,
                    exclude_relationships=exclude_relationships,
                    author_id=soa_footnote_vo.author_id,
                )
                soa_footnote_node.study_value.connect(study_value)
            # disconnect old StudyValue node to only keep StudyValue connection to the Latest value of StudySoAFootnote
            previous_item.study_value.disconnect(study_value)

    def get_all_versions_for_specific_footnote(
        self, uid: str, study_uid: str
    ) -> list[StudySoAFootnoteVOHistory]:
        query_parameters: dict[str, Any] = {}
        query = """
                MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(sa:StudyAction)-[:AFTER]->(sf:StudySoAFootnote {uid:$uid})
                """

        query_parameters["study_uid"] = study_uid
        query_parameters["uid"] = uid
        query += self.with_query()
        query += self.order_by_date()
        all_study_soa_footnotes = db.cypher_query(query, query_parameters)
        all_selections = []
        for selection in utils.db_result_to_list(all_study_soa_footnotes):
            selection_vo = self.create_vo_history_from_db_output(selection=selection)
            all_selections.append(selection_vo)
        return all_selections

    def get_all_versions(self, study_uid: str) -> list[StudySoAFootnoteVOHistory]:
        query_parameters: dict[str, Any] = {}
        query = """
                MATCH (sr:StudyRoot {uid: $study_uid})-[:AUDIT_TRAIL]->(sa:StudyAction)-[:AFTER]->(sf:StudySoAFootnote)
                """

        query_parameters["study_uid"] = study_uid
        query += self.with_query()
        query += self.order_by_date()
        all_study_soa_footnotes = db.cypher_query(query, query_parameters)
        all_selections = []
        for selection in utils.db_result_to_list(all_study_soa_footnotes):
            selection_vo = self.create_vo_history_from_db_output(selection=selection)
            all_selections.append(selection_vo)
        return all_selections

    def check_exists_soa_footnotes_for_footnote_and_study_uid(
        self, study_uid: str, footnote_uid: str, soa_footnote_uid_to_exclude: str
    ) -> str | None:
        query = """
            MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)-[:HAS_STUDY_FOOTNOTE]->(study_soa_footnote:StudySoAFootnote)
                -[:HAS_SELECTED_FOOTNOTE]->(footnote_value:FootnoteValue)<-[:HAS_VERSION]-(footnote_root:FootnoteRoot {uid: $footnote_uid})
            WHERE study_soa_footnote.uid <> $soa_footnote_uid_to_exclude AND NOT (study_soa_footnote)-[:BEFORE]-() AND NOT (study_soa_footnote)--(:Delete)
            RETURN DISTINCT footnote_value.name_plain
        """
        existing_footnote, _ = db.cypher_query(
            query,
            params={
                "study_uid": study_uid,
                "footnote_uid": footnote_uid,
                "soa_footnote_uid_to_exclude": soa_footnote_uid_to_exclude,
            },
        )
        return existing_footnote[0][0] if len(existing_footnote) > 0 else None
