import datetime
import logging
from enum import Enum
from textwrap import dedent
from typing import Iterable

from neomodel import DoesNotExist, RelationshipManager, db

from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    UpdateSoASnapshot,
)
from clinical_mdr_api.domain_repositories.models.study_selections import StudySelection
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.domains.study_selections.study_selection_base import (
    SOA_ITEM_TYPES,
    SoAItemType,
)
from clinical_mdr_api.models.study_selections.study_selection import (
    ReferencedItem,
    SoACellReference,
    SoAFootnoteReference,
)
from clinical_mdr_api.services._utils import ensure_transaction
from common import queries
from common.auth.user import user
from common.config import settings
from common.exceptions import NotFoundException
from common.telemetry import trace_calls

SOA_ITEM_TYPE_TO_RELATIONSHIP_MODEL_MAME_MAP = {
    SoAItemType.STUDY_EPOCH: "has_study_epoch",
    SoAItemType.STUDY_VISIT: "has_study_visit",
    SoAItemType.STUDY_SOA_GROUP: "has_study_soa_group",
    SoAItemType.STUDY_ACTIVITY_GROUP: "has_study_activity_group",
    SoAItemType.STUDY_ACTIVITY_SUBGROUP: "has_study_activity_subgroup",
    SoAItemType.STUDY_ACTIVITY: "has_study_activity",
    SoAItemType.STUDY_ACTIVITY_INSTANCE: "has_study_activity_instance",
    SoAItemType.STUDY_ACTIVITY_SCHEDULE: "has_study_activity_schedule",
    SoAItemType.STUDY_SOA_FOOTNOTE: "has_study_footnote",
}

log = logging.getLogger(__name__)


class SoALayout(Enum):
    PROTOCOL = "protocol"
    PROTOCOL_LAB_TABLE = "protocol_lab_table"
    DETAILED = "detailed"
    OPERATIONAL = "operational"


