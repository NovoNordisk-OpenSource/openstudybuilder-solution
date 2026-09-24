import copy
from dataclasses import dataclass, fields, replace
from datetime import date as date_type
from datetime import datetime, time, timezone
from decimal import Decimal
from typing import Any, Mapping, MutableSequence, Sequence, cast, overload

from neomodel import db
from neomodel.exceptions import DoesNotExist
from neomodel.sync_.match import Path
from neomodel.sync_.node import NodeMeta

from clinical_mdr_api import utils
from clinical_mdr_api.domain_repositories._utils.helpers import (
    acquire_write_lock_study_value,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_attributes_repository import (
    CTCodelistAttributesRepository,
)
from clinical_mdr_api.domain_repositories.generic_repository import RepositoryImpl
from clinical_mdr_api.domain_repositories.models._utils import (
    format_generic_header_values,
)
from clinical_mdr_api.domain_repositories.models.concepts import UnitDefinitionRoot
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermContext,
    CTTermRoot,
    MetaStudyField,
)
from clinical_mdr_api.domain_repositories.models.dictionary import DictionaryTermRoot
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrRel,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.project import Project
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
    StudyAction,
)
from clinical_mdr_api.domain_repositories.models.study_field import (
    StudyArrayField,
    StudyBooleanField,
    StudyField,
    StudyIntField,
    StudyProjectField,
    StudyTextField,
    StudyTimeField,
)
from clinical_mdr_api.domain_repositories.models.study_visit import StudyVisit
from clinical_mdr_api.domain_repositories.study_definitions.study_definition_repository import (
    StudyDefinitionRepository,
)
from clinical_mdr_api.domains.study_definition_aggregates.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domains.study_definition_aggregates.root import (
    StudyDefinitionSnapshot,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_configuration import (
    FieldConfiguration,
    StudyFieldType,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    HighLevelStudyDesignVO,
    StudyDescriptionVO,
    StudyFieldAuditTrailActionVO,
    StudyFieldAuditTrailEntryAR,
    StudyIdentificationMetadataVO,
    StudyInterventionVO,
    StudyMetadataVO,
    StudyPopulationVO,
    StudyStatus,
    StudyVersionMetadataVO,
)
from clinical_mdr_api.models.study_selections.study import (
    StudyOtherAttributeColumns,
    StudyPreferredTimeUnit,
    StudySoaPreferencesInput,
    StudySubpartAuditTrail,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    calculate_total_count_from_query_result,
    validate_filters_and_add_search_string,
)
from clinical_mdr_api.services._utils import calculate_diffs
from clinical_mdr_api.services.user_info import UserInfoService
from common import exceptions
from common.config import settings
from common.telemetry import trace_calls
from common.utils import convert_to_datetime, validate_max_skip_clause

MAINTAIN_RELATIONSHIPS_FOR_NEW_STUDY_VALUE = {
    "belongs_to_study_parent_part",
    "has_study_data_supplier",
    "has_study_activity",
    "has_study_activity_group",
    "has_study_activity_instance",
    "has_study_activity_instruction",
    "has_study_activity_schedule",
    "has_study_activity_subgroup",
    "has_study_arm",
    "has_study_branch_arm",
    "has_study_cohort",
    "has_study_compound",
    "has_study_compound_dosing",
    "has_study_criteria",
    "has_study_design_cell",
    "has_study_design_class",
    "has_study_disease_milestone",
    "has_study_element",
    "has_study_endpoint",
    "has_study_epoch",
    "has_study_footnote",
    "has_study_objective",
    "has_study_soa_group",
    "has_study_standard_version",
    "has_study_subpart",
    "has_study_visit",
}


def _is_metadata_snapshot_and_status_equal_comparing_study_value_properties(
    current: StudyDefinitionSnapshot, previous: StudyDefinitionSnapshot
) -> bool:
    """
    A convenience function for comparing two snapshot for equality of StudyValue node properties.
    :param current: A StudyDefinitionSnapshot to compare.
    :param previous: Another StudyDefinitionSnapshot to compare.
    :return: True if current == previous (comparing StudyValue node properties), otherwise False
    """
    return (
        current.current_metadata.id_metadata.study_number
        == previous.current_metadata.id_metadata.study_number
        and current.current_metadata.id_metadata.subpart_id
        == previous.current_metadata.id_metadata.subpart_id
        and current.current_metadata.id_metadata.study_acronym
        == previous.current_metadata.id_metadata.study_acronym
        and current.current_metadata.id_metadata.study_subpart_acronym
        == previous.current_metadata.id_metadata.study_subpart_acronym
        and current.current_metadata.id_metadata.study_id_prefix
        == previous.current_metadata.id_metadata.study_id_prefix
        and current.current_metadata.id_metadata.description
        == previous.current_metadata.id_metadata.description
        and current.study_status == previous.study_status
        and current.released_metadata == previous.released_metadata
    )


@dataclass(frozen=True)
class _AdditionalClosure:
    root: StudyRoot
    value: StudyValue
    latest_value: ClinicalMdrRel
    latest_draft: VersionRelationship
    latest_released: VersionRelationship | None
    latest_locked: VersionRelationship | None
    previous_snapshot: StudyDefinitionSnapshot


class StudyDefinitionRepositoryImpl(StudyDefinitionRepository, RepositoryImpl):
    def __init__(self, author_id):
        super().__init__()
        self.audit_info.author_id = author_id

    @classmethod
    def _retrieve_draft_study_metadata_snapshot(
        cls,
        latest_draft_value: StudyValue,
        latest_draft_relationship: VersionRelationship,
    ) -> StudyMetadataVO:
        draft_metadata_snapshot = cls._study_metadata_snapshot_from_study_value(
            latest_draft_value
        )
        draft_metadata_snapshot = (
            cls._assign_snapshot_ver_properties_from_ver_relationship(
                snapshot=draft_metadata_snapshot,
                ver_relationship=latest_draft_relationship,
            )
        )
        return draft_metadata_snapshot

    @classmethod
    def _retrieve_current_study_metadata_snapshot(
        cls,
        latest_draft_relationship: VersionRelationship,
        draft_snapshot: StudyMetadataVO,
        latest_locked_relationship: VersionRelationship | None,
        locked_snapshot: StudyMetadataVO | None,
    ):
        current_metadata_snapshot: StudyMetadataVO | None

        # some parts of current metadata metadata (those regarding version info) are stored in different way
        # in the underlying DB depending whether current version is draft version or locked
        # so we must retrieve those in different way
        if latest_draft_relationship.end_date is None:
            # in draft we do not need author and info (these are only in db for audit not for business logic)
            # just version timestamp
            current_metadata_snapshot = draft_snapshot
        else:
            # but we need those if current is non-DRAFT (i.e. LOCKED)
            assert latest_locked_relationship is not None
            current_metadata_snapshot = locked_snapshot
        return current_metadata_snapshot

    @classmethod
    def _retrieve_released_study_metadata_snapshot(
        cls, latest_released_value: StudyValue | None, latest_released_relationship
    ) -> StudyMetadataVO | None:
        released: StudyMetadataVO | None = None
        if latest_released_relationship is not None:
            assert latest_released_value is not None
            released = cls._study_metadata_snapshot_from_study_value(
                latest_released_value
            )
            assert released is not None
            released = cls._assign_snapshot_ver_properties_from_ver_relationship(
                snapshot=released, ver_relationship=latest_released_relationship
            )

        return released

    @classmethod
    def _retrieve_locked_study_metadata_snapshot(
        cls,
        locked_study_value: StudyValue | None,
        locked_relationship: VersionRelationship | None,
    ) -> StudyMetadataVO | None:
        locked: StudyMetadataVO | None = None
        if locked_study_value and locked_relationship:
            locked = cls._study_metadata_snapshot_from_study_value(locked_study_value)
            locked = cls._assign_snapshot_ver_properties_from_ver_relationship(
                snapshot=locked, ver_relationship=locked_relationship
            )
        return locked

    @classmethod
    def _retrieve_locked_study_metadata_snapshots(
        cls, root: StudyRoot
    ) -> MutableSequence[StudyMetadataVO]:
        # now we must retrieve locked versions
        # this is tricky since match gives us the list of values (not relationships)
        # although not very probable however it's possible that two consecutive locked version
        # are actually locked with the same value node
        locked_metadata_snapshots: list[StudyMetadataVO] = []
        locked_value_node: StudyValue
        # so we get locked value nodes first
        # however there is a problem. neomodel returns them many times if there are multiple relationship instances
        # between them. There for we must remember ids of processed nodes, to skip subsequent processing of the same
        # node.
        processed_nodes = set()
        for locked_value_node in root.has_version.match(
            status=StudyStatus.LOCKED.value
        ):
            # then for every value we get has_version_relationship which are LOCKED
            if locked_value_node.element_id in processed_nodes:
                # we skip processing in case we already have it processed
                continue
            # if we haven't processed it yet we process (and store it as processed)
            processed_nodes.add(locked_value_node.element_id)

            # here goes the real processing
            has_version_relationship_instance: VersionRelationship
            for has_version_relationship_instance in root.has_version.all_relationships(
                locked_value_node
            ):
                if has_version_relationship_instance.status == StudyStatus.LOCKED.value:
                    locked = cls._retrieve_locked_study_metadata_snapshot(
                        locked_study_value=locked_value_node,
                        locked_relationship=has_version_relationship_instance,
                    )
                    if locked:
                        locked_metadata_snapshots.append(locked)

        # now we have all locked metadata snapshot in locked_metadata_snapshots list. However in indeterminate order
        # and aggregate want them chronological. So we need to sort the list by version_timestamp
        locked_metadata_snapshots.sort(
            key=lambda _: cast(datetime, _.ver_metadata.version_timestamp)
        )

        return locked_metadata_snapshots

    @classmethod
    def _retrieve_all_snapshots_from_cypher_query_result(
        cls, result_set: list[dict[Any, Any]], deleted: bool = False
    ) -> list[StudyDefinitionSnapshot]:
        """
        Function maps the result of the cypher query which is list of dictionaries into
        the list of StudyDefinitionSnapshots holding StudyMetadataVO instances.
        :param result_set:
        :return list[StudyDefinitionSnapshot]:
        """
        snapshots: list[StudyDefinitionSnapshot] = []
        for study in result_set:
            current_metadata_snapshot = cls._study_metadata_snapshot_from_cypher_res(
                study["current_metadata"]
            )
            released_metadata_snapshot = cls._study_metadata_snapshot_from_cypher_res(
                study["released_metadata"]
            )
            draft_metadata_snapshot = cls._study_metadata_snapshot_from_cypher_res(
                study["draft_metadata"]
            )
            locked_metadata_versions = (
                study["locked_metadata_versions"]["locked_metadata_array"]
                if study["locked_metadata_versions"] is not None
                else []
            )
            locked_metadata_snapshots = [
                cls._study_metadata_snapshot_from_cypher_res(locked_metadata)
                for locked_metadata in locked_metadata_versions
            ]
            snapshot = StudyDefinitionSnapshot(
                deleted=deleted,
                current_metadata=current_metadata_snapshot,
                released_metadata=released_metadata_snapshot,
                draft_metadata=draft_metadata_snapshot,
                locked_metadata_versions=locked_metadata_snapshots,
                uid=study["uid"],
                study_parent_part_uid=study["study_parent_part_uid"],
                study_subpart_uids=study["study_subpart_uids"],
                study_status=(
                    study["study_status"] if not deleted else StudyStatus.DELETED.value
                ),
            )
            snapshots.append(snapshot)
        return snapshots

    @staticmethod
    def _ensure_transaction() -> None:
        """ensures a Neomodel database transaction is active"""

        if getattr(db, "_active_transaction", None) is None:
            raise SystemError(
                "Must be called inside an active Neomodel database transaction to retrieve StudyDefinition for update."
            )

    def _retrieve_snapshot_by_uid(
        self,
        uid: str,
        for_update: bool,
        study_value_version: str | None = None,
    ) -> tuple[StudyDefinitionSnapshot | None, Any]:
        if for_update:
            self._ensure_transaction()
            acquire_write_lock_study_value(uid)

            # we should be able to return deleted studies
            # but it should not be possible to be edited
            exceptions.BusinessLogicException.raise_if(
                self.check_if_study_is_deleted(study_uid=uid),
                msg=f"Study with UID '{uid}' is deleted.",
            )

        root: StudyRoot

        try:
            root = StudyRoot.nodes.get(uid=uid)
        except DoesNotExist:
            return None, None

        snapshot, closure = self._retrieve_snapshot(
            root, for_update=for_update, study_value_version=study_value_version
        )
        if snapshot is None:
            return None, None
        return snapshot, closure

    @classmethod
    def _retrieve_snapshot(
        cls,
        root: StudyRoot,
        for_update: bool = False,
        study_value_version: str | None = None,
    ) -> tuple[StudyDefinitionSnapshot | None, _AdditionalClosure | None]:
        """
        Optimized snapshot retrieval that consolidates multiple neomodel
        traversals into a single Cypher query for version pointers and relationships,
        then fetches field data only for the needed StudyValue nodes.
        When for_update=True, also inflates relationship objects to build _AdditionalClosure.
        """
        # Single Cypher query to fetch all version pointers, relationships, and parent/subpart info
        rs, columns = db.cypher_query(
            """
            MATCH (sr:StudyRoot {uid: $uid})
            OPTIONAL MATCH (sr)-[ld:LATEST_DRAFT]->(ld_val:StudyValue)
            OPTIONAL MATCH (sr)-[lv:LATEST]->(lv_val:StudyValue)
            OPTIONAL MATCH (sr)-[lr:LATEST_RELEASED]->(lr_val:StudyValue)
            OPTIONAL MATCH (sr)-[ll:LATEST_LOCKED]->(ll_val:StudyValue)
            OPTIONAL MATCH (parent_root:StudyRoot)-[:LATEST]->(:StudyValue)
                -[:HAS_STUDY_SUBPART]->(:StudyValue)<-[:LATEST]-(sr)
            OPTIONAL MATCH (sr)-[:LATEST]->(sv_latest:StudyValue)
                -[:HAS_STUDY_SUBPART]->(:StudyValue)<-[:LATEST]-(sub_root:StudyRoot)
                WHERE NOT EXISTS((sub_root)-[:AUDIT_TRAIL]->(:StudyAction:Delete)-[:BEFORE]->(:StudyValue)<-[:LATEST]-(sub_root))
            WITH sr, ld, ld_val, lv, lv_val, lr, lr_val, ll, ll_val,
                 parent_root.uid AS parent_uid,
                 collect(DISTINCT sub_root.uid) AS subpart_uids
            OPTIONAL MATCH (sr)-[hv:HAS_VERSION {status: 'LOCKED'}]->(hv_val:StudyValue)
            WITH sr, ld, ld_val, lv, lv_val, lr, lr_val, ll, ll_val, parent_uid, subpart_uids,
                 collect(DISTINCT {
                    val_id: elementId(hv_val),
                    start_date: hv.start_date,
                    end_date: hv.end_date,
                    version: hv.version,
                    status: hv.status,
                    author_id: hv.author_id,
                    change_description: hv.change_description
                 }) AS locked_versions
            OPTIONAL MATCH (sr)-[sv_rel:HAS_VERSION]->(sv_val:StudyValue)
                WHERE sv_rel.version = $study_value_version
                AND sv_rel.status IN ['LOCKED', 'RELEASED']
            WITH sr, ld, ld_val, lv, lv_val, lr, lr_val, ll, ll_val,
                 parent_uid, subpart_uids, locked_versions,
                 collect(DISTINCT {
                    val_id: elementId(sv_val),
                    start_date: sv_rel.start_date,
                    version: sv_rel.version,
                    status: sv_rel.status,
                    author_id: sv_rel.author_id,
                    change_description: sv_rel.change_description
                 }) AS specific_versions
            RETURN
                elementId(ld_val) AS draft_val_id,
                ld.start_date AS draft_start, ld.end_date AS draft_end,
                ld.version AS draft_version, ld.status AS draft_status,
                ld.author_id AS draft_author_id, ld.change_description AS draft_change_desc,
                elementId(lr_val) AS released_val_id,
                lr.start_date AS released_start,
                lr.version AS released_version, lr.status AS released_status,
                lr.author_id AS released_author_id, lr.change_description AS released_change_desc,
                parent_uid, subpart_uids,
                locked_versions,
                specific_versions,
                ld, lv, lv_val, lr, ll
            """,
            params={"uid": root.uid, "study_value_version": study_value_version},
        )

        if not rs or not rs[0]:
            return None, None

        row = dict(zip(columns, rs[0]))
        draft_val_id = row["draft_val_id"]
        draft_start, draft_end = row["draft_start"], row["draft_end"]
        draft_version, draft_status = row["draft_version"], row["draft_status"]
        draft_author_id, draft_change_desc = (
            row["draft_author_id"],
            row["draft_change_desc"],
        )
        released_info: dict[str, Any] = {
            "val_id": row["released_val_id"],
            "start_date": row["released_start"],
            "version": row["released_version"],
            "status": row["released_status"],
            "author_id": row["released_author_id"],
            "change_description": row["released_change_desc"],
        }
        parent_uid = row["parent_uid"]
        subpart_uids = row["subpart_uids"] or []
        locked_versions_raw = row["locked_versions"] or []
        specific_versions_raw = row["specific_versions"] or []
        raw_ld_rel = row["ld"]
        raw_lv_rel = row["lv"]
        raw_lv_val = row["lv_val"]
        raw_lr_rel = row["lr"]
        raw_ll_rel = row["ll"]

        if draft_val_id is None:
            return None, None

        # Validate specific version if requested
        if study_value_version:
            # Filter to entries that actually matched (val_id is not None)
            specific_versions_raw = [
                sv for sv in specific_versions_raw if sv and sv.get("val_id")
            ]
            if not specific_versions_raw:
                raise exceptions.NotFoundException(
                    f"There is no Locked or Released version with version '{study_value_version}' for study with uid '{root.uid}'"
                )

        # Collect unique StudyValue element IDs that we need to fetch field data for
        val_ids_to_fetch: set[str] = set()
        val_ids_to_fetch.add(draft_val_id)
        if released_info["val_id"]:
            val_ids_to_fetch.add(released_info["val_id"])
        # Also add locked version value IDs
        for lv_entry in locked_versions_raw:
            if lv_entry and lv_entry.get("val_id"):
                val_ids_to_fetch.add(lv_entry["val_id"])
        # Also add specific version value ID
        for sv_entry in specific_versions_raw:
            if sv_entry and sv_entry.get("val_id"):
                val_ids_to_fetch.add(sv_entry["val_id"])

        # Fetch StudyValue nodes by element ID (batch)
        val_nodes: dict[str, StudyValue] = {}
        if val_ids_to_fetch:
            fetched_nodes, _ = db.cypher_query(
                """
                UNWIND $ids AS eid
                MATCH (sv:StudyValue) WHERE elementId(sv) = eid
                RETURN elementId(sv), sv
                """,
                params={"ids": list(val_ids_to_fetch)},
            )
            for node_row in fetched_nodes:
                sv_node = StudyValue.inflate(node_row[1])
                val_nodes[node_row[0]] = sv_node

        # Build draft metadata snapshot
        draft_value_node = val_nodes.get(draft_val_id)
        if draft_value_node is None:
            return None, None
        draft_metadata_snapshot = cls._study_metadata_snapshot_from_study_value(
            draft_value_node
        )
        draft_metadata_snapshot = cls._assign_snapshot_ver_properties_from_raw(
            draft_metadata_snapshot,
            draft_start,
            draft_version,
            draft_status,
            draft_author_id,
            draft_change_desc,
        )

        # Build released metadata snapshot
        released_metadata_snapshot = None
        if released_info["val_id"] and released_info["val_id"] in val_nodes:
            released_value_node = val_nodes[released_info["val_id"]]
            released_metadata_snapshot = cls._study_metadata_snapshot_from_study_value(
                released_value_node
            )
            released_metadata_snapshot = cls._assign_snapshot_ver_properties_from_raw(
                released_metadata_snapshot,
                released_info["start_date"],
                released_info["version"],
                released_info["status"],
                released_info["author_id"],
                released_info["change_description"],
            )

        # Build locked metadata snapshots
        locked_metadata_snapshots: list[StudyMetadataVO] = []
        processed_locked: set[tuple[str, str | None]] = set()
        for lv_entry in locked_versions_raw:
            if not lv_entry or not lv_entry.get("val_id"):
                continue
            lv_val_id = lv_entry["val_id"]
            lv_version = lv_entry.get("version")
            dedup_key = (lv_val_id, lv_version)
            if dedup_key in processed_locked:
                continue
            processed_locked.add(dedup_key)
            lv_node = val_nodes.get(lv_val_id)
            if lv_node is None:
                continue
            locked_snap = cls._study_metadata_snapshot_from_study_value(lv_node)
            locked_snap = cls._assign_snapshot_ver_properties_from_raw(
                locked_snap,
                lv_entry.get("start_date"),
                lv_version,
                StudyStatus.LOCKED.value,
                lv_entry.get("author_id"),
                lv_entry.get("change_description"),
            )
            locked_metadata_snapshots.append(locked_snap)
        locked_metadata_snapshots.sort(
            key=lambda s: cast(datetime, s.ver_metadata.version_timestamp)
        )

        # Build specific metadata snapshot if a version was requested
        specific_metadata_snapshot: StudyMetadataVO | None = None
        if study_value_version and specific_versions_raw:
            # Prefer LOCKED over RELEASED
            chosen = None
            for sv_entry in specific_versions_raw:
                if sv_entry.get("status") == StudyStatus.LOCKED.value:
                    chosen = sv_entry
                    break
            if chosen is None:
                chosen = specific_versions_raw[0]
            sv_node = val_nodes.get(chosen["val_id"])
            if sv_node is not None:
                specific_metadata_snapshot = (
                    cls._study_metadata_snapshot_from_study_value(sv_node)
                )
                specific_metadata_snapshot = (
                    cls._assign_snapshot_ver_properties_from_raw(
                        specific_metadata_snapshot,
                        chosen.get("start_date"),
                        chosen.get("version"),
                        chosen.get("status"),
                        chosen.get("author_id"),
                        chosen.get("change_description"),
                    )
                )

        # Determine current metadata
        if draft_end is None:
            current_metadata_snapshot = draft_metadata_snapshot
        else:
            current_metadata_snapshot = (
                locked_metadata_snapshots[-1]
                if locked_metadata_snapshots
                else draft_metadata_snapshot
            )

        snapshot = StudyDefinitionSnapshot(
            deleted=False,
            current_metadata=current_metadata_snapshot,
            draft_metadata=draft_metadata_snapshot,
            released_metadata=released_metadata_snapshot,
            specific_metadata=specific_metadata_snapshot,
            locked_metadata_versions=locked_metadata_snapshots,
            uid=root.uid,
            study_parent_part_uid=parent_uid,
            study_subpart_uids=subpart_uids,
            study_status=(
                StudyStatus.DRAFT.value
                if draft_end is None
                else StudyStatus.LOCKED.value
            ),
        )

        # Build _AdditionalClosure for update flow by inflating raw relationship objects
        closure: _AdditionalClosure | None = None
        if for_update:
            latest_value_node = (
                StudyValue.inflate(raw_lv_val) if raw_lv_val else draft_value_node
            )
            closure = _AdditionalClosure(
                root=root,
                value=latest_value_node,
                latest_value=(
                    cast(ClinicalMdrRel, ClinicalMdrRel.inflate(raw_lv_rel))
                    if raw_lv_rel
                    else cast(ClinicalMdrRel, VersionRelationship.inflate(raw_ld_rel))
                ),
                latest_draft=cast(
                    VersionRelationship, VersionRelationship.inflate(raw_ld_rel)
                ),
                latest_released=(
                    cast(VersionRelationship, VersionRelationship.inflate(raw_lr_rel))
                    if raw_lr_rel
                    else None
                ),
                latest_locked=(
                    cast(VersionRelationship, VersionRelationship.inflate(raw_ll_rel))
                    if raw_ll_rel
                    else None
                ),
                previous_snapshot=copy.deepcopy(snapshot),
            )

        return snapshot, closure

    def _save(
        self,
        snapshot: StudyDefinitionSnapshot,
        additional_closure: Any,
        is_subpart_relationship_update: bool = False,
    ) -> None:
        self._ensure_transaction()  # raises an error if we are not inside transaction

        assert isinstance(
            additional_closure, _AdditionalClosure
        )  # this should always hold here

        # convenience variables (those not used are commented out, however may become useful later)
        current_snapshot: StudyDefinitionSnapshot = snapshot
        previous_snapshot: StudyDefinitionSnapshot = (
            additional_closure.previous_snapshot
        )
        previous_value: StudyValue = additional_closure.value
        latest_draft: VersionRelationship = additional_closure.latest_draft
        latest_released: VersionRelationship | None = additional_closure.latest_released
        latest_locked: VersionRelationship | None = additional_closure.latest_locked
        root: StudyRoot = additional_closure.root
        date = datetime.now(timezone.utc)

        # we do nothing if nothing changed
        if previous_snapshot == current_snapshot and not is_subpart_relationship_update:
            return

        # generate :StudyAction:Delete node
        if current_snapshot.deleted:
            self._generate_study_value_audit_node(
                study_root_node=root,
                study_value_node_after=None,
                study_value_node_before=previous_value,
                change_status=None,
                author_id=self.audit_info.author_id,
                date=date,
            )
            return

        # some assertions about what and how can things be or change (current implementation is built on those
        # assumptions and may break if they not hold)
        assert (
            current_snapshot.current_metadata is not None
        )  # there must be some current value
        assert previous_snapshot.current_metadata  # in previous snapshot as well
        # there are only two possible permanent current states of the aggregate
        assert current_snapshot.study_status in (
            StudyStatus.DRAFT.value,
            StudyStatus.LOCKED.value,
        )
        assert (
            current_snapshot.uid == previous_snapshot.uid
        )  # uid cannot change (something is very wrong if it does)

        # locked metadata which had been persisted before do not change
        if (
            len(current_snapshot.locked_metadata_versions) > 0
            and len(previous_snapshot.locked_metadata_versions) > 0
        ):
            assert (
                current_snapshot.locked_metadata_versions[0]
                == previous_snapshot.locked_metadata_versions[0]
            )
        assert (
            current_snapshot.locked_metadata_versions[
                0 : len(previous_snapshot.locked_metadata_versions)
            ]
            == previous_snapshot.locked_metadata_versions
        )

        # first we maintain latest_value (possibly creating new value node)
        expected_latest_value = self._maintain_latest_value_and_relationship_on_save(
            current_snapshot=current_snapshot,
            previous_snapshot=previous_snapshot,
            previous_value=previous_value,
            root=root,
            date=date,
            is_subpart_relationship_update=is_subpart_relationship_update,
        )

        # now we maintain all types of relationship we have in DB to the study.

        self._maintain_latest_draft_relationship_on_save(
            expected_latest_value=expected_latest_value,
            latest_draft_relationship=latest_draft,
            root=root,
            current_snapshot=current_snapshot,
        )
        self._maintain_latest_locked_relationship_on_save(
            expected_latest_value=expected_latest_value,
            latest_locked=latest_locked,
            previous_snapshot=previous_snapshot,
            root=root,
            current_snapshot=current_snapshot,
        )
        self._maintain_latest_released_relationship_on_save(
            current_snapshot=current_snapshot,
            latest_released=latest_released,
            previous_snapshot=previous_snapshot,
            root=root,
            previous_value=previous_value,
            expected_latest_value=expected_latest_value,
        )
        self._maintain_has_version_relationship_on_save(
            expected_latest_value=expected_latest_value,
            root=root,
            current_snapshot=current_snapshot,
            previous_snapshot=previous_snapshot,
            previous_latest_value=previous_value,
        )

        # Next, persist and maintain the study fields as nodes in the graph.
        self._maintain_study_project_field_relationship(
            root,
            previous_snapshot,
            current_snapshot,
            previous_value,
            expected_latest_value,
            date,
        )
        self._maintain_study_fields_relationships(
            root,
            previous_snapshot,
            current_snapshot,
            previous_value,
            expected_latest_value,
            date,
        )
        self._maintain_study_array_fields_relationships(
            root,
            previous_snapshot,
            current_snapshot,
            previous_value,
            expected_latest_value,
            date,
        )
        self._maintain_study_registry_id_fields_relationships(
            root,
            previous_snapshot,
            current_snapshot,
            previous_value,
            expected_latest_value,
            date,
        )
        for rel in MAINTAIN_RELATIONSHIPS_FOR_NEW_STUDY_VALUE:
            self._maintain_study_relationship_on_save(
                rel, expected_latest_value, previous_value
            )
        self._maintain_study_pref_time_unit_relationship_on_save(
            expected_latest_value=expected_latest_value, previous_value=previous_value
        )
        self._maintain_study_soa_preferences_relationship_on_save(
            expected_latest_value=expected_latest_value, previous_value=previous_value
        )
        self._maintain_study_soa_split_relationship_on_save(
            expected_latest_value=expected_latest_value, previous_value=previous_value
        )

    def _maintain_study_relationship_on_save(
        self,
        relation_name: str,
        expected_latest_value: StudyValue,
        previous_value: StudyValue,
    ):
        # check if new value node is created
        if expected_latest_value is not previous_value:
            study_selection_nodes = getattr(previous_value, relation_name).all()
            if relation_name not in MAINTAIN_RELATIONSHIPS_FOR_NEW_STUDY_VALUE:
                # remove the relation from the old value node
                getattr(previous_value, relation_name).disconnect_all()
            # add the relation to the new node
            for study_selection_node in study_selection_nodes:
                if relation_name in [
                    "has_study_subpart",
                    "belongs_to_study_parent_part",
                ]:
                    if study_selection_node.latest_value.single():
                        getattr(expected_latest_value, relation_name).connect(
                            study_selection_node
                        )
                else:
                    getattr(expected_latest_value, relation_name).connect(
                        study_selection_node
                    )

    def _maintain_study_pref_time_unit_relationship_on_save(
        self, expected_latest_value: StudyValue, previous_value: StudyValue
    ):
        # check if new value node is created
        if expected_latest_value is not previous_value:
            # remove the relation from the old value node
            preferred_time_unit_node = previous_value.has_time_field.get_or_none(
                field_name=settings.study_field_preferred_time_unit_name
            )
            soa_preferred_time_unit_node = previous_value.has_time_field.get_or_none(
                field_name=settings.study_field_soa_preferred_time_unit_name
            )
            if preferred_time_unit_node is not None:
                # add the relation to the new node
                expected_latest_value.has_time_field.connect(preferred_time_unit_node)

            if soa_preferred_time_unit_node is not None:
                # add the relation to the new node
                expected_latest_value.has_time_field.connect(
                    soa_preferred_time_unit_node
                )

    def _maintain_study_soa_preferences_relationship_on_save(
        self, expected_latest_value: StudyValue, previous_value: StudyValue
    ):
        # if new value node is created
        if expected_latest_value is not previous_value:
            nodes = previous_value.has_boolean_field.filter(
                field_name__in=settings.study_soa_preferences_fields
            )

            for node in nodes:
                # add the relation to the new node
                expected_latest_value.has_boolean_field.connect(node)

    def _maintain_study_soa_split_relationship_on_save(
        self, expected_latest_value: StudyValue, previous_value: StudyValue
    ):
        # if new value node is created
        if expected_latest_value is not previous_value:
            nodes = previous_value.has_array_field.filter(
                field_name=settings.study_soa_split_uids_field
            )

            for node in nodes:
                # add the relation to the new node
                expected_latest_value.has_array_field.connect(node)

    def _maintain_latest_value_and_relationship_on_save(
        self,
        current_snapshot: StudyDefinitionSnapshot,
        previous_snapshot: StudyDefinitionSnapshot,
        previous_value: StudyValue,
        root: StudyRoot,
        date: datetime,
        is_subpart_relationship_update: bool = False,
    ):
        assert (
            current_snapshot.current_metadata is not None
        )  # sth must be very wrong if does not hold
        assert (
            previous_snapshot.current_metadata is not None
        )  # sth must be very wrong if does not hold
        # first we need to know whether we have to create new value node
        # i.e. whether there are changes in other but version related metadata
        # if there are none we do not need to maintain anything and we expect the new latest value be exactly the same
        # node as the previous
        expected_latest_value = previous_value

        if (
            not _is_metadata_snapshot_and_status_equal_comparing_study_value_properties(
                current_snapshot,
                previous_snapshot,
                # we don't wan't to create new StudyValue node if we've just LOCKED a Study
            )
            and current_snapshot.study_status != StudyStatus.LOCKED.value
        ) or is_subpart_relationship_update:
            # we need a new node (for a new value)
            expected_latest_value = self._study_value_from_study_metadata_snapshot(
                current_snapshot.current_metadata
            )
            expected_latest_value.save()

            # in this case we also need to reconnect LATEST relationship
            root.latest_value.reconnect(
                old_node=previous_value, new_node=expected_latest_value
            )

            self._generate_study_value_audit_node(
                study_root_node=root,
                study_value_node_after=expected_latest_value,
                study_value_node_before=previous_value,
                change_status=None,
                author_id=self.audit_info.author_id,
                date=date,
            )
        return expected_latest_value

    def _maintain_latest_released_relationship_on_save(
        self,
        current_snapshot,
        latest_released,
        previous_snapshot,
        root,
        previous_value,
        expected_latest_value,
    ):
        if current_snapshot.study_status == StudyStatus.DRAFT.value:
            study_value_node_to_connect = previous_value
        else:
            study_value_node_to_connect = expected_latest_value
        # now we maintain LATEST_RELEASED relationship
        # the maintenance is needed only if there is some change in released_metadata
        if current_snapshot.released_metadata != previous_snapshot.released_metadata:
            # if released_metadata have been removed (is None) we just need to close LATEST_RELEASE (if it's open)
            # (i.e. set end_date if not set)
            if current_snapshot.released_metadata is None:
                assert latest_released is not None
                if latest_released.end_date is None:
                    latest_released.end_date = (
                        current_snapshot.current_metadata.ver_metadata.version_timestamp
                    )
                    latest_released.save()
            else:
                # if we have some new released_metadata we either initialize LATEST_RELEASED relationship (if there is
                # none) or update and reconnect existing if there is one
                if latest_released is None:  # initialize LATEST_RELEASED
                    version_properties = {
                        "start_date": current_snapshot.released_metadata.ver_metadata.version_timestamp,
                        "status": StudyStatus.RELEASED.value,
                        "author_id": self.audit_info.author_id,
                        "version": current_snapshot.released_metadata.ver_metadata.version_number,
                        "change_description": current_snapshot.released_metadata.ver_metadata.version_description,
                    }
                    root.latest_released.connect(
                        study_value_node_to_connect, properties=version_properties
                    )
                    root.has_version.connect(
                        study_value_node_to_connect, properties=version_properties
                    )
                else:  # update and reconnect goes below
                    latest_released.start_date = (
                        current_snapshot.released_metadata.ver_metadata.version_timestamp
                    )
                    latest_released.change_description = (
                        current_snapshot.released_metadata.ver_metadata.version_description
                    )
                    latest_released.author_id = self.audit_info.author_id
                    latest_released.version = (
                        current_snapshot.released_metadata.ver_metadata.version_number
                    )
                    latest_released.end_date = None
                    latest_released.save()
                    root.has_version.connect(
                        study_value_node_to_connect,
                        properties={
                            "start_date": latest_released.start_date,
                            "status": latest_released.status,
                            "author_id": latest_released.author_id,
                            "version": latest_released.version,
                            "change_description": latest_released.change_description,
                        },
                    )
                    root.latest_released.reconnect(
                        old_node=latest_released.end_node(),
                        new_node=study_value_node_to_connect,
                    )

    def _maintain_has_version_relationship_on_save(
        self,
        expected_latest_value: StudyValue,
        root: StudyRoot,
        current_snapshot: StudyDefinitionSnapshot,
        previous_snapshot: StudyDefinitionSnapshot,
        previous_latest_value: StudyValue,
    ):
        assert (
            current_snapshot.current_metadata is not None
        )  # something must be very wrong if this not hold
        # we maintain HAS_VERSION which means two actions:
        # 1. close the instance of the relation which is open and connected to current value
        # 2. create new instance of the relation connected to expected_latest_value (which may be new one or the same)

        # We want to maintain HAS_VERSION if we've created a new StudyValue node or StudyStatus is different
        # for going from DRAFT -> LOCKED we are not creating a new StudyValue node
        if (
            expected_latest_value != previous_latest_value
            or current_snapshot.study_status != previous_snapshot.study_status
        ):
            # here goes step 1 (closing the old HAS_VERSION instance)
            has_version_relationship: VersionRelationship
            for has_version_relationship in root.has_version.all_relationships(
                previous_latest_value
            ):
                if has_version_relationship.end_date is None:
                    has_version_relationship.end_date = (
                        current_snapshot.current_metadata.ver_metadata.version_timestamp
                    )
                    has_version_relationship.save()
            # and step 2 (creating a new instance)
            root.has_version.connect(
                expected_latest_value,
                properties={
                    "start_date": current_snapshot.current_metadata.ver_metadata.version_timestamp,
                    "status": current_snapshot.study_status,
                    "author_id": self.audit_info.author_id,
                    "version": current_snapshot.current_metadata.ver_metadata.version_number,
                    "change_description": current_snapshot.current_metadata.ver_metadata.version_description,
                },
            )

    def _maintain_latest_locked_relationship_on_save(
        self,
        expected_latest_value: StudyValue,
        latest_locked: VersionRelationship | None,
        previous_snapshot: StudyDefinitionSnapshot,
        root: StudyRoot,
        current_snapshot: StudyDefinitionSnapshot,
    ):
        assert (
            current_snapshot.current_metadata is not None
        )  # something must be very wrong if this not hold
        # if the study is in LOCKED state then we need to update or initialize LATEST_LOCKED relationship
        # we do not need to do anything otherwise (does not affect LATEST_LOCKED)
        if len(current_snapshot.locked_metadata_versions) != len(
            previous_snapshot.locked_metadata_versions
        ):
            # this is not exactly forbidden (to lock more than once in single transaction),
            # however not needed currently and hence not implemented (at least not tested for this case)
            # i.e. we support exactly one new LOCKED version
            if (
                len(current_snapshot.locked_metadata_versions)
                - len(previous_snapshot.locked_metadata_versions)
                != 1
            ):
                raise NotImplementedError(
                    f"Study {current_snapshot.uid}: locking more than once in the same request not supported (yet?)."
                )

            # update and reconnect LATEST_LOCKED relationship if there is one
            if latest_locked is not None:
                if (
                    current_snapshot.current_metadata.ver_metadata.version_timestamp
                    is None
                ):
                    raise ValueError("Version timestamp must not be None.")

                latest_locked.start_date = (
                    current_snapshot.current_metadata.ver_metadata.version_timestamp
                )
                if self.audit_info.author_id:
                    latest_locked.author_id = self.audit_info.author_id
                if current_snapshot.current_metadata.ver_metadata.version_description:
                    latest_locked.change_description = (
                        current_snapshot.current_metadata.ver_metadata.version_description
                    )
                latest_locked.version = str(
                    len(current_snapshot.locked_metadata_versions)
                )
                latest_locked.save()
                root.latest_locked.reconnect(
                    old_node=latest_locked.end_node(), new_node=expected_latest_value
                )
            else:
                # we have to initialize LATEST_LOCKED relationship if there is none
                root.latest_locked.connect(
                    expected_latest_value,
                    properties={
                        "start_date": current_snapshot.current_metadata.ver_metadata.version_timestamp,
                        "status": current_snapshot.study_status,
                        "author_id": self.audit_info.author_id,
                        "change_description": current_snapshot.current_metadata.ver_metadata.version_description,
                        "version": len(current_snapshot.locked_metadata_versions),
                    },
                )

    def _maintain_latest_draft_relationship_on_save(
        self,
        expected_latest_value: StudyValue,
        latest_draft_relationship: VersionRelationship,
        root: StudyRoot,
        current_snapshot: StudyDefinitionSnapshot,
    ) -> None:
        assert (
            current_snapshot.current_metadata is not None
        )  # this should always hold (something is very wrong if not)
        # if this is study in DRAFT state we need to update LATEST_DRAFT attributes and possibly reconnect
        if current_snapshot.study_status == StudyStatus.DRAFT.value:
            # we need to update attributes of latest DRAFT
            if current_snapshot.current_metadata.ver_metadata.version_timestamp is None:
                raise ValueError("Version timestamp must not be None.")

            latest_draft_relationship.start_date = (
                current_snapshot.current_metadata.ver_metadata.version_timestamp
            )
            if self.audit_info.author_id:
                latest_draft_relationship.author_id = self.audit_info.author_id
            latest_draft_relationship.end_date = None
            latest_draft_relationship.save()
            root.latest_draft.reconnect(
                old_node=latest_draft_relationship.end_node(),
                new_node=expected_latest_value,
            )
        else:  # if it's not in DRAFT (anymore)
            # then we may need to close (set end date) on LATEST_DRAFT (if it's not already closed)
            if latest_draft_relationship.end_date is None:
                latest_draft_relationship.end_date = (
                    current_snapshot.current_metadata.ver_metadata.version_timestamp
                )
                latest_draft_relationship.save()

    def _maintain_study_project_field_relationship(
        self,
        study_root: StudyRoot,
        previous_snapshot: StudyDefinitionSnapshot,
        current_snapshot: StudyDefinitionSnapshot,
        previous_value: StudyValue,
        expected_latest_value: StudyValue,
        date: datetime,
    ):
        curr_metadata = current_snapshot.current_metadata
        prev_metadata = previous_snapshot.current_metadata
        if (
            curr_metadata.id_metadata.project_number
            != prev_metadata.id_metadata.project_number
            or previous_value is not expected_latest_value
        ):
            project_node = Project.nodes.get(
                project_number=curr_metadata.id_metadata.project_number
            )

            # disconnecting Project from previous StudyValue node
            prev_study_project_field = previous_value.has_project.get_or_none()
            if (
                prev_study_project_field is not None
                and previous_value is expected_latest_value
            ):
                expected_latest_value.has_project.disconnect(prev_study_project_field)

            # assigning Project to newly created StudyValue node
            study_project_field = StudyProjectField()
            study_project_field.save()
            study_project_field.has_field.connect(project_node)
            expected_latest_value.has_project.connect(study_project_field)

            self._generate_study_field_audit_node(
                study_root_node=study_root,
                study_field_node_after=study_project_field,
                study_field_node_before=prev_study_project_field,
                change_status=None,
                author_id=self.audit_info.author_id,
                date=date,
            )

    def _get_associated_ct_term_root_node(
        self, term_uid: str, study_field_name: str, is_dictionary_term: bool = False
    ) -> CTTermRoot | DictionaryTermRoot:
        if not is_dictionary_term:
            query = """
                MATCH (term_root:CTTermRoot {uid: $uid})-[:HAS_NAME_ROOT]->()-[:LATEST_FINAL]->()
                RETURN term_root
                """
        else:
            query = """
                MATCH (dictionary_term_root:DictionaryTermRoot {uid: $uid})-[:LATEST_FINAL]->()
                RETURN dictionary_term_root
                """
        result, _ = db.cypher_query(query, {"uid": term_uid}, resolve_objects=True)
        if len(result) > 0 and len(result[0]) > 0:
            return result[0][0]
        raise exceptions.ValidationException(
            msg=f"{'DictionaryTerm' if is_dictionary_term else 'CTTerm'} with UID '{term_uid}' doesn't exist."
            f"Please check if the CT data was properly loaded for the following StudyField '{study_field_name}'."
        )

    def _get_previous_study_field_node(
        self,
        config_item,
        study_root,
        study_field_name,
        prev_study_field_value,
        prev_study_field_null_value_code,
    ):
        null_value_code = (
            None if prev_study_field_value else prev_study_field_null_value_code
        )
        prev_study_field_node = None
        if config_item.study_field_data_type == StudyFieldType.TEXT:
            prev_study_field_node = (
                StudyTextField.get_specific_field_currently_used_in_study(
                    study_uid=study_root.uid,
                    field_name=study_field_name,
                    value=prev_study_field_value,
                    null_value_code=null_value_code,
                )
            )
        elif config_item.study_field_data_type == StudyFieldType.BOOL:
            prev_study_field_node = (
                StudyBooleanField.get_specific_field_currently_used_in_study(
                    study_uid=study_root.uid,
                    field_name=study_field_name,
                    value=prev_study_field_value,
                    null_value_code=null_value_code,
                )
            )
        elif config_item.study_field_data_type == StudyFieldType.TIME:
            prev_study_field_node = (
                StudyTimeField.get_specific_field_currently_used_in_study(
                    study_uid=study_root.uid,
                    field_name=study_field_name,
                    value=prev_study_field_value,
                    null_value_code=null_value_code,
                )
            )
        elif config_item.study_field_data_type == StudyFieldType.INT:
            prev_study_field_node = (
                StudyIntField.get_specific_field_currently_used_in_study(
                    study_uid=study_root.uid,
                    field_name=study_field_name,
                    value=prev_study_field_value,
                    null_value_code=null_value_code,
                )
            )
        return prev_study_field_node

    def _get_or_create_study_field_node(
        self,
        study_field: type,
        study_root: StudyRoot,
        study_field_name: str,
        study_field_value: Any,
        term_node: CTTermContext | DictionaryTermRoot | None,
        null_value_code: str | None = None,
        to_delete: bool = False,
    ):
        study_field_node = study_field.get_specific_field_currently_used_in_study(
            study_uid=study_root.uid,
            field_name=study_field_name,
            value=study_field_value,
            null_value_code=null_value_code,
        )
        if study_field_node is None or to_delete:
            study_field_node = study_field.create(
                {
                    "value": study_field_value,
                    "field_name": study_field_name,
                }
            )[0]
        if term_node:
            # check if the term is already connected
            existing_term_rel = study_field_node.has_type.get_or_none()
            if existing_term_rel:
                existing_term = existing_term_rel.has_selected_term.get_or_none()
                new_term = term_node.has_selected_term.get_or_none()
                if existing_term.uid != new_term.uid:
                    # disconnect the existing term relationship if it exists
                    study_field_node.has_type.disconnect(existing_term)
                    study_field_node.has_type.connect(term_node)
            else:
                study_field_node.has_type.connect(term_node)
        if null_value_code:
            existing_null_value_reason = None
            existing_null_value_reason_rel = (
                study_field_node.has_reason_for_null_value.get_or_none()
            )
            if existing_null_value_reason_rel:
                existing_null_value_reason = (
                    existing_null_value_reason_rel.has_selected_term.get_or_none()
                )

            # Return early if the null value reason is already correctly set
            if (
                existing_null_value_reason
                and existing_null_value_reason.uid == null_value_code
            ):
                return study_field_node

            # Disconnect the existing null value reason relationship if it exists
            if existing_null_value_reason:
                study_field_node.has_reason_for_null_value.disconnect(
                    existing_null_value_reason
                )

            # TODO This doesn't do much, just gets the node with the given uid
            null_value_reason_node = self._get_associated_ct_term_root_node(
                term_uid=null_value_code,
                study_field_name="Null Flavour",
            )
            null_value_reason_node = (
                CTCodelistAttributesRepository().get_or_create_selected_term(
                    null_value_reason_node,
                    codelist_submission_value=settings.null_flavor_cl_submval,
                    catalogue_name=settings.sdtm_ct_catalogue_name,
                )
            )

            study_field_node.has_reason_for_null_value.connect(null_value_reason_node)
        return study_field_node

    def _maintain_study_fields_relationships(
        self,
        study_root: StudyRoot,
        previous_snapshot: StudyDefinitionSnapshot,
        current_snapshot: StudyDefinitionSnapshot,
        previous_value: StudyValue,
        expected_latest_value: StudyValue,
        date: datetime,
    ):
        curr_metadata = current_snapshot.current_metadata
        prev_metadata = previous_snapshot.current_metadata
        for config_item in FieldConfiguration.default_field_config():
            if (
                config_item.study_field_grouping == "ver_metadata"
                or config_item.study_field_data_type
                not in [
                    StudyFieldType.TEXT,
                    StudyFieldType.BOOL,
                    StudyFieldType.TIME,
                    StudyFieldType.INT,
                ]
            ):
                continue

            study_field_value = curr_metadata.get_field_value(
                config_item.study_field_grouping, config_item.study_field_name
            )  # current field value
            prev_study_field_value = prev_metadata.get_field_value(
                config_item.study_field_grouping, config_item.study_field_name
            )  # previous field value
            study_field_name = config_item.study_field_name_api  # field name
            if config_item.study_field_null_value_code is not None:
                prev_study_field_null_value_code = prev_metadata.get_field_value(
                    config_item.study_field_grouping,
                    config_item.study_field_null_value_code,
                )  # previous null value code
                study_field_null_value_code = curr_metadata.get_field_value(
                    config_item.study_field_grouping,
                    config_item.study_field_null_value_code,
                )  # current null value code
            else:
                prev_study_field_null_value_code = None
                study_field_null_value_code = None

            if (
                study_field_value != prev_study_field_value
                or previous_value is not expected_latest_value
                or prev_study_field_null_value_code != study_field_null_value_code
            ):
                prev_study_field_node = self._get_previous_study_field_node(
                    config_item=config_item,
                    study_root=study_root,
                    study_field_name=study_field_name,
                    prev_study_field_value=prev_study_field_value,
                    prev_study_field_null_value_code=prev_study_field_null_value_code,
                )
                study_field_node = None
                # check if the study field needs to be deleted
                to_delete = False
                if study_field_value is None and study_field_null_value_code is None:
                    if study_field_value is None and prev_study_field_value is not None:
                        study_field_value = prev_study_field_value
                        to_delete = True
                    elif (
                        study_field_null_value_code is None
                        and prev_study_field_null_value_code is not None
                    ):
                        study_field_null_value_code = prev_study_field_null_value_code
                        to_delete = True
                if (
                    study_field_value is not None
                    or study_field_null_value_code is not None
                ):
                    node_uid = None
                    configured_codelist_uid = None
                    if config_item.configured_codelist_uid:
                        configured_codelist_uid = config_item.configured_codelist_uid
                        node_uid = study_field_value
                    elif config_item.study_field_data_type == StudyFieldType.BOOL:
                        node_uid = (
                            settings.ct_uid_boolean_yes
                            if study_field_value
                            else settings.ct_uid_boolean_no
                        )
                        configured_codelist_uid = settings.ct_uid_boolean_codelist
                    elif config_item.configured_term_uid:
                        node_uid = config_item.configured_term_uid
                    if node_uid:
                        ct_term_root_node = self._get_associated_ct_term_root_node(
                            term_uid=node_uid,
                            study_field_name=study_field_name,
                            is_dictionary_term=config_item.is_dictionary_term,
                        )
                        if not config_item.is_dictionary_term:
                            ct_term_root_node = CTCodelistAttributesRepository().get_or_create_selected_term(
                                ct_term_root_node,
                                codelist_uid=configured_codelist_uid,
                                catalogue_name=settings.sdtm_ct_catalogue_name,
                            )
                    else:
                        ct_term_root_node = None

                    if study_field_value is not None:
                        if config_item.study_field_data_type == StudyFieldType.TEXT:
                            study_field_node = self._get_or_create_study_field_node(
                                study_field=StudyTextField,
                                study_root=study_root,
                                study_field_name=study_field_name,
                                study_field_value=study_field_value,
                                term_node=ct_term_root_node,
                                to_delete=to_delete,
                            )
                            if not to_delete:
                                expected_latest_value.has_text_field.connect(
                                    study_field_node
                                )
                        elif config_item.study_field_data_type == StudyFieldType.BOOL:
                            study_field_node = self._get_or_create_study_field_node(
                                study_field=StudyBooleanField,
                                study_root=study_root,
                                study_field_name=study_field_name,
                                study_field_value=study_field_value,
                                term_node=ct_term_root_node,
                                to_delete=to_delete,
                            )
                            if not to_delete:
                                expected_latest_value.has_boolean_field.connect(
                                    study_field_node
                                )
                        elif config_item.study_field_data_type == StudyFieldType.TIME:
                            study_field_node = self._get_or_create_study_field_node(
                                study_field=StudyTimeField,
                                study_root=study_root,
                                study_field_name=study_field_name,
                                study_field_value=study_field_value,
                                term_node=ct_term_root_node,
                                to_delete=to_delete,
                            )
                            if not to_delete:
                                expected_latest_value.has_time_field.connect(
                                    study_field_node
                                )
                        elif config_item.study_field_data_type == StudyFieldType.INT:
                            study_field_node = self._get_or_create_study_field_node(
                                study_field=StudyIntField,
                                study_root=study_root,
                                study_field_name=study_field_name,
                                study_field_value=study_field_value,
                                term_node=ct_term_root_node,
                                to_delete=to_delete,
                            )
                            if not to_delete:
                                expected_latest_value.has_int_field.connect(
                                    study_field_node
                                )

                    elif study_field_null_value_code is not None:
                        if config_item.study_field_data_type == StudyFieldType.TEXT:
                            study_field_node = self._get_or_create_study_field_node(
                                study_field=StudyTextField,
                                study_root=study_root,
                                study_field_name=study_field_name,
                                study_field_value=study_field_value,
                                term_node=ct_term_root_node,
                                null_value_code=study_field_null_value_code,
                                to_delete=to_delete,
                            )
                            if not to_delete:
                                expected_latest_value.has_text_field.connect(
                                    study_field_node
                                )
                        elif config_item.study_field_data_type == StudyFieldType.BOOL:
                            study_field_node = self._get_or_create_study_field_node(
                                study_field=StudyBooleanField,
                                study_root=study_root,
                                study_field_name=study_field_name,
                                study_field_value=study_field_value,
                                term_node=ct_term_root_node,
                                null_value_code=study_field_null_value_code,
                                to_delete=to_delete,
                            )
                            if not to_delete:
                                expected_latest_value.has_boolean_field.connect(
                                    study_field_node
                                )
                        elif config_item.study_field_data_type == StudyFieldType.TIME:
                            study_field_node = self._get_or_create_study_field_node(
                                study_field=StudyTimeField,
                                study_root=study_root,
                                study_field_name=study_field_name,
                                study_field_value=study_field_value,
                                term_node=ct_term_root_node,
                                null_value_code=study_field_null_value_code,
                                to_delete=to_delete,
                            )
                            if not to_delete:
                                expected_latest_value.has_time_field.connect(
                                    study_field_node
                                )
                        elif config_item.study_field_data_type == StudyFieldType.INT:
                            study_field_node = self._get_or_create_study_field_node(
                                study_field=StudyIntField,
                                study_root=study_root,
                                study_field_name=study_field_name,
                                study_field_value=study_field_value,
                                term_node=ct_term_root_node,
                                null_value_code=study_field_null_value_code,
                                to_delete=to_delete,
                            )
                            if not to_delete:
                                expected_latest_value.has_int_field.connect(
                                    study_field_node
                                )
                if (
                    prev_study_field_node is not None
                    and (prev_study_field_node != study_field_node)
                    and previous_value is expected_latest_value
                ):
                    if config_item.study_field_data_type == StudyFieldType.TEXT:
                        expected_latest_value.has_text_field.disconnect(
                            prev_study_field_node
                        )
                    elif config_item.study_field_data_type == StudyFieldType.BOOL:
                        expected_latest_value.has_boolean_field.disconnect(
                            prev_study_field_node
                        )
                    elif config_item.study_field_data_type == StudyFieldType.TIME:
                        expected_latest_value.has_time_field.disconnect(
                            prev_study_field_node
                        )
                    elif config_item.study_field_data_type == StudyFieldType.INT:
                        expected_latest_value.has_int_field.disconnect(
                            prev_study_field_node
                        )
                if study_field_node != prev_study_field_node:
                    self._generate_study_field_audit_node(
                        study_root_node=study_root,
                        study_field_node_after=study_field_node,
                        study_field_node_before=prev_study_field_node,
                        change_status=None,
                        author_id=self.audit_info.author_id,
                        date=date,
                        to_delete=to_delete,
                    )

    def _maintain_study_array_fields_relationships(
        self,
        study_root: StudyRoot,
        previous_snapshot: StudyDefinitionSnapshot,
        current_snapshot: StudyDefinitionSnapshot,
        previous_value: StudyValue,
        expected_latest_value: StudyValue,
        date: datetime,
    ):
        curr_metadata = current_snapshot.current_metadata
        prev_metadata = previous_snapshot.current_metadata
        for config_item in [
            item
            for item in FieldConfiguration.default_field_config()
            if item.study_field_data_type == StudyFieldType.CODELIST_MULTISELECT
        ]:
            study_array_field_value = curr_metadata.get_field_value(
                config_item.study_field_grouping, config_item.study_field_name
            )  # current field value
            prev_study_array_field_value = prev_metadata.get_field_value(
                config_item.study_field_grouping, config_item.study_field_name
            )  # previous field value
            study_array_field_name = config_item.study_field_name_api  # field name
            if config_item.study_field_null_value_code is not None:
                prev_study_array_field_null_value_code = prev_metadata.get_field_value(
                    config_item.study_field_grouping,
                    config_item.study_field_null_value_code,
                )  # previous null value code
                study_array_field_null_value_code = curr_metadata.get_field_value(
                    config_item.study_field_grouping,
                    config_item.study_field_null_value_code,
                )  # current null value code
            else:
                study_array_field_null_value_code = None
                prev_study_array_field_null_value_code = None
            is_c_code_field = (
                config_item.configured_codelist_uid
            )  # is this codelist field

            if (
                study_array_field_value != prev_study_array_field_value
                or previous_value is not expected_latest_value
                or prev_study_array_field_null_value_code
                != study_array_field_null_value_code
            ):
                prev_study_array_field_node = (
                    StudyArrayField.get_specific_field_currently_used_in_study(
                        study_uid=study_root.uid,
                        field_name=study_array_field_name,
                        value=prev_study_array_field_value,
                    )
                )

                study_array_field_node = None
                # check if the study field needs to be deleted
                to_delete = False
                if (
                    not study_array_field_value
                    and study_array_field_null_value_code is None
                ):
                    if (
                        not (
                            study_array_field_value
                            or study_array_field_null_value_code is not None
                        )
                        and prev_study_array_field_value
                    ):
                        study_array_field_value = prev_study_array_field_value
                        to_delete = True
                    elif (
                        not (
                            not study_array_field_value
                            and study_array_field_null_value_code is not None
                        )
                        and prev_study_array_field_null_value_code is not None
                    ):
                        study_array_field_null_value_code = (
                            prev_study_array_field_null_value_code
                        )
                        to_delete = True

                if (
                    study_array_field_value
                    or study_array_field_null_value_code is not None
                ):
                    ct_term_root_nodes = []
                    # we can't link CTTermRoot for these nodes as they are not valid codelists at the moment
                    if is_c_code_field or config_item.is_dictionary_term:
                        if study_array_field_value is not None:
                            for study_array_value in study_array_field_value:
                                ct_term_root_node = self._get_associated_ct_term_root_node(
                                    term_uid=study_array_value,
                                    study_field_name=study_array_field_name,
                                    is_dictionary_term=config_item.is_dictionary_term,
                                )
                                if not config_item.is_dictionary_term:
                                    ct_term_root_node = CTCodelistAttributesRepository().get_or_create_selected_term(
                                        ct_term_root_node,
                                        codelist_uid=config_item.configured_codelist_uid,
                                        catalogue_name=settings.sdtm_ct_catalogue_name,
                                    )
                                ct_term_root_nodes.append(ct_term_root_node)
                    if study_array_field_value:
                        # If the value is set, create a StudyTextField node and (optionally) link it to matching CT term.
                        study_array_field_node = (
                            StudyArrayField.get_specific_field_currently_used_in_study(
                                study_uid=study_root.uid,
                                field_name=study_array_field_name,
                                value=study_array_field_value,
                            )
                        )
                        if study_array_field_node is None or to_delete:
                            study_array_field_node = StudyArrayField(
                                value=study_array_field_value,
                                field_name=study_array_field_name,
                            ).save()
                        # disconnect any existing has_term or has_dictionary_term relationships
                        if config_item.is_dictionary_term:
                            for rel in study_array_field_node.has_dictionary_type.all():
                                study_array_field_node.has_dictionary_type.disconnect(
                                    rel
                                )
                        else:
                            for rel in study_array_field_node.has_type.all():
                                study_array_field_node.has_type.disconnect(rel)
                        # then reconnect the new set
                        for term_root_node in ct_term_root_nodes:
                            if not config_item.is_dictionary_term:
                                study_array_field_node.has_type.connect(term_root_node)
                            else:
                                study_array_field_node.has_dictionary_type.connect(
                                    term_root_node
                                )
                        if not to_delete:
                            expected_latest_value.has_array_field.connect(
                                study_array_field_node
                            )
                    elif (
                        not study_array_field_value
                        and study_array_field_null_value_code is not None
                    ):
                        study_array_field_node = (
                            StudyArrayField.get_specific_field_currently_used_in_study(
                                study_uid=study_root.uid,
                                field_name=study_array_field_name,
                                value=study_array_field_value,
                                null_value_code=study_array_field_null_value_code,
                            )
                        )
                        if study_array_field_node is None or to_delete:
                            study_array_field_node = StudyArrayField(
                                value=[], field_name=study_array_field_name
                            ).save()
                        # disconnect any existing has_type relationships
                        for rel in study_array_field_node.has_type.all():
                            study_array_field_node.has_type.disconnect(rel)
                        # then reconnect the new set
                        for ct_term_root_node in ct_term_root_nodes:
                            study_array_field_node.has_type.connect(ct_term_root_node)

                        # check if the same null flavor reason is already connected,
                        # don't connect again if so
                        existing_null_value_reason_uid = None
                        existing_null_value_reason_rel = (
                            study_array_field_node.has_reason_for_null_value.get_or_none()
                        )
                        if existing_null_value_reason_rel:
                            existing_null_value_reason_uid = (
                                existing_null_value_reason_rel.has_selected_term.get_or_none().uid
                            )
                            if (
                                existing_null_value_reason_uid
                                != study_array_field_null_value_code
                            ):
                                study_array_field_node.has_reason_for_null_value.disconnect(
                                    existing_null_value_reason_rel
                                )
                                existing_null_value_reason_uid = None

                        if not existing_null_value_reason_uid:
                            null_value_reason_node = (
                                self._get_associated_ct_term_root_node(
                                    term_uid=study_array_field_null_value_code,
                                    study_field_name="Null Flavor",
                                )
                            )
                            null_value_reason_node = CTCodelistAttributesRepository().get_or_create_selected_term(
                                null_value_reason_node,
                                codelist_submission_value=settings.null_flavor_cl_submval,
                                catalogue_name=settings.sdtm_ct_catalogue_name,
                            )
                            study_array_field_node.has_reason_for_null_value.connect(
                                null_value_reason_node
                            )
                        if not to_delete:
                            expected_latest_value.has_array_field.connect(
                                study_array_field_node
                            )

                if (
                    prev_study_array_field_node is not None
                    and (prev_study_array_field_node != study_array_field_node)
                    and previous_value is expected_latest_value
                ):
                    expected_latest_value.has_array_field.disconnect(
                        prev_study_array_field_node
                    )
                if study_array_field_node != prev_study_array_field_node:
                    self._generate_study_field_audit_node(
                        study_root_node=study_root,
                        study_field_node_after=study_array_field_node,
                        study_field_node_before=prev_study_array_field_node,
                        change_status=None,
                        author_id=self.audit_info.author_id,
                        date=date,
                        to_delete=to_delete,
                    )

    def _maintain_study_registry_id_fields_relationships(
        self,
        study_root: StudyRoot,
        previous_snapshot: StudyDefinitionSnapshot,
        current_snapshot: StudyDefinitionSnapshot,
        previous_value: StudyValue,
        expected_latest_value: StudyValue,
        date: datetime,
    ):
        curr_metadata = current_snapshot.current_metadata
        prev_metadata = previous_snapshot.current_metadata
        for config_item in [
            item
            for item in FieldConfiguration.default_field_config()
            if item.study_field_data_type == StudyFieldType.REGISTRY
        ]:
            study_registry_id_value = curr_metadata.get_field_value(
                config_item.study_field_grouping, config_item.study_field_name
            )  # current field value
            prev_study_registry_id_value = prev_metadata.get_field_value(
                config_item.study_field_grouping, config_item.study_field_name
            )  # previous field value
            study_registry_id_name = config_item.study_field_name_api  # field name

            if config_item.study_field_null_value_code is not None:
                study_registry_null_value_code = curr_metadata.get_field_value(
                    config_item.study_field_grouping,
                    config_item.study_field_null_value_code,
                )
                prev_study_registry_null_value_code = prev_metadata.get_field_value(
                    config_item.study_field_grouping,
                    config_item.study_field_null_value_code,
                )
            else:
                prev_study_registry_null_value_code = None
                study_registry_null_value_code = None

            if (
                study_registry_id_value != prev_study_registry_id_value
                or previous_value is not expected_latest_value
                or prev_study_registry_null_value_code != study_registry_null_value_code
            ):
                study_registry_id_text_field_node = None
                null_value_code = (
                    None
                    if prev_study_registry_id_value
                    else prev_study_registry_null_value_code
                )
                prev_study_registry_id_text_field_node = (
                    StudyTextField.get_specific_field_currently_used_in_study(
                        study_uid=study_root.uid,
                        field_name=study_registry_id_name,
                        value=prev_study_registry_id_value,
                        null_value_code=null_value_code,
                    )
                )
                # check if the study field needs to be deleted
                to_delete = False
                if (
                    study_registry_id_value is None
                    and study_registry_null_value_code is None
                ):
                    if (
                        study_registry_id_value is None
                        and prev_study_registry_id_value is not None
                    ):
                        study_registry_id_value = prev_study_registry_id_value
                        to_delete = True
                    elif (
                        study_registry_null_value_code is None
                        and prev_study_registry_null_value_code is not None
                    ):
                        study_registry_null_value_code = (
                            prev_study_registry_null_value_code
                        )
                        to_delete = True

                if study_registry_id_value is not None:
                    study_registry_id_text_field_node = (
                        self._get_or_create_study_field_node(
                            study_field=StudyTextField,
                            study_root=study_root,
                            study_field_name=study_registry_id_name,
                            study_field_value=study_registry_id_value,
                            term_node=None,
                            to_delete=to_delete,
                        )
                    )
                    if not to_delete:
                        expected_latest_value.has_text_field.connect(
                            study_registry_id_text_field_node
                        )

                elif study_registry_null_value_code is not None:
                    study_registry_id_text_field_node = (
                        self._get_or_create_study_field_node(
                            study_field=StudyTextField,
                            study_root=study_root,
                            study_field_name=study_registry_id_name,
                            study_field_value=study_registry_id_value,
                            term_node=None,
                            null_value_code=study_registry_null_value_code,
                            to_delete=to_delete,
                        )
                    )
                    if not to_delete:
                        expected_latest_value.has_text_field.connect(
                            study_registry_id_text_field_node
                        )
                if (
                    prev_study_registry_id_text_field_node is not None
                    and (
                        prev_study_registry_id_text_field_node
                        != study_registry_id_text_field_node
                    )
                    and previous_value is expected_latest_value
                ):
                    expected_latest_value.has_text_field.disconnect(
                        prev_study_registry_id_text_field_node
                    )
                if (
                    study_registry_id_text_field_node
                    != prev_study_registry_id_text_field_node
                ):
                    self._generate_study_field_audit_node(
                        study_root_node=study_root,
                        study_field_node_after=study_registry_id_text_field_node,
                        study_field_node_before=prev_study_registry_id_text_field_node,
                        change_status=None,
                        author_id=self.audit_info.author_id,
                        date=date,
                        to_delete=to_delete,
                    )

    @classmethod
    def add_value_and_null_value_code_to_dict(
        cls,
        study_field_node_value,
        study_field_node_name,
        null_value_code,
        retrieved_data,
    ):
        null_value_code_suffix = "_null_value_code"
        null_value_field_name = (
            cls.truncate_code_or_codes_suffix(study_field_node_name)
            + null_value_code_suffix
        )
        retrieved_data[study_field_node_name] = study_field_node_value
        if null_value_code is not None:
            retrieved_data[null_value_field_name] = (
                null_value_code.has_selected_term.single().uid
            )
        else:
            retrieved_data[null_value_field_name] = None

    @classmethod
    def _get_text_field_value(cls, text_field_node) -> str:
        if type_context_node := text_field_node.has_type.get_or_none():
            return type_context_node.has_selected_term.get_or_none().uid
        return text_field_node.value

    @classmethod
    def _get_array_field_values(cls, array_field_node) -> list[str]:
        if type_nodes := array_field_node.has_type.all():
            return sorted(
                node.has_selected_term.get_or_none().uid for node in type_nodes
            )
        return array_field_node.value

    @classmethod
    def _retrieve_data_from_study_value(cls, study_value: StudyValue) -> dict[Any, Any]:
        """
        Retrieves all StudyField data from a StudyValue node using a single Cypher query
        instead of multiple neomodel traversals.
        Returns data in dictionary that maps StudyField field_names into StudyField values.
        :param study_value:
        :return dict:
        """
        rs, _ = db.cypher_query(
            """
            MATCH (sv:StudyValue) WHERE elementId(sv) = $sv_id

            // Project
            OPTIONAL MATCH (sv)-[:HAS_PROJECT]->(:StudyProjectField)<-[:HAS_FIELD]-(p:Project)

            // Text fields with optional type (codelist) and null value reason
            OPTIONAL MATCH (sv)-[:HAS_TEXT_FIELD]->(tf:StudyTextField)
            OPTIONAL MATCH (tf)-[:HAS_TYPE]->(tf_type:CTTermContext)-[:HAS_SELECTED_TERM]->(tf_term:CTTermRoot)
            OPTIONAL MATCH (tf)-[:HAS_REASON_FOR_NULL_VALUE]->(tf_nv:CTTermContext)-[:HAS_SELECTED_TERM]->(tf_nv_term:CTTermRoot)
            WITH sv, p,
                 collect(DISTINCT {
                     field_name: tf.field_name,
                     value: tf.value,
                     term_uid: tf_term.uid,
                     null_value_uid: tf_nv_term.uid
                 }) AS text_fields

            // Int fields with optional null value reason
            OPTIONAL MATCH (sv)-[:HAS_INT_FIELD]->(intf:StudyIntField)
            OPTIONAL MATCH (intf)-[:HAS_REASON_FOR_NULL_VALUE]->(intf_nv:CTTermContext)-[:HAS_SELECTED_TERM]->(intf_nv_term:CTTermRoot)
            WITH sv, p, text_fields,
                 collect(DISTINCT {
                     field_name: intf.field_name,
                     value: intf.value,
                     null_value_uid: intf_nv_term.uid
                 }) AS int_fields

            // Boolean fields with optional null value reason
            OPTIONAL MATCH (sv)-[:HAS_BOOLEAN_FIELD]->(bf:StudyBooleanField)
            OPTIONAL MATCH (bf)-[:HAS_REASON_FOR_NULL_VALUE]->(bf_nv:CTTermContext)-[:HAS_SELECTED_TERM]->(bf_nv_term:CTTermRoot)
            WITH sv, p, text_fields, int_fields,
                 collect(DISTINCT {
                     field_name: bf.field_name,
                     value: bf.value,
                     null_value_uid: bf_nv_term.uid
                 }) AS boolean_fields

            // Time fields with optional null value reason
            OPTIONAL MATCH (sv)-[:HAS_TIME_FIELD]->(tmf:StudyTimeField)
            OPTIONAL MATCH (tmf)-[:HAS_REASON_FOR_NULL_VALUE]->(tmf_nv:CTTermContext)-[:HAS_SELECTED_TERM]->(tmf_nv_term:CTTermRoot)
            WITH sv, p, text_fields, int_fields, boolean_fields,
                 collect(DISTINCT {
                     field_name: tmf.field_name,
                     value: tmf.value,
                     null_value_uid: tmf_nv_term.uid
                 }) AS time_fields

            // Array fields with optional type terms and null value reason
            OPTIONAL MATCH (sv)-[:HAS_ARRAY_FIELD]->(af:StudyArrayField)
            OPTIONAL MATCH (af)-[:HAS_REASON_FOR_NULL_VALUE]->(af_nv:CTTermContext)-[:HAS_SELECTED_TERM]->(af_nv_term:CTTermRoot)
            OPTIONAL MATCH (af)-[:HAS_TYPE]->(af_type:CTTermContext)-[:HAS_SELECTED_TERM]->(af_term:CTTermRoot)
            WITH sv, p, text_fields, int_fields, boolean_fields, time_fields,
                 af, af_nv_term,
                 collect(DISTINCT af_term.uid) AS af_term_uids
            WITH sv, p, text_fields, int_fields, boolean_fields, time_fields,
                 collect(DISTINCT {
                     field_name: af.field_name,
                     value: af.value,
                     term_uids: af_term_uids,
                     null_value_uid: af_nv_term.uid
                 }) AS array_fields

            RETURN p.project_number, text_fields, int_fields, boolean_fields, time_fields, array_fields
            """,
            params={"sv_id": study_value.element_id},
        )

        retrieved_data: dict[Any, Any] = {}

        if not rs or not rs[0]:
            return retrieved_data

        row = rs[0]
        project_number = row[0]
        text_fields = row[1] or []
        int_fields = row[2] or []
        boolean_fields = row[3] or []
        time_fields = row[4] or []
        array_fields = row[5] or []

        retrieved_data["project_number"] = project_number

        # Process text fields
        for tf in text_fields:
            if tf["field_name"] is None:
                continue
            # If has_type exists, use the term UID as value; otherwise use literal value
            field_value = tf["term_uid"] if tf["term_uid"] is not None else tf["value"]
            field_name = tf["field_name"]
            null_value_uid = tf["null_value_uid"]
            null_value_field_name = (
                cls.truncate_code_or_codes_suffix(field_name) + "_null_value_code"
            )
            retrieved_data[field_name] = field_value
            retrieved_data[null_value_field_name] = null_value_uid

        # Process int fields
        for inf in int_fields:
            if inf["field_name"] is None:
                continue
            field_name = inf["field_name"]
            null_value_uid = inf["null_value_uid"]
            null_value_field_name = (
                cls.truncate_code_or_codes_suffix(field_name) + "_null_value_code"
            )
            retrieved_data[field_name] = inf["value"]
            retrieved_data[null_value_field_name] = null_value_uid

        # Process boolean fields
        for bf in boolean_fields:
            if bf["field_name"] is None:
                continue
            field_name = bf["field_name"]
            null_value_uid = bf["null_value_uid"]
            null_value_field_name = (
                cls.truncate_code_or_codes_suffix(field_name) + "_null_value_code"
            )
            retrieved_data[field_name] = bf["value"]
            retrieved_data[null_value_field_name] = null_value_uid

        # Process time fields
        for tmf in time_fields:
            if tmf["field_name"] is None:
                continue
            field_name = tmf["field_name"]
            null_value_uid = tmf["null_value_uid"]
            null_value_field_name = (
                cls.truncate_code_or_codes_suffix(field_name) + "_null_value_code"
            )
            retrieved_data[field_name] = tmf["value"]
            retrieved_data[null_value_field_name] = null_value_uid

        # Process array fields
        for af in array_fields:
            if af["field_name"] is None:
                continue
            field_name = af["field_name"]
            null_value_uid = af["null_value_uid"]
            null_value_field_name = (
                cls.truncate_code_or_codes_suffix(field_name) + "_null_value_code"
            )
            # If has_type terms exist, use sorted term UIDs; otherwise use the stored array value
            term_uids = [uid for uid in (af["term_uids"] or []) if uid is not None]
            retrieved_data[field_name] = (
                sorted(term_uids) if term_uids else (af["value"] or [])
            )
            retrieved_data[null_value_field_name] = null_value_uid

        return retrieved_data

    @classmethod
    def _assign_snapshot_ver_properties_from_ver_relationship(
        cls,
        snapshot: StudyMetadataVO,
        ver_relationship: VersionRelationship,
    ) -> StudyMetadataVO:
        new_ver = StudyVersionMetadataVO(
            version_timestamp=ver_relationship.start_date,
            version_author=UserInfoService.get_author_username_from_id(
                ver_relationship.author_id
            ),
            version_description=ver_relationship.change_description,
            version_number=(
                Decimal(ver_relationship.version) if ver_relationship.version else None
            ),
            study_status=StudyStatus(ver_relationship.status),
        )
        return replace(snapshot, ver_metadata=new_ver)

    @classmethod
    def _assign_snapshot_ver_properties_from_raw(
        cls,
        snapshot: StudyMetadataVO,
        start_date,
        version: str | None,
        status: str | None,
        author_id: str | None,
        change_description: str | None,
    ) -> StudyMetadataVO:
        new_ver = StudyVersionMetadataVO(
            version_timestamp=convert_to_datetime(start_date),
            version_author=UserInfoService.get_author_username_from_id(author_id or ""),
            version_description=change_description,
            version_number=Decimal(version) if version else None,
            study_status=StudyStatus(status) if status else StudyStatus.DRAFT,
        )
        return replace(snapshot, ver_metadata=new_ver)

    @classmethod
    def _study_metadata_snapshot_from_study_value(
        cls, study_value: StudyValue
    ) -> StudyMetadataVO:
        retrieved_data = cls._retrieve_data_from_study_value(study_value)

        grouped: dict[str, dict[str, Any]] = {}
        for config_item in FieldConfiguration.default_field_config():
            g = config_item.study_field_grouping
            if g not in grouped:
                grouped[g] = {}
            if g == "ver_metadata":
                grouped[g][config_item.study_field_name] = None
            elif hasattr(study_value, config_item.study_field_name):
                grouped[g][config_item.study_field_name] = getattr(
                    study_value, config_item.study_field_name
                )
            elif (
                config_item.study_field_data_type == StudyFieldType.CODELIST_MULTISELECT
            ):
                grouped[g][config_item.study_field_name] = retrieved_data.get(
                    config_item.study_field_name_api, []
                )
            else:
                grouped[g][config_item.study_field_name] = retrieved_data.get(
                    config_item.study_field_name_api
                )

        reg_fields = grouped.get("id_metadata.registry_identifiers", {})
        registry_identifiers = RegistryIdentifiersVO(**reg_fields)

        id_fields = grouped.get("id_metadata", {})
        id_metadata = StudyIdentificationMetadataVO(
            project_number=id_fields.get("project_number", ""),
            study_number=id_fields.get("study_number"),
            subpart_id=id_fields.get("subpart_id"),
            study_acronym=id_fields.get("study_acronym"),
            study_subpart_acronym=id_fields.get("study_subpart_acronym"),
            description=id_fields.get("description"),
            registry_identifiers=registry_identifiers,
            _study_id_prefix=id_fields.get("study_id_prefix"),
        )

        return StudyMetadataVO(
            id_metadata=id_metadata,
            ver_metadata=None,
            high_level_study_design=HighLevelStudyDesignVO(
                **grouped.get("high_level_study_design", {})
            ),
            study_population=StudyPopulationVO(**grouped.get("study_population", {})),
            study_intervention=StudyInterventionVO(
                **grouped.get("study_intervention", {})
            ),
            study_description=StudyDescriptionVO(
                **grouped.get("study_description", {})
            ),
        )

    @overload
    @classmethod
    def _study_metadata_snapshot_from_cypher_res(
        cls, metadata_section: dict[Any, Any]
    ) -> StudyMetadataVO: ...

    @overload
    @classmethod
    def _study_metadata_snapshot_from_cypher_res(
        cls, metadata_section: None
    ) -> None: ...

    @classmethod
    def _study_metadata_snapshot_from_cypher_res(
        cls, metadata_section: dict[Any, Any] | None
    ) -> StudyMetadataVO | None:
        """
        Function maps the part of the result of the cypher query that holds Study metadata information
        into a StudyMetadataVO.
        :param metadata_section:
        :return StudyMetadataVO | None:
        """
        if metadata_section is None:
            return None

        # Build version metadata from cypher result
        ver_metadata = StudyVersionMetadataVO(
            version_timestamp=convert_to_datetime(
                value=metadata_section["version_timestamp"]
            ),
            version_author=UserInfoService.get_author_username_from_id(
                metadata_section["version_author_id"]
            ),
            version_description=metadata_section.get("version_description"),
            version_number=metadata_section.get("version_number"),
        )

        # Build id_metadata - registry identifiers default to None
        registry_identifiers = RegistryIdentifiersVO(
            ct_gov_id=None,
            ct_gov_id_null_value_code=None,
            eudract_id=None,
            eudract_id_null_value_code=None,
            universal_trial_number_utn=None,
            universal_trial_number_utn_null_value_code=None,
            japanese_trial_registry_id_japic=None,
            japanese_trial_registry_id_japic_null_value_code=None,
            investigational_new_drug_application_number_ind=None,
            investigational_new_drug_application_number_ind_null_value_code=None,
            eu_trial_number=None,
            eu_trial_number_null_value_code=None,
            civ_id_sin_number=None,
            civ_id_sin_number_null_value_code=None,
            national_clinical_trial_number=None,
            national_clinical_trial_number_null_value_code=None,
            japanese_trial_registry_number_jrct=None,
            japanese_trial_registry_number_jrct_null_value_code=None,
            national_medical_products_administration_nmpa_number=None,
            national_medical_products_administration_nmpa_number_null_value_code=None,
            eudamed_srn_number=None,
            eudamed_srn_number_null_value_code=None,
            investigational_device_exemption_ide_number=None,
            investigational_device_exemption_ide_number_null_value_code=None,
            eu_pas_number=None,
            eu_pas_number_null_value_code=None,
        )

        id_metadata = StudyIdentificationMetadataVO(
            project_number=metadata_section["project_number"] or "",
            study_number=metadata_section["study_number"],
            subpart_id=metadata_section["subpart_id"],
            study_acronym=metadata_section["study_acronym"],
            study_subpart_acronym=metadata_section["study_subpart_acronym"],
            description=metadata_section["description"],
            registry_identifiers=registry_identifiers,
            _study_id_prefix=metadata_section["study_id_prefix"],
        )

        return StudyMetadataVO(
            id_metadata=id_metadata,
            ver_metadata=ver_metadata,
            high_level_study_design=HighLevelStudyDesignVO(),
            study_population=StudyPopulationVO(),
            study_intervention=StudyInterventionVO(),
            study_description=StudyDescriptionVO(
                study_title=metadata_section["study_title"],
                study_short_title=metadata_section["study_short_title"],
            ),
        )

    @classmethod
    def _study_value_from_study_metadata_snapshot(
        cls, metadata_snapshot: StudyMetadataVO
    ) -> StudyValue:
        id_meta = metadata_snapshot.id_metadata
        # we should keep keep (ready made) study_id in DB for ease of sorting and selection
        _study_id = (
            None
            if (id_meta.study_number is None or id_meta.study_id_prefix is None)
            else f"{id_meta.study_id_prefix}-{id_meta.study_number}"
        )

        value = StudyValue(
            study_id=_study_id,
            study_number=id_meta.study_number,
            subpart_id=id_meta.subpart_id,
            study_acronym=id_meta.study_acronym,
            study_subpart_acronym=id_meta.study_subpart_acronym,
            description=id_meta.description,
            study_id_prefix=id_meta.study_id_prefix,
        )

        return value

    def _create(self, snapshot: StudyDefinitionSnapshot) -> None:
        self._ensure_transaction()
        if (
            snapshot.released_metadata is not None
            or len(snapshot.locked_metadata_versions) > 0
        ):
            # The use case of creating a new object having anything more than draft metadata
            # is not supported (currently it's irrelevant).
            raise NotImplementedError(
                "The case of creating a new object having anything more"
                " than draft metadata is not supported (yet?)."
            )

        # Create root & value nodes based on the specified NeoModel class.
        root = StudyRoot(uid=snapshot.uid)
        assert snapshot.current_metadata is not None
        value = self._study_value_from_study_metadata_snapshot(
            snapshot.current_metadata
        )
        root.save()
        value.save()
        rel_properties = self._create_versioning_data(snapshot)
        self._db_create_relationship(root.latest_value, value, rel_properties)
        self._db_create_relationship(root.latest_draft, value, rel_properties)
        self._db_create_relationship(root.has_version, value, rel_properties)
        project_node = Project.nodes.get(
            project_number=snapshot.current_metadata.id_metadata.project_number
        )
        study_project_field_node = StudyProjectField()
        study_project_field_node.save()
        study_project_field_node.has_field.connect(project_node)
        value.has_project.connect(study_project_field_node)

        # Log the study value creation in the audit trail
        date = datetime.now(timezone.utc)
        self._generate_study_value_audit_node(
            study_root_node=root,
            study_value_node_after=value,
            study_value_node_before=None,
            change_status=None,
            author_id=self.audit_info.author_id,
            date=date,
        )
        # Log the link to the project in the audit trail
        self._generate_study_field_audit_node(
            study_root_node=root,
            study_field_node_after=study_project_field_node,
            study_field_node_before=None,
            change_status=None,
            author_id=self.audit_info.author_id,
            date=date,
        )

        # Persist study fields and registry identifiers that are inherited
        # from a parent study (e.g. when creating a subpart).  Only call the
        # maintain helpers when there are actual values to persist.
        metadata = snapshot.current_metadata
        has_study_description = (
            metadata.study_description.study_title is not None
            or metadata.study_description.study_short_title is not None
        )
        has_registry_ids = any(
            metadata.get_field_value(cfg.study_field_grouping, cfg.study_field_name)
            is not None
            for cfg in FieldConfiguration.default_field_config()
            if cfg.study_field_data_type == StudyFieldType.REGISTRY
        )
        if has_study_description or has_registry_ids:
            empty_metadata = StudyMetadataVO(
                id_metadata=StudyIdentificationMetadataVO(
                    project_number=metadata.id_metadata.project_number or "",
                    study_number=metadata.id_metadata.study_number,
                    subpart_id=None,
                    study_acronym=None,
                    description=None,
                    registry_identifiers=RegistryIdentifiersVO(),
                ),
                ver_metadata=None,
                high_level_study_design=HighLevelStudyDesignVO(),
                study_population=StudyPopulationVO(),
                study_intervention=StudyInterventionVO(),
                study_description=StudyDescriptionVO(),
            )
            empty_snapshot = StudyDefinitionSnapshot(
                uid=snapshot.uid,
                study_parent_part_uid=snapshot.study_parent_part_uid,
                study_subpart_uids=snapshot.study_subpart_uids,
                current_metadata=empty_metadata,
                draft_metadata=None,
                released_metadata=None,
                locked_metadata_versions=[],
                study_status=snapshot.study_status,
                deleted=False,
            )
            if has_study_description:
                self._maintain_study_fields_relationships(
                    study_root=root,
                    previous_snapshot=empty_snapshot,
                    current_snapshot=snapshot,
                    previous_value=value,
                    expected_latest_value=value,
                    date=date,
                )
            if has_registry_ids:
                self._maintain_study_registry_id_fields_relationships(
                    study_root=root,
                    previous_snapshot=empty_snapshot,
                    current_snapshot=snapshot,
                    previous_value=value,
                    expected_latest_value=value,
                    date=date,
                )

    @staticmethod
    def _generate_study_value_audit_node(
        study_root_node: StudyRoot,
        study_value_node_after: StudyField | None,
        study_value_node_before: StudyField | None,
        change_status: str | None,
        author_id: str | None,
        date: datetime,
    ) -> StudyAction:
        if study_value_node_before is None:
            audit_node = Create()
        elif study_value_node_after is None:
            audit_node = Delete()
        else:
            audit_node = Edit()
        if change_status:
            audit_node.status = change_status
        if author_id:
            audit_node.author_id = author_id
        audit_node.date = date
        audit_node.save()

        if study_value_node_before:
            audit_node.study_value_has_before.connect(study_value_node_before)
        if study_value_node_after:
            audit_node.study_value_node_has_after.connect(study_value_node_after)

        study_root_node.audit_trail.connect(audit_node)
        return audit_node

    def _create_versioning_data(
        self, snapshot: StudyDefinitionSnapshot
    ) -> Mapping[str, Any]:
        assert snapshot.current_metadata is not None
        ver_meta = snapshot.current_metadata.ver_metadata
        assert (
            ver_meta is None
            or ver_meta.version_author is None
            or (
                self.audit_info.author_id
                and ver_meta.version_author
                == UserInfoService.get_author_username_from_id(
                    self.audit_info.author_id
                )
            )
        )
        data = {
            "start_date": ver_meta.version_timestamp if ver_meta else None,
            "end_date": None,
            "status": snapshot.study_status,
            "version": (
                len(snapshot.locked_metadata_versions)
                if snapshot.study_status == StudyStatus.LOCKED.value
                else None
            ),
            "change_description": ver_meta.version_description if ver_meta else None,
            "author_id": self.audit_info.author_id,
        }
        return data

    def _retrieve_fields_audit_trail(
        self, uid: str
    ) -> list[StudyFieldAuditTrailEntryAR] | None:
        query = """
        MATCH (root:StudyRoot {uid: $studyuid})-[:AUDIT_TRAIL]->(action)

        OPTIONAL MATCH (action)-[:BEFORE]->(before)
        WHERE "StudyField" in labels(before) or "StudyValue" in labels(before)
        OPTIONAL MATCH (action)-[:AFTER]->(after)
        WHERE "StudyField" in labels(after) or "StudyValue" in labels(after)
        
        // Preprocess the audit trail structure into the format expected by the API.
        WITH root.uid as study_uid, 
            [x in labels(action) WHERE x <> "StudyAction"][0] as action, 
            action.date as date,
            action.author_id AS author_id,
            CASE
                WHEN before is NULL THEN NULL
                WHEN (before:StudyValue) THEN ["study_acronym", "study_subpart_acronym", "study_id", "study_number"]
                WHEN (before:StudyProjectField) THEN ["project_number"]
                WHEN (before:StudyField) THEN [before.field_name]
                ELSE ["Unknown"]
            END as before_field, 
            CASE
                WHEN before is NULL THEN [NULL,NULL,NULL,NULL]
                WHEN (before:StudyValue) THEN [before.study_acronym, before.study_subpart_acronym, before.study_id_prefix,
                before.study_number, before.description]
                WHEN (before:StudyProjectField) THEN [head([(before)<-[:HAS_FIELD]-(p) | p.project_number])]
                WHEN (before:StudyArrayField) THEN [apoc.text.join(before.value, ', ')]
                WHEN (NOT before.field_name in ["study_acronym", "study_subpart_acronym", "study_id", "study_number"]) THEN [before.value]
            END as before_value, 
            CASE
                //WHEN ("Delete" in labels(action) AND "StudyField" in labels(after)) OR (after is NULL) THEN [NULL,NULL,NULL,NULL]
                WHEN (after:StudyValue) THEN ["study_acronym", "study_subpart_acronym", "study_id", "study_number"]
                WHEN (after:StudyProjectField) THEN ["project_number"]
                WHEN (after:StudyField) THEN [after.field_name]
                ELSE ["Unknown"]
            END as after_field, 
            CASE
                //WHEN ("Delete" in labels(action) AND "StudyField" in labels(after)) OR (after is NULL) THEN [NULL]
                WHEN (after:StudyValue) THEN [after.study_acronym, after.study_subpart_acronym, after.study_id_prefix, after.study_number, after.description]
                WHEN (after:StudyProjectField) THEN [head([(after)<-[:HAS_FIELD]-(p) | p.project_number])]
                WHEN (after:StudyArrayField) THEN [apoc.text.join(after.value, ', ')]
                WHEN (NOT after.field_name in ["study_acronym", "study_subpart_acronym", "study_id", "study_number"]) THEN [after.value]
            END as after_value
        WITH study_uid, date, author_id, action, coalesce(before_field,after_field) as field, before_value as before, after_value as after 
        ORDER BY field ASC
        WITH study_uid, 
            date, 
            author_id, 
            action, 
            apoc.coll.zip(field, apoc.coll.zip(before,after)) as field_with_values_array
            CALL (author_id) {
                OPTIONAL MATCH (author: User)
                WHERE author.user_id = author_id
                RETURN coalesce(author.username, author_id) AS author_username 
            }
        UNWIND field_with_values_array as field_with_value
        WITH *
        WHERE NOT (field_with_value[1][0] IS NOT NULL 
                    AND field_with_value[1][1] IS NOT NULL 
                    AND (field_with_value[1][0] = field_with_value[1][1] and not action = 'Delete')
                )
            AND NOT (field_with_value[1][0] IS NULL 
                    AND field_with_value[1][1] IS NULL
                )
        RETURN study_uid, toString(date) as date, author_id, collect(
            distinct  {action:action, 
             field:field_with_value[0], 
             before:toString(field_with_value[1][0]),  
             after:toString(field_with_value[1][1])
             }) as actions,
             author_username

        ORDER BY date DESC

      """

        query_parameters = {"studyuid": uid}
        result_array, _ = db.cypher_query(query, query_parameters)

        # if the study is not found, return None.
        if len(result_array) == 0:
            return None
        audit_trail = [
            StudyFieldAuditTrailEntryAR(
                study_uid=row[0],
                author_id=row[2],
                author_username=row[4],
                date=row[1],
                actions=[
                    StudyFieldAuditTrailActionVO(
                        section=self.get_section_name_for_study_field(action["field"]),
                        action=action["action"],
                        field_name=self.truncate_code_or_codes_suffix(action["field"]),
                        before_value=action["before"],
                        after_value=action["after"],
                    )
                    for action in row[3]
                    if action["field"] not in ["study_id_prefix"]
                ],
            )
            for row in result_array
        ]
        return audit_trail

    @classmethod
    def truncate_code_or_codes_suffix(
        cls,
        field_name: str,
    ) -> str:
        """
        Truncates code or codes name suffix if exists
        """
        suffixes_to_truncate = ["_code", "_codes"]
        for suffix in suffixes_to_truncate:
            if field_name.endswith(suffix) and "null_value_code" not in field_name:
                field_name = field_name[: -(len(suffix))]
                if field_name == "trial_intent_types":
                    field_name = "trial_intent_type"
        return field_name

    @classmethod
    def get_section_name_for_study_field(cls, field):
        """
        For a given field name, find what logical section of the study properties it belongs to.
        """
        if (
            field in [field.name for field in fields(StudyIdentificationMetadataVO)]  # type: ignore[arg-type]
            or field == "study_id"
        ):
            return "identification_metadata"
        if field in [field.name for field in fields(RegistryIdentifiersVO)]:
            return "registry_identifiers"
        if field in [field.name for field in fields(StudyVersionMetadataVO)]:  # type: ignore[arg-type]
            return "version_metadata"
        if field in [field.name for field in fields(HighLevelStudyDesignVO)]:
            return "high_level_study_design"
        if field in [field.name for field in fields(StudyPopulationVO)]:
            return "study_population"
        if field in [field.name for field in fields(StudyInterventionVO)]:
            return "study_intervention"
        if field in [field.name for field in fields(StudyDescriptionVO)]:
            return "study_description"
        # A study field was found in the audit trail that does not belong to any sections:
        return "Unknown"

    def _build_snapshot_match_clause(
        self,
        study_selection_object_node_id,
        study_selection_object_node_type,
        filter_query_parameters: dict[Any, Any],
        deleted: bool,
    ) -> str:
        if study_selection_object_node_id:
            match_clause = f"""
MATCH (:{study_selection_object_node_type.ROOT_NODE_LABEL}{{uid:$sson_id}})-->(:{study_selection_object_node_type.VALUE_NODE_LABEL})
<-[:{study_selection_object_node_type.STUDY_SELECTION_REL_LABEL}]-(:StudySelection)<-[:{study_selection_object_node_type.STUDY_VALUE_REL_LABEL}]-(sv:StudyValue)
WITH sv
MATCH (sr:StudyRoot)-[:LATEST]->(sv)
"""
            filter_query_parameters["sson_id"] = study_selection_object_node_id
        else:
            match_clause = "MATCH (sr:StudyRoot)-[:LATEST]->(sv:StudyValue)"
        match_clause += (
            f"WHERE {'' if deleted else 'NOT'} EXISTS((sv)<-[:BEFORE]-(:Delete))"
        )
        return match_clause

    def _build_snapshot_alias_clause(self) -> str:
        alias_clause = """
                    sr, sv,
                    head([(sr)-[ll:LATEST_LOCKED]->() | ll]) AS llr,
                    head([(sr)-[lr:LATEST_RELEASED]->(lrn) | {lrr:lr, svr: lrn}]) AS released,
                    head([(sr)-[ld:LATEST_DRAFT]->(sdr) | {ldr:ld, sdr: sdr}]) AS draft,
                    head([(sr)-[hv:HAS_VERSION {status: 'LOCKED'}]->(hvn) | {has_version:hv, svlh:hvn}]) AS locked,
                    head([(sv)<-[:HAS_STUDY_SUBPART]-(:StudyValue)<-[:LATEST]-(parent:StudyRoot) | parent.uid]) AS study_parent_part_uid,
                    [(sv)-[:HAS_STUDY_SUBPART]->(:StudyValue)<-[:LATEST]-(sub:StudyRoot)
                     | sub.uid] AS study_subpart_uids,
                    exists((sr)-[:LATEST_LOCKED]->()) AS has_latest_locked,
                    exists((sr)-[:LATEST_DRAFT]->()) AS has_latest_draft,
                    exists((sr)-[:LATEST_RELEASED]->()) AS has_latest_released,
                    exists((sv)-[:HAS_STUDY_FOOTNOTE]->()) AS has_study_footnote,
                    exists((sv)-[:HAS_STUDY_OBJECTIVE]->()) AS has_study_objective,
                    exists((sv)-[:HAS_STUDY_ENDPOINT]->()) AS has_study_endpoint,
                    exists((sv)-[:HAS_STUDY_CRITERIA]->()) AS has_study_criteria,
                    exists((sv)-[:HAS_STUDY_ACTIVITY]->()) AS has_study_activity,
                    exists((sv)-[:HAS_STUDY_ACTIVITY_INSTRUCTION]->()) AS has_study_activity_instruction
                    WITH sr,
                    sv,
                    study_parent_part_uid,
                    study_subpart_uids,
                    llr,
                    released,
                    draft,
                    locked,
                    has_latest_locked,
                    has_latest_draft,
                    has_latest_released,
                    has_study_footnote,
                    has_study_objective,
                    has_study_endpoint,
                    has_study_criteria,
                    has_study_activity,
                    has_study_activity_instruction,
                    locked.svlh AS svlh,
                    locked.has_version AS has_version,
                    released.lrr AS lrr,
                    released.svr AS svr,
                    draft.ldr AS ldr,
                    draft.sdr AS sdr
                    ORDER BY has_version.end_date ASC
                    WITH *,
                        sr.uid as uid,
                        CASE WHEN ldr.end_date IS NULL THEN 'DRAFT' ELSE 'LOCKED' END as study_status,
                        {
                            study_id: sv.study_id,
                            study_number: sv.study_number,
                            subpart_id: sv.subpart_id,
                            study_acronym: sv.study_acronym,
                            study_subpart_acronym: sv.study_subpart_acronym,
                            study_id_prefix: sv.study_id_prefix,
                            description: sv.description,
                            project_number: head([(sv)-[:HAS_PROJECT]->(:StudyProjectField)<-[:HAS_FIELD]-(p:Project) | p.project_number]),
                            study_title: head([(sv)-[:HAS_TEXT_FIELD]->(t:StudyTextField) WHERE t.field_name = "study_title" | t.value]),
                            study_short_title: head([(sv)-[:HAS_TEXT_FIELD]->(st:StudyTextField) WHERE st.field_name = "study_short_title" | st.value]),
                            version_timestamp: CASE WHEN ldr.end_date IS NULL THEN ldr.start_date ELSE llr.start_date END,
                            version_number: CASE WHEN ldr.end_date IS NULL THEN ldr.version ELSE llr.version END,
                            version_author_id: CASE WHEN ldr.end_date IS NULL THEN ldr.author_id ELSE llr.author_id END
                        } AS current_metadata,
                        CASE WHEN has_latest_locked THEN
                        {
                            locked_metadata_array: [
                                locked_version IN collect({
                                    study_id: svlh.study_id,
                                    study_number: svlh.study_number,
                                    subpart_id: svlh.subpart_id,
                                    study_acronym: svlh.study_acronym,
                                    study_subpart_acronym: svlh.study_subpart_acronym,
                                    study_id_prefix: svlh.study_id_prefix,
                                    description: svlh.description,
                                    project_number: head([(svlh)-[:HAS_PROJECT]->(:StudyProjectField)<-[:HAS_FIELD]-(p:Project) | p.project_number]),
                                    study_title: head([(svlh)-[:HAS_TEXT_FIELD]->(t:StudyTextField) WHERE t.field_name = "study_title" | t.value]),
                                    study_short_title: head([(svlh)-[:HAS_TEXT_FIELD]->(st:StudyTextField) WHERE st.field_name = "study_short_title" | st.value]),
                                    version_timestamp: has_version.start_date,
                                    version_number: has_version.version,
                                    version_author_id: has_version.author_id
                                })
                            ]
                        }  END AS locked_metadata_versions,
                        CASE WHEN has_latest_released AND lrr.end_date IS NULL THEN
                        {
                            study_id: svr.study_id,
                            study_number: svr.study_number,
                            subpart_id: svr.subpart_id,
                            study_acronym: svr.study_acronym,
                            study_subpart_acronym: svr.study_subpart_acronym,
                            study_id_prefix: svr.study_id_prefix,
                            description: svr.description,
                            project_number: head([(svr)-[:HAS_PROJECT]->(:StudyProjectField)<-[:HAS_FIELD]-(p:Project) | p.project_number]),
                            study_title: head([(svr)-[:HAS_TEXT_FIELD]->(t:StudyTextField) WHERE t.field_name = "study_title" | t.value]),
                            study_short_title: head([(svr)-[:HAS_TEXT_FIELD]->(st:StudyTextField) WHERE st.field_name = "study_short_title" | st.value]),
                            version_timestamp: lrr.start_date,
                            version_number: lrr.version_number,
                            version_author_id: lrr.author_id
                        }  END AS released_metadata,
                        CASE WHEN has_latest_draft THEN
                        {
                            study_id: sdr.study_id,
                            study_number: sdr.study_number,
                            subpart_id: sdr.subpart_id,
                            study_acronym: sdr.study_acronym,
                            study_subpart_acronym: sdr.study_subpart_acronym,
                            study_id_prefix: sdr.study_id_prefix,
                            description: sdr.description,
                            project_number: head([(sdr)-[:HAS_PROJECT]->(:StudyProjectField)<-[:HAS_FIELD]-(p:Project) | p.project_number]),
                            study_title: head([(sdr)-[:HAS_TEXT_FIELD]->(t:StudyTextField) WHERE t.field_name = "study_title" | t.value]),
                            study_short_title: head([(sdr)-[:HAS_TEXT_FIELD]->(st:StudyTextField) WHERE st.field_name = "study_short_title" | st.value]),
                            version_timestamp: ldr.start_date,
                            version_number: ldr.version_number,
                            version_author_id: ldr.author_id
                        }  END AS draft_metadata,
                        has_study_footnote,
                        has_study_objective,
                        has_study_endpoint,
                        has_study_criteria,
                        has_study_activity,
                        has_study_activity_instruction
                    """
        return alias_clause

    def _update_snapshot_filter_by(
        self,
        filter_by: dict[str, dict[str, Any]],
        has_study_footnote: bool | None = None,
        has_study_objective: bool | None = None,
        has_study_endpoint: bool | None = None,
        has_study_criteria: bool | None = None,
        has_study_activity: bool | None = None,
        has_study_activity_instruction: bool | None = None,
    ) -> dict[str, dict[str, Any]]:
        if has_study_footnote is not None:
            filter_by["has_study_footnote"] = {"v": [has_study_footnote]}
        if has_study_objective is not None:
            filter_by["has_study_objective"] = {"v": [has_study_objective]}
        if has_study_endpoint is not None:
            filter_by["has_study_endpoint"] = {"v": [has_study_endpoint]}
        if has_study_criteria is not None:
            filter_by["has_study_criteria"] = {"v": [has_study_criteria]}
        if has_study_activity is not None:
            filter_by["has_study_activity"] = {"v": [has_study_activity]}
        if has_study_activity_instruction is not None:
            filter_by["has_study_activity_instruction"] = {
                "v": [has_study_activity_instruction]
            }
        return filter_by

    def _retrieve_all_snapshots(
        self,
        has_study_footnote: bool | None = None,
        has_study_objective: bool | None = None,
        has_study_endpoint: bool | None = None,
        has_study_criteria: bool | None = None,
        has_study_activity: bool | None = None,
        has_study_activity_instruction: bool | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_selection_object_node_id: int | str | None = None,
        study_selection_object_node_type: NodeMeta | None = None,
        deleted: bool = False,
    ) -> GenericFilteringReturn[StudyDefinitionSnapshot]:
        # To build StudyDefinitionSnapshot (domain object) we need 5 main members:
        # * uid
        # * study_status
        # * current_metadata (can't be None)
        #   - retrieved in 'AS current_metadata' section
        # * released_metadata (can be None)
        #   - retrieved in 'AS released_metadata" section (if there is such need)
        # * locked_metadata_versions (can be None) - array of locked_metadata ordered by end_date property
        #   - retrieved in 'AS locked_metadata_versions' section (if there is such need)
        # All of the above members are fetched in the query below.
        # The following query contains some representation logic (mainly in parts where the CASE clause is used)
        # The logic was taken from the already existing implementation of retrieving single Study.

        if sort_by is None:
            sort_by = {"uid": True}

        if filter_by is None:
            filter_by = {}

        # Specific filtering
        filter_query_parameters: dict[Any, Any] = {}

        match_clause = self._build_snapshot_match_clause(
            study_selection_object_node_id,
            study_selection_object_node_type,
            filter_query_parameters,
            deleted,
        )
        alias_clause = self._build_snapshot_alias_clause()
        filter_by = self._update_snapshot_filter_by(
            filter_by,
            has_study_footnote,
            has_study_objective,
            has_study_endpoint,
            has_study_criteria,
            has_study_activity,
            has_study_activity_instruction,
        )

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
            return_model=StudyDefinitionSnapshot,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()

        # the following code formats the output of the neomodel query
        # it assigns the names for the properties of each Study, as neomodel
        # returns names of the properties in the separate array
        studies = []
        for study in result_array:
            study_dictionary = {}
            for study_property, attribute_name in zip(study, attributes_names):
                study_dictionary[attribute_name] = study_property
            studies.append(study_dictionary)

        total = calculate_total_count_from_query_result(
            len(studies), page_number, page_size, total_count
        )
        if total is None:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                total = count_result[0][0]
            else:
                total = 0

        return GenericFilteringReturn(
            items=self._retrieve_all_snapshots_from_cypher_query_result(
                studies, deleted=deleted
            ),
            total=total,
        )

    def generate_uid(self) -> str:
        return StudyRoot.get_next_free_uid_and_increment_counter()

    @staticmethod
    def _generate_study_field_audit_node(
        study_root_node: StudyRoot,
        study_field_node_after: StudyField | None,
        study_field_node_before: StudyField | None,
        change_status: str | None,
        author_id: str | None,
        date: datetime,
        to_delete: bool = False,
    ) -> StudyAction:
        """
        Updates the audit trail when study fields are added, removed or modified.
        """
        if study_field_node_before is None:
            audit_node = Create()
        elif study_field_node_after is None or to_delete:
            audit_node = Delete()
        else:
            audit_node = Edit()
        if change_status:
            audit_node.status = change_status
        if author_id:
            audit_node.author_id = author_id
        audit_node.date = date
        audit_node.save()

        if study_field_node_before:
            audit_node.study_field_has_before.connect(study_field_node_before)
        # For Delete actions, AFTER points to the deleted node (the before node)
        # so the audit trail has a required outgoing AFTER relationship.
        after_node = study_field_node_after or study_field_node_before
        if after_node:
            audit_node.study_field_node_has_after.connect(after_node)

        study_root_node.audit_trail.connect(audit_node)
        return audit_node

    def get_preferred_time_unit(
        self,
        study_uid: str,
        for_protocol_soa: bool = False,
        study_value_version: str | None = None,
    ) -> list[StudyTimeField]:
        filters = {
            "field_name": (
                settings.study_field_soa_preferred_time_unit_name
                if for_protocol_soa
                else settings.study_field_preferred_time_unit_name
            ),
        }
        if study_value_version:
            filters.update(
                {
                    "has_time_field__has_version__uid": study_uid,
                    "has_time_field__has_version|version": study_value_version,
                    "has_time_field__has_version|status": StudyStatus.RELEASED.value,
                }
            )
        else:
            filters.update(
                {
                    "has_time_field__latest_value__uid": study_uid,
                }
            )
        nodes = StudyTimeField.nodes.traverse(
            "has_unit_definition__has_latest_value",
            "has_after__audit_trail",
        ).filter(**filters)
        return nodes.resolve_subgraph()

    def post_preferred_time_unit(
        self, study_uid: str, unit_definition_uid: str, for_protocol_soa: bool = False
    ) -> list[StudyPreferredTimeUnit]:
        nodes = self.get_preferred_time_unit(
            study_uid=study_uid, for_protocol_soa=for_protocol_soa
        )

        exceptions.AlreadyExistsException.raise_if(
            nodes,
            msg=f"There already exists a Preferred Time Unit for the Study with UID '{study_uid}'.",
        )

        study_root = StudyRoot.nodes.get(uid=study_uid)
        latest_study_value = study_root.latest_value.single()
        unit_definition = UnitDefinitionRoot.nodes.get(uid=unit_definition_uid)
        preferred_time_field_sf = StudyTimeField(
            value=unit_definition_uid,
            field_name=(
                settings.study_field_soa_preferred_time_unit_name
                if for_protocol_soa
                else settings.study_field_preferred_time_unit_name
            ),
        ).save()
        preferred_time_field_sf.has_unit_definition.connect(unit_definition)
        latest_study_value.has_time_field.connect(preferred_time_field_sf)

        self._generate_study_field_audit_node(
            study_root_node=study_root,
            study_field_node_after=preferred_time_field_sf,
            study_field_node_before=None,
            change_status=None,
            author_id=self.audit_info.author_id,
            date=datetime.now(timezone.utc),
        )
        return self.get_preferred_time_unit(
            study_uid=study_uid, for_protocol_soa=for_protocol_soa
        )

    def edit_preferred_time_unit(
        self, study_uid: str, unit_definition_uid: str, for_protocol_soa: bool = False
    ) -> list[StudyPreferredTimeUnit]:
        # getting previous preferred time unit study field
        previous_time_fields = self.get_preferred_time_unit(
            study_uid=study_uid, for_protocol_soa=for_protocol_soa
        )

        exceptions.BusinessLogicException.raise_if(
            len(previous_time_fields) > 1,
            msg="Returned more than one previous preferred StudyTimeField nodes",
        )
        exceptions.BusinessLogicException.raise_if(
            len(previous_time_fields) == 0,
            msg="The previous preferred StudyTimeField node was not found",
        )

        previous_time_field = previous_time_fields[0]

        study_root = StudyRoot.nodes.get(uid=study_uid)
        latest_study_value = study_root.latest_value.single()
        unit_definition = UnitDefinitionRoot.nodes.get(uid=unit_definition_uid)

        # creating (soa_)preferred_time_unit StudyTimeField node
        preferred_time_field_sf = StudyTimeField(
            value=unit_definition_uid,
            field_name=(
                settings.study_field_soa_preferred_time_unit_name
                if for_protocol_soa
                else settings.study_field_preferred_time_unit_name
            ),
        ).save()

        # connecting (soa_)preferred_time_unit StudyTimeField node to the UnitDefinitionRoot node
        preferred_time_field_sf.has_unit_definition.connect(unit_definition)

        # connecting StudyValue node to the StudyTimeField node
        latest_study_value.has_time_field.connect(preferred_time_field_sf)

        # disconnecting StudyValue from the :BEFORE version of StudyTimeField
        latest_study_value.has_time_field.disconnect(previous_time_field)

        exceptions.BusinessLogicException.raise_if(
            previous_time_field.value == unit_definition_uid,
            msg=f"The Preferred Time Unit for the Study with UID '{study_uid}' is already '{unit_definition_uid}'.",
        )

        self._generate_study_field_audit_node(
            study_root_node=study_root,
            study_field_node_after=preferred_time_field_sf,
            study_field_node_before=previous_time_field,
            change_status=None,
            author_id=self.audit_info.author_id,
            date=datetime.now(timezone.utc),
        )
        return self.get_preferred_time_unit(
            study_uid=study_uid, for_protocol_soa=for_protocol_soa
        )

    def study_exists_by_uid(self, study_uid: str) -> bool:
        return bool(StudyRoot.nodes.get_or_none(uid=study_uid))

    def check_if_study_is_locked(self, study_uid: str) -> bool:
        root = StudyRoot.nodes.get_or_none(uid=study_uid)

        exceptions.NotFoundException.raise_if(root is None, "Study", study_uid)

        is_study_locked = (
            root.latest_locked.get_or_none() == root.latest_value.get_or_none()
        )
        return is_study_locked

    @classmethod
    def check_if_study_is_deleted(cls, study_uid: str) -> bool:
        root = StudyRoot.nodes.get_or_none(uid=study_uid)

        exceptions.NotFoundException.raise_if(root is None, "Study", study_uid)

        query = """
            MATCH (study_root:StudyRoot {uid: $uid})-[:LATEST]->(:StudyValue)<-[:BEFORE]-(:Delete)
            RETURN study_root
            """
        result, _ = db.cypher_query(query, {"uid": study_uid})
        return len(result) > 0 and len(result[0]) > 0

    @staticmethod
    def check_if_study_uid_and_version_exists(
        study_uid: str, study_value_version: str | None = None
    ) -> bool:
        if study_value_version:
            query = """
                MATCH (r:StudyRoot {uid: $uid})-[hv:HAS_VERSION]->(v:StudyValue)
                WHERE NOT EXISTS((v)<-[:BEFORE]-(:Delete)) AND hv.version=$version
                RETURN r
                """
        else:
            query = """
                MATCH (r:StudyRoot {uid: $uid})-[:LATEST]->(v:StudyValue)
                WHERE NOT EXISTS((v)<-[:BEFORE]-(:Delete))
                RETURN r
                """

        result, _ = db.cypher_query(
            query, {"uid": study_uid, "version": study_value_version}
        )

        return len(result) > 0 and len(result[0]) > 0

    @staticmethod
    @trace_calls(args=[0, 1], kwargs=["study_uid", "study_value_version"])
    def get_study_id(
        study_uid: str, study_value_version: str | None = None
    ) -> str | None:
        """Efficiently retrieves the Study ID for a given Study uid and version."""

        if study_value_version:
            query = [
                "MATCH (study_root:StudyRoot {uid: $uid})-[has_version:HAS_VERSION]->(study_value:StudyValue)",
                "WHERE NOT EXISTS((study_value)<-[:BEFORE]-(:Delete)) AND has_version.version=$version",
            ]
        else:
            query = [
                "MATCH (study_root:StudyRoot {uid: $uid})-[:LATEST]->(study_value:StudyValue)",
                "WHERE NOT EXISTS((study_value)<-[:BEFORE]-(:Delete))",
            ]

        query.append("RETURN study_value")

        results, _ = db.cypher_query(
            "\n".join(query), {"uid": study_uid, "version": study_value_version}
        )

        if len(results):
            study_value = results[0][0]

            study_id_prefix = study_value.get("study_id_prefix")
            study_number = study_value.get("study_number")
            study_subpart_acronym = study_value.get("study_subpart_acronym")

            if study_number and study_id_prefix:
                study_id = f"{study_id_prefix}-{study_number}"
                if study_subpart_acronym:
                    study_id += f"-{study_subpart_acronym}"
                return study_id

        return None

    def get_latest_released_version_from_specific_datetime(
        self, study_uid: str, specified_datetime: str
    ) -> str | None:
        version_relationships = (
            StudyValue.nodes.traverse("has_version")
            .filter(
                **{
                    "has_version|end_date__lte": datetime.fromisoformat(
                        specified_datetime
                    ),
                    "has_version|status": "RELEASED",
                    "has_version__uid": study_uid,
                }
            )
            .order_by("-has_version|end_date")
            .all()
        )

        if len(version_relationships) == 0:
            return None

        latest_version_relationship = version_relationships[0]
        return latest_version_relationship[2].version

    def _retrieve_study_subpart_with_history(
        self,
        uid: str,
        is_subpart: bool = False,
        study_value_version: str | None = None,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """
        returns the audit trail for all study subparts of the study
        """
        params: dict[str, str | list[str] | int] = {}
        if not is_subpart:
            params = {"study_uid": uid}
            if study_value_version:
                version = "{version: $study_value_version}"
                params["study_value_version"] = study_value_version
            else:
                version = ""

            subpart_uids = db.cypher_query(
                f"""
                MATCH (:StudyRoot {{uid: $study_uid}})-[:HAS_VERSION{version}]->(:StudyValue)
                -[:HAS_STUDY_SUBPART]->(:StudyValue)<-[:HAS_VERSION]-(ssr:StudyRoot)
                RETURN DISTINCT ssr.uid
                """,
                params=params,
            )
            subpart_uids = [subpart_uid[0] for subpart_uid in subpart_uids[0]]
        else:
            subpart_uids = [uid]

        params = {"subpart_uids": subpart_uids, "uid": uid}
        if study_value_version:
            version = "{version: $study_value_version}"
            params["study_value_version"] = study_value_version
        else:
            version = ""

        if not is_subpart and version:
            parent_in_version = f"<-[:HAS_STUDY_SUBPART]-(:StudyValue)<-[:HAS_VERSION{version}]-(:StudyRoot {{uid: $uid}})"
        else:
            parent_in_version = ""

        base_query = f"""
            MATCH (ssr:StudyRoot)-[h_rel:HAS_VERSION]->(ssv:StudyValue)
            {parent_in_version}
            WHERE ssr.uid IN $subpart_uids
            OPTIONAL MATCH (ssv)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (ssv)<-[:BEFORE]-(bsa:StudyAction)
            OPTIONAL MATCH (ssv)<-[:HAS_STUDY_SUBPART]-(psv:StudyValue)<-[p_h_rel:HAS_VERSION]-(psr:StudyRoot)
        """

        if page_size > 0:
            validate_max_skip_clause(page_number=page_number, page_size=page_size)
            skip = (page_number - 1) * page_size
            params["skip"] = skip
            params["limit"] = page_size
            pagination_clause = "SKIP $skip LIMIT $limit"
        else:
            pagination_clause = ""

        rs = db.cypher_query(
            f"""
            {base_query}
            RETURN DISTINCT
                psr.uid AS parent_uid,
                ssr.uid AS subpart_uid,
                ssv.subpart_id AS subpart_id,
                ssv.study_acronym AS study_acronym,
                ssv.study_subpart_acronym AS study_subpart_acronym,
                h_rel.author_id AS author_id,
                h_rel.start_date AS start_date,
                h_rel.end_date AS end_date,
                labels(asa) AS change_type
                ORDER BY start_date DESC
                {pagination_clause}
            """,
            params=params,
        )
        rs = utils.db_result_to_list(rs)
        rs.reverse()

        total = -1
        if total_count:
            count_result = db.cypher_query(
                f"""
                {base_query}
                WITH DISTINCT
                    psr.uid AS parent_uid,
                    ssr.uid AS subpart_uid,
                    ssv.subpart_id AS subpart_id,
                    ssv.study_acronym AS study_acronym,
                    ssv.study_subpart_acronym AS study_subpart_acronym,
                    h_rel.author_id AS author_id,
                    h_rel.start_date AS start_date,
                    h_rel.end_date AS end_date,
                    labels(asa) AS change_type
                RETURN count(*) AS total
                """,
                params=params,
            )
            total = count_result[0][0][0]

        result = []
        if not is_subpart:
            subpart_status = set()
            for item in rs:
                if item["parent_uid"] is not None and item["parent_uid"] != uid:
                    continue
                if item["subpart_uid"] not in subpart_status and not item["parent_uid"]:
                    continue

                if item["parent_uid"]:
                    subpart_status.add(item["subpart_uid"])
                    remove = False
                else:
                    remove = True

                change_type = ""
                for action in item["change_type"]:
                    if "StudyAction" not in action:
                        change_type = action

                if item["subpart_uid"] in subpart_status:
                    result.append(
                        {
                            "subpart_uid": item["subpart_uid"],
                            "subpart_id": (
                                item["subpart_id"] if item["parent_uid"] else None
                            ),
                            "study_acronym": (
                                item["study_acronym"] if item["parent_uid"] else None
                            ),
                            "study_subpart_acronym": (
                                item["study_subpart_acronym"]
                                if item["parent_uid"]
                                else None
                            ),
                            "start_date": convert_to_datetime(value=item["start_date"]),
                            "end_date": (
                                convert_to_datetime(value=item["end_date"])
                                if item["end_date"]
                                else None
                            ),
                            "author_username": item["author_id"],
                            "change_type": (
                                change_type if item["parent_uid"] else "Delete"
                            ),
                        }
                    )

                    if remove:
                        subpart_status.remove(item["subpart_uid"])
        else:
            for item in rs:
                for action in item["change_type"]:
                    if "StudyAction" not in action:
                        change_type = action

                result.append(
                    {
                        "subpart_uid": item["subpart_uid"],
                        "subpart_id": item["subpart_id"],
                        "study_acronym": item["study_acronym"],
                        "study_subpart_acronym": item["study_subpart_acronym"],
                        "start_date": convert_to_datetime(value=item["start_date"]),
                        "end_date": (
                            convert_to_datetime(value=item["end_date"])
                            if item["end_date"]
                            else None
                        ),
                        "author_username": item["author_id"],
                        "change_type": change_type,
                    }
                )

        result.reverse()

        items = calculate_diffs(result, StudySubpartAuditTrail)
        return GenericFilteringReturn(items=items, total=total)

    # ------------------------------------------------------------------
    # Study Other Attributes (TS-parameter side-channel — see
    # `routers/studies/studies.py::get_study_other_attributes`).
    # ------------------------------------------------------------------

    # Mapping of semantic data type name → (StudyField subclass,
    # StudyValue relationship attribute). Used both when persisting new
    # values (POST/PATCH) and when locating the existing field of a
    # previous data type to detach it.
    _OTHER_ATTRIBUTE_TYPE_MAP: dict[str, tuple[type[StudyField], str]] = {
        "Boolean": (StudyBooleanField, "has_boolean_field"),
        "Date": (StudyTimeField, "has_time_field"),
        "DateTime": (StudyTimeField, "has_time_field"),
        "Datetime": (StudyTimeField, "has_time_field"),
        "Duration": (StudyTimeField, "has_time_field"),
        "Time": (StudyTimeField, "has_time_field"),
    }
    _OTHER_ATTRIBUTE_DEFAULT_TYPE: tuple[type[StudyField], str] = (
        StudyTextField,
        "has_text_field",
    )

    @classmethod
    def _other_attribute_rel_for(cls, study_field: StudyField) -> str:
        """Reverse-lookup the StudyValue rel attribute for an existing
        StudyField, using the same map that drove its creation."""
        for field_class, rel_name in (
            *cls._OTHER_ATTRIBUTE_TYPE_MAP.values(),
            cls._OTHER_ATTRIBUTE_DEFAULT_TYPE,
        ):
            if isinstance(study_field, field_class):
                return rel_name
        return cls._OTHER_ATTRIBUTE_DEFAULT_TYPE[1]

    def list_study_other_attributes(
        self,
        study_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[dict[str, Any]]:
        """Return one row per TS-parameter CTTerm visible on the
        Other Study Attributes page (filtered by `osb_page_reference`)
        that has a parameter_value assigned (i.e. a StudyField exists)."""

        if sort_by is None:
            sort_by = {"parameter": True}
        sort_by = {self._OTHER_ATTR_FIELD_MAP.get(k, k): v for k, v in sort_by.items()}

        if filter_by is None:
            filter_by = {}
        filter_by = {
            self._OTHER_ATTR_FIELD_MAP.get(k, k): v for k, v in filter_by.items()
        }

        match_clause = """
            MATCH (:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)
            MATCH (parmcd_cl:CTCodelistRoot {uid: $parmcd_uid})-[ht:HAS_TERM]->(clt:CTCodelistTerm)
                -[:HAS_TERM_ROOT]->(term_root:CTTermRoot)
            WHERE ht.end_date IS NULL
            MATCH (term_root)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)
                -[:LATEST_FINAL]->(ctnv:CTTermNameValue)
            MATCH (ctnv)-[:RELATED_STUDY_FIELD_SELECTION]
                ->(msf:MetaStudyField {osb_page_reference: $page_ref})
            MATCH (sv)-->(sf:StudyField)-[:HAS_META_STUDY_FIELD]->(msf)
                WHERE sf.field_name = ctnv.name
            OPTIONAL MATCH (msf)-[:HAS_SEMANTIC_DATA_TYPE]->(:CTTermContext)
                -[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]
                ->(:CTTermNameRoot)-[:LATEST]->(dt_name:CTTermNameValue)
            OPTIONAL MATCH (ctnv)-[:RESPONSE_CODELIST]->(resp_cl:CTCodelistRoot)
            OPTIONAL MATCH (resp_cl)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)
                -[:LATEST_FINAL]->(resp_cl_name:CTCodelistNameValue)
            OPTIONAL MATCH (sf)-[:HAS_REASON_FOR_NULL_VALUE]->(:CTTermContext)
                -[:HAS_SELECTED_TERM]->(nf:CTTermRoot)
            OPTIONAL MATCH (nf)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)
                -[:LATEST_FINAL]->(nf_name:CTTermNameValue)
            OPTIONAL MATCH (sf)<-[:AFTER]-(audit:StudyAction)
        """
        alias_clause = """DISTINCT
                term_root.uid              AS ts_parameter_term_uid,
                clt.submission_value       AS code,
                ctnv.name                  AS parameter,
                ctnv.reference             AS reference,
                ctnv.required_level        AS required_level,
                dt_name.name               AS semantic_data_type,
                resp_cl.uid                AS response_codelist_uid,
                resp_cl_name.name          AS response_codelist_name,
                ctnv.notes                 AS notes,
                sf.value                   AS parameter_value,
                nf.uid                     AS null_flavor_term_uid,
                nf_name.name               AS null_flavor_term_name,
                audit.date                 AS start_date,
                coalesce(head([(user:User)-[*0]-() WHERE user.user_id=audit.author_id | user.username]), audit.author_id) AS author_username
        """

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
            return_model=StudyOtherAttributeColumns,
        )
        query.parameters.update(
            {
                "study_uid": study_uid,
                "parmcd_uid": settings.ts_parmcd_codelist_uid,
                "parm_uid": settings.ts_parm_codelist_uid,
                "page_ref": settings.study_other_attributes_page_reference,
            }
        )

        result_array, attributes_names = query.execute()
        keys = [str(name) for name in attributes_names]
        rows = [dict(zip(keys, row)) for row in result_array]

        total = calculate_total_count_from_query_result(
            len(rows), page_number, page_size, total_count
        )
        if total is None:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            total = count_result[0][0] if len(count_result) > 0 else 0

        return GenericFilteringReturn(items=rows, total=total)

    # Map nested response-model field names to internal flat column aliases
    _OTHER_ATTR_FIELD_MAP: dict[str, str] = {
        "response_codelist.sponsor_preferred_name": "response_codelist_name",
        "response_codelist.uid": "response_codelist_uid",
        "null_flavor.sponsor_preferred_name": "null_flavor_term_name",
        "null_flavor.uid": "null_flavor_term_uid",
    }

    def get_distinct_other_attribute_headers(
        self,
        study_uid: str,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ) -> list[Any]:
        """Return distinct values for *field_name* across all Other Study
        Attribute rows that have a value assigned, suitable for populating a filter drop-down.
        """

        field_name = self._OTHER_ATTR_FIELD_MAP.get(field_name, field_name)
        if filter_by:
            filter_by = {
                self._OTHER_ATTR_FIELD_MAP.get(k, k): v for k, v in filter_by.items()
            }

        match_clause = """
            MATCH (:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)
            MATCH (parmcd_cl:CTCodelistRoot {uid: $parmcd_uid})-[ht:HAS_TERM]->(clt:CTCodelistTerm)
                -[:HAS_TERM_ROOT]->(term_root:CTTermRoot)
            WHERE ht.end_date IS NULL
            MATCH (term_root)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)
                -[:LATEST_FINAL]->(ctnv:CTTermNameValue)
            MATCH (ctnv)-[:RELATED_STUDY_FIELD_SELECTION]
                ->(msf:MetaStudyField {osb_page_reference: $page_ref})
            MATCH (sv)-->(sf:StudyField)-[:HAS_META_STUDY_FIELD]->(msf)
                WHERE sf.field_name = ctnv.name
            OPTIONAL MATCH (msf)-[:HAS_SEMANTIC_DATA_TYPE]->(:CTTermContext)
                -[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]
                ->(:CTTermNameRoot)-[:LATEST]->(dt_name:CTTermNameValue)
            OPTIONAL MATCH (ctnv)-[:RESPONSE_CODELIST]->(resp_cl:CTCodelistRoot)
            OPTIONAL MATCH (resp_cl)-[:HAS_NAME_ROOT]->(:CTCodelistNameRoot)
                -[:LATEST_FINAL]->(resp_cl_name:CTCodelistNameValue)
            OPTIONAL MATCH (sf)-[:HAS_REASON_FOR_NULL_VALUE]->(:CTTermContext)
                -[:HAS_SELECTED_TERM]->(nf:CTTermRoot)
            OPTIONAL MATCH (nf)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)
                -[:LATEST_FINAL]->(nf_name:CTTermNameValue)
            OPTIONAL MATCH (sf)<-[:AFTER]-(audit:StudyAction)
        """
        alias_clause = """DISTINCT
                term_root.uid              AS ts_parameter_term_uid,
                clt.submission_value       AS code,
                ctnv.name                  AS parameter,
                ctnv.reference             AS reference,
                ctnv.required_level        AS required_level,
                dt_name.name               AS semantic_data_type,
                resp_cl.uid                AS response_codelist_uid,
                resp_cl_name.name          AS response_codelist_name,
                ctnv.notes                 AS notes,
                sf.value                   AS parameter_value,
                nf.uid                     AS null_flavor_term_uid,
                nf_name.name               AS null_flavor_term_name,
                audit.date                 AS start_date,
                coalesce(head([(user:User)-[*0]-() WHERE user.user_id=audit.author_id | user.username]), audit.author_id) AS author_username
        """

        filter_by = validate_filters_and_add_search_string(
            search_string, field_name, filter_by
        )

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            return_model=StudyOtherAttributeColumns,
        )
        query.parameters.update(
            {
                "study_uid": study_uid,
                "parmcd_uid": settings.ts_parmcd_codelist_uid,
                "parm_uid": settings.ts_parm_codelist_uid,
                "page_ref": settings.study_other_attributes_page_reference,
            }
        )
        query.full_query = query.build_header_query(
            header_alias=field_name, page_size=page_size
        )
        result_array, _ = query.execute()

        return (
            format_generic_header_values(result_array[0][0])
            if len(result_array) > 0
            else []
        )

    def _resolve_other_attribute_meta_study_field(
        self, ts_parameter_term_uid: str
    ) -> tuple[MetaStudyField, type[StudyField], str, str]:
        """Walk CTTermRoot → latest CTTermNameValue → MetaStudyField and
        also resolve the StudyField subclass + StudyValue rel attribute
        from the MetaStudyField's semantic data type.

        Returns ``(msf, field_class, rel_name, term_name)`` where
        *term_name* is the CTTermNameValue name — used as the unique
        ``field_name`` when persisting the StudyField.

        Validates that the term is on the Other Study Attributes page.
        Falls back to (StudyTextField, "has_text_field") when the data
        type is missing or unknown.
        """
        rows, _ = db.cypher_query(
            """
            MATCH (term_root:CTTermRoot {uid: $uid})-[:HAS_NAME_ROOT]
                ->(:CTTermNameRoot)-[:LATEST_FINAL]
                ->(ctnv:CTTermNameValue)
            MATCH (cl:CTCodelistRoot)-[ht:HAS_TERM]->(:CTCodelistTerm)
                -[:HAS_TERM_ROOT]->(term_root)
            WHERE cl.uid IN [$parmcd_uid, $parm_uid] AND ht.end_date IS NULL
            MATCH (ctnv)-[:RELATED_STUDY_FIELD_SELECTION]->(msf:MetaStudyField {osb_page_reference: $page_ref})
            OPTIONAL MATCH (msf)-[:HAS_SEMANTIC_DATA_TYPE]->(:CTTermContext)
                -[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]
                ->(:CTTermNameRoot)-[:LATEST]->(dt:CTTermNameValue)
            RETURN msf, dt.name AS data_type_name, ctnv.name AS term_name
            """,
            {
                "uid": ts_parameter_term_uid,
                "page_ref": settings.study_other_attributes_page_reference,
                "parmcd_uid": settings.ts_parmcd_codelist_uid,
                "parm_uid": settings.ts_parm_codelist_uid,
            },
            resolve_objects=True,
        )
        exceptions.NotFoundException.raise_if(
            not rows,
            msg=(
                f"TS parameter CT term '{ts_parameter_term_uid}' was not found, "
                f"is not in codelists '{settings.ts_parmcd_codelist_uid}' / "
                f"'{settings.ts_parm_codelist_uid}', is not configured for the "
                f"Other Study Attributes page, or has no related MetaStudyField."
            ),
        )
        msf, data_type_name, term_name = rows[0]
        field_class, rel_name = self._OTHER_ATTRIBUTE_TYPE_MAP.get(
            data_type_name or "", self._OTHER_ATTRIBUTE_DEFAULT_TYPE
        )
        return msf, field_class, rel_name, term_name

    def _get_existing_other_attribute_field(
        self,
        study_uid: str,
        meta_study_field: MetaStudyField,
        field_name: str,
    ) -> StudyField | None:
        rows, _ = db.cypher_query(
            """
            MATCH (:StudyRoot {uid: $study_uid})-[:LATEST]->(:StudyValue)
                -->(sf:StudyField)-[:HAS_META_STUDY_FIELD]->(msf:MetaStudyField)
            WHERE elementId(msf) = $msf_eid AND sf.field_name = $field_name
            RETURN sf
            """,
            {
                "study_uid": study_uid,
                "msf_eid": meta_study_field.element_id_property,
                "field_name": field_name,
            },
            resolve_objects=True,
        )
        return rows[0][0] if rows else None

    def _attach_null_flavor(
        self, study_field: StudyField, null_flavor_term_uid: str
    ) -> None:
        null_value_reason_node = self._get_associated_ct_term_root_node(
            term_uid=null_flavor_term_uid,
            study_field_name="Other Study Attribute Null Flavor",
        )
        null_value_reason_node = (
            CTCodelistAttributesRepository().get_or_create_selected_term(
                null_value_reason_node,
                codelist_submission_value=settings.null_flavor_cl_submval,
                catalogue_name=settings.sdtm_ct_catalogue_name,
            )
        )
        study_field.has_reason_for_null_value.connect(null_value_reason_node)

    def post_study_other_attribute(
        self,
        study_uid: str,
        ts_parameter_term_uid: str,
        parameter_value: str | bool | None,
        null_flavor_term_uid: str | None,
    ) -> None:
        meta_study_field, field_class, rel_name, term_name = (
            self._resolve_other_attribute_meta_study_field(ts_parameter_term_uid)
        )
        study_root = StudyRoot.nodes.get(uid=study_uid)
        latest_study_value = study_root.latest_value.single()

        exceptions.AlreadyExistsException.raise_if(
            self._get_existing_other_attribute_field(
                study_uid, meta_study_field, term_name
            )
            is not None,
            msg=(
                f"Study with UID '{study_uid}' already has an Other Study Attribute "
                f"selection for TS parameter '{ts_parameter_term_uid}'."
            ),
        )

        new_field = self._create_other_attribute_field(
            field_class, meta_study_field, parameter_value, term_name
        )
        getattr(latest_study_value, rel_name).connect(new_field)
        if null_flavor_term_uid:
            self._attach_null_flavor(new_field, null_flavor_term_uid)

        self._generate_study_field_audit_node(
            study_root_node=study_root,
            study_field_node_after=new_field,
            study_field_node_before=None,
            change_status=None,
            author_id=self.audit_info.author_id,
            date=datetime.now(timezone.utc),
        )

    def edit_study_other_attribute(
        self,
        study_uid: str,
        ts_parameter_term_uid: str,
        parameter_value: str | bool | None,
        null_flavor_term_uid: str | None,
    ) -> None:
        meta_study_field, field_class, rel_name, term_name = (
            self._resolve_other_attribute_meta_study_field(ts_parameter_term_uid)
        )
        study_root = StudyRoot.nodes.get(uid=study_uid)
        latest_study_value = study_root.latest_value.single()

        previous_field = self._get_existing_other_attribute_field(
            study_uid, meta_study_field, term_name
        )
        exceptions.NotFoundException.raise_if(
            previous_field is None,
            msg=(
                f"Study with UID '{study_uid}' has no Other Study Attribute "
                f"selection for TS parameter '{ts_parameter_term_uid}'. "
                f"Use POST to create one first."
            ),
        )
        assert (
            previous_field is not None
        )  # for type checker; raise_if above guarantees this

        new_field = self._create_other_attribute_field(
            field_class, meta_study_field, parameter_value, term_name
        )
        getattr(latest_study_value, rel_name).connect(new_field)
        # The previous field's class tells us which HAS_*_FIELD edge to
        # detach (it may differ from the new one if the data type changed).
        getattr(
            latest_study_value, self._other_attribute_rel_for(previous_field)
        ).disconnect(previous_field)
        if null_flavor_term_uid:
            self._attach_null_flavor(new_field, null_flavor_term_uid)

        self._generate_study_field_audit_node(
            study_root_node=study_root,
            study_field_node_after=new_field,
            study_field_node_before=previous_field,
            change_status=None,
            author_id=self.audit_info.author_id,
            date=datetime.now(timezone.utc),
        )

    def delete_study_other_attribute(
        self,
        study_uid: str,
        ts_parameter_term_uid: str,
    ) -> None:
        meta_study_field, _, _, term_name = (
            self._resolve_other_attribute_meta_study_field(ts_parameter_term_uid)
        )
        study_root = StudyRoot.nodes.get(uid=study_uid)
        latest_study_value = study_root.latest_value.single()

        existing_field = self._get_existing_other_attribute_field(
            study_uid, meta_study_field, term_name
        )
        exceptions.NotFoundException.raise_if(
            existing_field is None,
            msg=(
                f"Study with UID '{study_uid}' has no Other Study Attribute "
                f"selection for TS parameter '{ts_parameter_term_uid}'."
            ),
        )
        assert existing_field is not None

        getattr(
            latest_study_value, self._other_attribute_rel_for(existing_field)
        ).disconnect(existing_field)

        self._generate_study_field_audit_node(
            study_root_node=study_root,
            study_field_node_after=None,
            study_field_node_before=existing_field,
            change_status=None,
            author_id=self.audit_info.author_id,
            date=datetime.now(timezone.utc),
        )

    @staticmethod
    def _validate_boolean_value(parameter_value: Any) -> bool:
        """Validate and coerce a value for a StudyBooleanField."""
        if isinstance(parameter_value, bool):
            return parameter_value
        if isinstance(parameter_value, str):
            normalised = parameter_value.strip().lower()
            exceptions.ValidationException.raise_if(
                normalised not in {"true", "false"},
                msg=(
                    f"Boolean Other Study Attribute requires a boolean value, "
                    f"got '{parameter_value}'."
                ),
            )
            return normalised == "true"
        raise exceptions.ValidationException(
            msg=f"Boolean Other Study Attribute requires a boolean value, got '{parameter_value}'."
        )

    @staticmethod
    def _validate_time_value(parameter_value: Any) -> str:
        """Validate that a value is a valid ISO 8601 date/datetime/time string."""
        exceptions.ValidationException.raise_if(
            not isinstance(parameter_value, str),
            msg=(
                f"Date/DateTime/Time Other Study Attribute requires an ISO 8601 string, "
                f"got '{parameter_value}'."
            ),
        )
        for parser in (
            datetime.fromisoformat,
            date_type.fromisoformat,
            time.fromisoformat,
        ):
            try:
                parser(parameter_value)
                return parameter_value
            except ValueError, TypeError:
                continue
        raise exceptions.ValidationException(
            msg=(
                f"Date/DateTime/Time Other Study Attribute requires a valid "
                f"ISO 8601 value (e.g. '2024-01-15', '2024-01-15T10:30:00', '10:30:00'), "
                f"got '{parameter_value}'."
            ),
        )

    @staticmethod
    def _validate_text_value(parameter_value: Any) -> str:
        """Validate and coerce a value for a StudyTextField."""
        if isinstance(parameter_value, bool):
            raise exceptions.ValidationException(
                msg=f"Text Other Study Attribute requires a string value, got boolean '{parameter_value}'."
            )
        return str(parameter_value)

    @staticmethod
    def _create_other_attribute_field(
        field_class: type[StudyField],
        meta_study_field: MetaStudyField,
        parameter_value: str | bool | None,
        field_name: str,
    ) -> StudyField:
        """Persist a new StudyField of the resolved subtype, validating and
        coercing the input value based on the field class.

        *field_name* is the CTTermNameValue name for this TS parameter,
        used to uniquely identify the field among others sharing the
        same MetaStudyField (e.g. all Boolean Other Study Attributes).
        """
        value: Any = parameter_value
        if value is not None:
            if field_class is StudyBooleanField:
                value = StudyDefinitionRepositoryImpl._validate_boolean_value(value)
            elif field_class is StudyTimeField:
                value = StudyDefinitionRepositoryImpl._validate_time_value(value)
            elif field_class is StudyTextField:
                value = StudyDefinitionRepositoryImpl._validate_text_value(value)
        new_field = field_class(value=value, field_name=field_name).save()
        new_field.has_meta_study_field.connect(meta_study_field)
        return new_field

    @staticmethod
    def get_soa_preferences(
        study_uid: str,
        study_value_version: str | None = None,
        field_names: Sequence[str] | None = None,
    ) -> list[StudyBooleanField]:
        """Gets StudyBooleanField nodes related to SoA preferences"""

        if field_names is None:
            field_names = settings.study_soa_preferences_fields

        filters: dict[str, Any]

        if study_value_version:
            filters = {
                "has_boolean_field__has_version__uid": study_uid,
                "has_boolean_field__has_version|version": study_value_version,
            }
        else:
            filters = {
                "has_boolean_field__latest_value__uid": study_uid,
            }

        filters["field_name__in"] = field_names
        nodes = (
            StudyBooleanField.nodes.traverse(
                "has_after__audit_trail",
            )
            .filter(**filters)
            .resolve_subgraph()
        )
        return nodes

    def post_soa_preferences(
        self, study_uid: str, soa_preferences: StudySoaPreferencesInput
    ) -> list[StudyBooleanField]:
        """Creates StudyBooleanField nodes of SoA preferences if none are present"""

        exceptions.AlreadyExistsException.raise_if(
            self.get_soa_preferences(study_uid=study_uid),
            msg=f"SoA preferences already exist for Study with UID '{study_uid}'",
        )

        study_root = StudyRoot.nodes.get(uid=study_uid)
        latest_study_value = study_root.latest_value.single()

        for name, value in soa_preferences.model_dump(by_alias=True).items():
            field_sf = StudyBooleanField(field_name=name, value=value).save()
            latest_study_value.has_boolean_field.connect(field_sf)

            self._generate_study_field_audit_node(
                study_root_node=study_root,
                study_field_node_after=field_sf,
                study_field_node_before=None,
                change_status=None,
                author_id=self.audit_info.author_id,
                date=datetime.now(timezone.utc),
            )

        return self.get_soa_preferences(study_uid=study_uid)

    def edit_soa_preferences(
        self,
        study_uid: str,
        soa_preferences: StudySoaPreferencesInput,
    ) -> list[StudyBooleanField]:
        """Replaces StudyBooleanField nodes of SoA preferences for the supplied show_* parameters only"""

        # exclude_unset skips properties that were not provided on init, also won't use defaults
        prefs = soa_preferences.model_dump(by_alias=True, exclude_unset=True)

        study_root = StudyRoot.nodes.get(uid=study_uid)
        latest_study_value = study_root.latest_value.single()

        nodes = self.get_soa_preferences(
            study_uid=study_uid, field_names=tuple(prefs.keys())
        )

        # disconnect the previous version from StudyValue
        for node in nodes:
            latest_study_value.has_boolean_field.disconnect(node)

        _nodes = {node.field_name: node for node in nodes}

        for name, value in prefs.items():
            field_sf = StudyBooleanField(field_name=name, value=value).save()
            latest_study_value.has_boolean_field.connect(field_sf)

            self._generate_study_field_audit_node(
                study_root_node=study_root,
                study_field_node_after=field_sf,
                study_field_node_before=_nodes.get(name, None),
                change_status=None,
                author_id=self.audit_info.author_id,
                date=datetime.now(timezone.utc),
            )

        return self.get_soa_preferences(study_uid=study_uid)

    @staticmethod
    def get_soa_split_uids(
        study_uid: str,
        study_value_version: str | None = None,
        _field_name: str = settings.study_soa_split_uids_field,
    ) -> StudyArrayField | None:
        """Gets a StudyArrayField node as uids for SoA splitting"""

        if study_value_version:
            filters = {
                "has_array_field__has_version__uid": study_uid,
                "has_array_field__has_version|version": study_value_version,
                "has_array_field__has_version|status": StudyStatus.RELEASED.value,
            }
        else:
            filters = {
                "has_array_field__latest_value__uid": study_uid,
            }

        filters["field_name"] = _field_name

        try:
            return (
                StudyArrayField.nodes.traverse("has_after__audit_trail")
                .filter(**filters)
                .get()[0]
            )
        except DoesNotExist:
            return None

    def add_soa_split_uid(
        self,
        study_uid: str,
        uid: str,
        _field_name: str = settings.study_soa_split_uids_field,
    ) -> StudyArrayField:
        """Adds a UID to the StudyArrayField node for SoA splitting"""

        study_root: StudyRoot
        latest_study_value: StudyValue

        # Lock study in db
        acquire_write_lock_study_value(study_uid)

        # Fetch previous StudyArrayField
        try:
            previous_study_array_field = self.get_soa_split_uids(
                study_uid=study_uid, _field_name=_field_name
            )
        except exceptions.NotFoundException:
            previous_study_array_field = None

        # Check if uid is already in the array
        exceptions.AlreadyExistsException.raise_if(
            previous_study_array_field and uid in previous_study_array_field.value,  # type: ignore[operator]
            msg=f"StudyVisit '{uid}' is already present in SoA split UIDs for Study '{study_uid}'.",
        )

        # Get all StudyVisits ordered: we need to know which is the first member of a StudyVisitGroup
        all_visits_q = (
            StudyVisit.nodes.traverse(
                Path("in_visit_group", optional=True, include_rels_in_return=False)
            )
            .filter(has_study_visit__latest_value__uid=study_uid)
            .order_by("visit_number")
        )

        # Determine eligibility
        seen_uids = set()
        eligible_uids = set()
        _seen_group_uids = set()

        for (
            study_visit,
            study_visit_group,
            latest_study_value,
            _,
            study_root,
            _,
        ) in all_visits_q.all():
            seen_uids.add(study_visit.uid)
            if study_visit_group:
                if study_visit_group.uid in _seen_group_uids:
                    continue
                _seen_group_uids.add(study_visit_group.uid)
            eligible_uids.add(study_visit.uid)

        # Validate StudyVisit uid
        exceptions.NotFoundException.raise_if_not(uid in seen_uids, "StudyVisit", uid)

        # Validate eligibility of StudyVisit uid
        exceptions.BusinessLogicException.raise_if_not(
            uid in eligible_uids,
            msg=f"StudyVisit '{uid}' is not eligible to split SoA of Study '{study_uid}'.",
        )

        # Disconnect previous StudyArrayField
        if previous_study_array_field:
            latest_study_value.has_array_field.disconnect(previous_study_array_field)

        # Create new StudyArrayField with the uid added
        uids: set[str] = set()
        if previous_study_array_field:
            uids = set(previous_study_array_field.value)  # type: ignore[call-overload]
        uids |= {uid}
        new_study_array_field = StudyArrayField(
            field_name=_field_name, value=list(uids)
        ).save()
        latest_study_value.has_array_field.connect(new_study_array_field)

        # Extend audit trail
        self._generate_study_field_audit_node(
            study_root_node=study_root,
            study_field_node_after=new_study_array_field,
            study_field_node_before=previous_study_array_field,
            change_status=None,
            author_id=self.audit_info.author_id,
            date=datetime.now(timezone.utc),
        )

        return new_study_array_field

    def remove_soa_split_uid(
        self,
        study_uid: str,
        uid: str,
        _field_name: str = settings.study_soa_split_uids_field,
    ) -> StudyArrayField | None:
        """Removes a UID from the StudyArrayField node for SoA splitting"""

        study_root: StudyRoot
        latest_study_value: StudyValue

        # Lock study in db
        acquire_write_lock_study_value(study_uid)

        # Fetch previous StudyArrayField
        previous_study_array_field = self.get_soa_split_uids(
            study_uid=study_uid, _field_name=_field_name
        )

        # Check if uid is in the array
        exceptions.NotFoundException.raise_if_not(
            previous_study_array_field is not None
            and uid in previous_study_array_field.value,  # type: ignore[operator]
            msg=f"StudyVisit '{uid}' is not in SoA split UIDs for Study '{study_uid}'.",
        )

        # Disconnect previous StudyArrayField
        study_root, latest_study_value, _ = StudyRoot.nodes.traverse(
            "latest_value"
        ).get(uid=study_uid)
        latest_study_value.has_array_field.disconnect(previous_study_array_field)

        # Create new StudyArrayField if uids remain after removal
        if new_uids := list(set(previous_study_array_field.value) - {uid}):  # type: ignore[arg-type]
            new_study_array_field = StudyArrayField(
                field_name=_field_name, value=new_uids
            ).save()
            latest_study_value.has_array_field.connect(new_study_array_field)
        else:
            new_study_array_field = None

        # Extend audit trail
        self._generate_study_field_audit_node(
            study_root_node=study_root,
            study_field_node_after=new_study_array_field,
            study_field_node_before=previous_study_array_field,
            change_status=None,
            author_id=self.audit_info.author_id,
            date=datetime.now(timezone.utc),
        )

        return new_study_array_field

    def remove_soa_splits(
        self,
        study_uid: str,
        _field_name: str = settings.study_soa_split_uids_field,
    ) -> None:
        """Removes the StudyArrayField nodes for SoA splitting"""

        # Query StudyArrayFields
        filters = {
            "has_array_field__latest_value__uid": study_uid,
            "field_name": _field_name,
        }

        node: StudyArrayField
        for node, _, _, study_root, _, study_value, *_ in (
            StudyArrayField.nodes.traverse("has_after__audit_trail")
            .filter(**filters)
            .all()
        ):
            # Disconnect StudyArrayFields
            study_value.has_array_field.disconnect(node)

            # Extend audit trail
            self._generate_study_field_audit_node(
                study_root_node=study_root,
                study_field_node_before=node,
                study_field_node_after=None,
                change_status=None,
                author_id=self.audit_info.author_id,
                date=datetime.now(timezone.utc),
            )