class StudySoARepository:
    @staticmethod
    def _study_value_query(
        study_uid: str, study_value_version: str | None
    ) -> tuple[list[str], dict[str, str]]:
        """constructs a Cypher query and params for getting the StudyValue node of a given study version

        Returns:
            str: the Cypher query
            dict[str: str]: query parameters
        """

        params = {
            "study_uid": study_uid,
        }

        if study_value_version:
            params["study_value_version"] = study_value_version
            params["study_status"] = StudyStatus.RELEASED.value
            query = [
                "MATCH (study_root:StudyRoot {uid: $study_uid})-[study_version:HAS_VERSION {status: $study_status, version: $study_value_version}]->(study_value:StudyValue)"
            ]

        else:
            query = [
                "MATCH (study_root:StudyRoot {uid: $study_uid})-[study_version:LATEST]->(study_value:StudyValue)"
            ]

        return query, params

    @classmethod
    @trace_calls(args=[1, 2, 3], kwargs=["study_uid", "study_value_version", "layout"])
    def _disconnect_soa_rows(
        cls, study_uid: str, study_value_version: str, layout: SoALayout
    ):
        """Removes relationships HAS_PROTOCOL_SOA_CELL & HAS_PROTOCOL_SOA_FOOTNOTE of a given study version"""

        if layout != SoALayout.PROTOCOL:
            raise NotImplementedError("Only protocol SoA snapshot is implemented")

        sv_query, params = cls._study_value_query(study_uid, study_value_version)

        query = "\n".join(
            sv_query
            + [
                "MATCH (study_value)-[cell:HAS_PROTOCOL_SOA_CELL]->()",
                "DELETE cell",
            ]
        )
        db.cypher_query(query, params)

        query = "\n".join(
            sv_query
            + [
                "MATCH (study_value)-[fn:HAS_PROTOCOL_SOA_FOOTNOTE]->()",
                "DELETE fn",
            ]
        )
        db.cypher_query(query, params)

    @trace_calls(args=[1, 2, 3], kwargs=["study_uid", "study_value_version", "layout"])
    def load(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        layout: SoALayout = SoALayout.PROTOCOL,
    ) -> tuple[list[SoACellReference], list[SoAFootnoteReference]]:
        """Loads SoA snapshot HAS_PROTOCOL_SOA_CELL & HAS_PROTOCOL_SOA_FOOTNOTE relationships of a given study version"""

        if layout != SoALayout.PROTOCOL:
            raise NotImplementedError("Only protocol SoA snapshot is implemented")

        sv_query, params = self._study_value_query(study_uid, study_value_version)

        query = list(sv_query)
        query.append(dedent("""
            MATCH (study_value)-[cell:HAS_PROTOCOL_SOA_CELL]->(ss:StudySelection)
            RETURN cell, ss, 
               apoc.coll.sortMaps(
                   [(study_value)-[fn:HAS_PROTOCOL_SOA_FOOTNOTE]->(sfn:StudySoAFootnote)-->(ss) | {order: fn.order, symbol: fn.symbol, uid: sfn.uid}], 
                   '^order'
               ) AS sfns
            ORDER BY cell.row, cell.column, cell.order
        """).strip())

        results, _ = db.cypher_query("\n".join(query), params)

        cell_references = [self._to_soa_cell_reference(*result) for result in results]

        query = list(sv_query)
        query.append(dedent("""
            MATCH (study_value)-[fn:HAS_PROTOCOL_SOA_FOOTNOTE]->(sfn:StudySoAFootnote)
            RETURN fn, sfn
            ORDER BY fn.order
        """).strip())

        results, _ = db.cypher_query("\n".join(query), params)

        footnote_references = [
            self._to_soa_footnote_reference(*result) for result in results
        ]

        return cell_references, footnote_references

    @classmethod
    def _to_soa_cell_reference(cls, relationship, study_selection, footnotes):
        known_labels = study_selection.labels & SOA_ITEM_TYPES
        if not known_labels:
            raise RuntimeError(
                f"unknown SoAItemType: {', '.join(study_selection.labels)}"
            )
        label = next(iter(known_labels))

        return SoACellReference(
            row=relationship["row"],
            column=relationship["column"],
            span=relationship["span"],
            is_propagated=relationship["is_propagated"],
            order=relationship["order"],
            referenced_item=ReferencedItem(
                item_type=SoAItemType(label),
                item_uid=study_selection["uid"],
            ),
            footnote_references=[
                cls._to_soa_footnote_reference(footnote, footnote)
                for footnote in footnotes
                if footnote["uid"]
            ],
        )

    @staticmethod
    def _to_soa_footnote_reference(relationship, soa_footnote):
        """Returns SoAFootnoteReference obj. from "HAS_PROTOCOL_SOA_FOOTNOTE" relation and StudySoAFootnote node"""

        return SoAFootnoteReference(
            order=relationship["order"],
            symbol=relationship["symbol"],
            referenced_item=ReferencedItem(
                item_type=SoAItemType.STUDY_SOA_FOOTNOTE,
                item_uid=soa_footnote["uid"],
            ),
        )

    @classmethod
    @trace_calls(
        args=[1, 4, 5, 6],
        kwargs=["study_uid", "study_value_version", "layout", "study_status"],
    )
    @ensure_transaction(db)
    def save(
        cls,
        study_uid: str,
        cell_references: list[SoACellReference],
        footnote_references: list[SoAFootnoteReference],
        study_value_version: str | None = None,
        layout: SoALayout = SoALayout.PROTOCOL,
        study_status: StudyStatus | None = None,
    ):
        """Saves SoA snapshot HAS_PROTOCOL_SOA_CELL & HAS_PROTOCOL_SOA_FOOTNOTE relationships of a given study version"""

        if layout != SoALayout.PROTOCOL:
            raise NotImplementedError("Only protocol SoA snapshot is implemented")

        try:
            study_root: StudyRoot = StudyRoot.nodes.get(uid=study_uid)
        except DoesNotExist as e:
            raise NotFoundException("Study", study_uid) from e

        study_value: StudyValue
        if study_value_version:
            if study_status is None:
                study_status = StudyStatus.RELEASED

            try:
                study_value = study_root.has_version.match(
                    status=study_status.value, version=study_value_version
                )[0]
            except IndexError as e:
                raise NotFoundException(
                    msg=f"Study with specified uid '{study_uid}' and version '{study_value_version}' was not found."
                ) from e

        else:
            if study_status is None:
                study_status = StudyStatus.DRAFT

            study_value = study_root.latest_value.get()

        # delete previous SoA snapshot
        cls._disconnect_soa_rows(
            study_uid=study_uid, study_value_version=study_value_version, layout=layout
        )

        # save cells
        cls._save_relationship(
            relationship=study_value.has_protocol_soa_cell,
            references=cell_references,
            study_value=study_value,
        )

        # save footnotes
        cls._save_relationship(
            relationship=study_value.has_protocol_soa_footnote,
            references=footnote_references,
            study_value=study_value,
        )

        cls.manage_versioning_create(
            study_root=study_root,
            layout=layout,
            study_status=study_status,
        )

    @classmethod
    @trace_calls
    def _save_relationship(
        cls,
        relationship: RelationshipManager,
        references: Iterable[SoACellReference],
        study_value: StudyValue,
    ):
        for soa_cell_reference in references:
            referenced_item: ReferencedItem = soa_cell_reference.referenced_item

            try:
                relationship_property_name = (
                    SOA_ITEM_TYPE_TO_RELATIONSHIP_MODEL_MAME_MAP[
                        referenced_item.item_type
                    ]
                )
            except KeyError as exc:
                raise RuntimeError(
                    f"No domain model mapped for ReferencedItem type '{referenced_item.item_type}'"
                ) from exc

            try:
                ref_model: StudySelection = getattr(
                    study_value, relationship_property_name
                )
            except AttributeError as exc:
                raise RuntimeError(
                    f"Incorrect domain model mapped for ReferencedItem type '{referenced_item.item_type}', "
                    f"StudyValue has no '{relationship_property_name}'"
                ) from exc

            ref_node = ref_model.filter(uid=referenced_item.item_uid).first()

            ref_properties = {
                k: v
                for k, v in soa_cell_reference.model_dump().items()
                if k in {"row", "column", "span", "is_propagated", "order", "symbol"}
                and v is not None
            }

            relationship.connect(ref_node, ref_properties)

    @staticmethod
    def manage_versioning_create(
        study_root: StudyRoot,
        layout: SoALayout = SoALayout.PROTOCOL,
        study_status: StudyStatus = StudyStatus.DRAFT,
    ):
        action = UpdateSoASnapshot(
            date=datetime.datetime.now(datetime.timezone.utc),
            status=study_status.value,
            author_id=user().id(),
            object_type=f"{layout.value} SoA",
        )
        action.save()
        study_root.audit_trail.connect(action)

    @classmethod
    @trace_calls(
        args=[1, 2, 3], kwargs=["study_uid", "study_value_version", "get_instances"]
    )
    def query_study_activities(
        cls,
        study_uid: str,
        study_value_version: str | None = None,
        get_instances: bool = False,
    ):
        query, params = cls._study_value_query(study_uid, study_value_version)
        params["requested_library_name"] = settings.requested_library_name

        query.append(queries.study_standard_version_ct_terms_datetime)

        query.append(dedent("""
            MATCH (study_value)-[:HAS_STUDY_ACTIVITY]->
                (study_activity:StudyActivity)-[:HAS_SELECTED_ACTIVITY]->
                (activity_value:ActivityValue)<-[:HAS_VERSION]-
                (activity_root:ActivityRoot)<-[:CONTAINS_CONCEPT]-
                (act_library:Library)

            MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->
                (study_soa_group:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->
                (:CTTermContext)-[:HAS_SELECTED_TERM]->
                (soa_group_term_root:CTTermRoot)
            WHERE (study_soa_group)<-[:HAS_STUDY_SOA_GROUP]-(study_value)
        """))

        query.append(
            queries.ct_term_name_at_datetime.format(
                root="soa_group_term_root",
                value="soa_group_term_name",
            )
        )

        query.append(dedent("""
            OPTIONAL MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->
                (study_activity_group:StudyActivityGroup)-[:HAS_SELECTED_ACTIVITY_GROUP]->
                (activity_group_value:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot)
            WHERE (study_activity_group)<-[:HAS_STUDY_ACTIVITY_GROUP]-(study_value)

            OPTIONAL MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->
                (study_activity_subgroup:StudyActivitySubGroup)-[:HAS_SELECTED_ACTIVITY_SUBGROUP]->
                (activity_subgroup_value:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot)
            WHERE (study_activity_subgroup)<-[:HAS_STUDY_ACTIVITY_SUBGROUP]-(study_value)
        """))

        if get_instances:
            query.append(dedent("""
            OPTIONAL MATCH (study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]->
                (study_activity_instance:StudyActivityInstance)
            WHERE (study_activity_instance)<-[:HAS_STUDY_ACTIVITY_INSTANCE]-(study_value)

            OPTIONAL MATCH (study_activity_instance)-[:HAS_SELECTED_ACTIVITY_INSTANCE]->
                (activity_instance_value:ActivityInstanceValue)<-[:HAS_VERSION]-
                (activity_instance_root:ActivityInstanceRoot)<-[:CONTAINS_CONCEPT]-
                (act_inst_library:Library)

            OPTIONAL MATCH (activity_instance_value:ActivityInstanceValue)-[:ACTIVITY_INSTANCE_CLASS]->
                (activity_instance_class_root:ActivityInstanceClassRoot)-[:LATEST]->
                (activity_instance_class_latest_value:ActivityInstanceClassValue)
            """))

        query.append(dedent("""
            WITH DISTINCT *
            ORDER BY COALESCE(study_soa_group.order, 0), COALESCE(study_activity_group.order, 0),
                COALESCE(study_activity_subgroup.order, 0), COALESCE(study_activity.order, 0)
        """))
        if get_instances:
            # Use COALESCE to handle NULL instance orders for placeholders without instances
            query.append(", COALESCE(study_activity_instance.order, 0)")

        query.append(dedent("""
            RETURN {
                study_activity_uid: study_activity.uid,
                activity: {
                    uid: activity_root.uid,
                    name: activity_value.name,
                    name_sentence_case: activity_value.name_sentence_case,
                    is_data_collected: COALESCE(activity_value.is_data_collected, false),
                    is_request_rejected: COALESCE(activity_value.is_request_rejected, false),
                    is_request_final: COALESCE(activity_value.is_request_final, false),
                    is_multiple_selection_allowed: COALESCE(activity_value.is_multiple_selection_allowed, true),
                    library_name: act_library.name
                },
                accepted_version: study_activity.accepted_version,
                keep_old_version: COALESCE(study_activity.keep_old_version, false),
            """))
        if get_instances:
            query.append(dedent("""
                study_activity_instance_uid: study_activity_instance.uid,
                activity_instance: CASE WHEN activity_instance_root IS NOT NULL THEN {
                    uid: activity_instance_root.uid,
                    name: activity_instance_value.name,
                    name_sentence_case: activity_instance_value.name_sentence_case,
                    definition: activity_instance_value.definition,
                    abbreviation: activity_instance_value.abbreviation,
                    topic_code: activity_instance_value.topic_code,
                    adam_param_code: activity_instance_value.adam_param_code,
                    is_derived: COALESCE(activity_instance_value.is_derived, false),
                    is_default_selected_for_activity: COALESCE(activity_instance_value.is_default_selected_for_activity, false),
                    is_data_sharing: COALESCE(activity_instance_value.is_data_sharing, false),
                    is_required_for_activity: COALESCE(activity_instance_value.is_required_for_activity, false),
                    is_research_lab: COALESCE(activity_instance_value.is_research_lab, false),
                    is_legacy_usage: COALESCE(activity_instance_value.is_legacy_usage, false),
                    library_name: act_inst_library.name,
                    activity_instance_class: {
                        uid: activity_instance_class_root.uid,
                        name: activity_instance_class_latest_value.name
                    }
                } ELSE null END,
                state: CASE
                    WHEN activity_value.is_data_collected THEN
                        CASE
                            WHEN activity_instance_root.uid IS NOT NULL THEN
                                CASE
                                    WHEN activity_instance_value.is_required_for_activity THEN 'Review not needed'
                                    WHEN study_activity_instance.is_reviewed THEN 'Reviewed'
                                    ELSE 'Review needed'
                                END
                            ELSE 'Add instance'
                        END
                    ELSE 'Not applicable'
                END,
                is_reviewed: coalesce(study_activity_instance.is_reviewed, false),
                show_activity_instance_in_protocol_flowchart: COALESCE(study_activity_instance.show_activity_instance_in_protocol_flowchart, false),
                is_important: COALESCE(study_activity_instance.is_important, false),
                order: study_activity_instance.order,
            """))
        else:
            query.append("    order: study_activity.order,")
        query.append(dedent("""
                show_activity_in_protocol_flowchart: study_activity.show_activity_in_protocol_flowchart,
                show_activity_group_in_protocol_flowchart: COALESCE(study_activity_group.show_activity_group_in_protocol_flowchart, false),
                show_activity_subgroup_in_protocol_flowchart: COALESCE(study_activity_subgroup.show_activity_subgroup_in_protocol_flowchart, false),
                show_soa_group_in_protocol_flowchart: COALESCE(study_soa_group.show_soa_group_in_protocol_flowchart, false),
                study_activity_subgroup: {
                    study_activity_subgroup_uid: study_activity_subgroup.uid,
                    activity_subgroup_uid: activity_subgroup_root.uid,
                    activity_subgroup_name: activity_subgroup_value.name,
                    order: study_activity_subgroup.order
                },
                study_activity_group: {
                    study_activity_group_uid: study_activity_group.uid,
                    activity_group_uid: activity_group_root.uid,
                    activity_group_name: activity_group_value.name,
                    order: study_activity_group.order
                },
                study_soa_group: {
                    study_soa_group_uid: study_soa_group.uid,
                    soa_group_term_uid: soa_group_term_root.uid,
                    soa_group_term_name: soa_group_term_name.name,
                    order: study_soa_group.order
                },
                study_uid: study_root.uid,
                study_version: study_version.version
            } AS selection
        """))

        results, headers = db.cypher_query("\n".join(query), params=params)
        return results, headers
