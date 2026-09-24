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
from clinical_mdr_api.domain_repositories.models.study_audit_trail import Create, Edit
from clinical_mdr_api.domain_repositories.models.study_selections import StudyVersion
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.repositories._utils import calculate_total_count_from_query_result
from clinical_mdr_api.services._utils import ensure_transaction
from common.auth.user import user
from common.config import settings
from common.utils import (
    db_pagination_clause,
    get_db_result_as_dict,
    validate_page_number_and_page_size,
)


class StudyVersionRepository:
    """
    Repository for managing StudyVersion nodes.
    """

    def __init__(self):
        self.author_id = user().id()

    @staticmethod
    def _study_value_query(
        study_uid: str, version: str | None = None
    ) -> tuple[str, dict[str, str | None]]:
        params = {
            "study_uid": study_uid,
        }
        if version:
            params["version"] = version
            params["study_status"] = StudyStatus.RELEASED.value
            query = "MATCH (study_root:StudyRoot {uid: $study_uid})-[:HAS_VERSION{status:'RELEASED',version:$version}]->(study_value:StudyValue)"
        else:
            query = "MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)"

        return query, params

    @ensure_transaction(db)
    def create_or_update_study_version(
        self,
        study_uid: str,
        version: str | None = None,
        other_reason_for_unlocking: str | None = None,
        other_reason_for_locking: str | None = None,
        reason_for_lock_term_uid: str | None = None,
        reason_for_unlock_term_uid: str | None = None,
        release: bool = False,
    ) -> StudyVersion:
        """
        This method follows the following pattern to create StudyVersion nodes:
        - First release/lock: Creates a new StudyVersion node with Create audit action
        - Subsequent releases/locks: Updates the existing StudyVersion node with Edit audit action

        Args:
            study_uid: UID of the Study
            version: Version string for the StudyVersion (required when locking/releasing, optional when unlocking)
            other_reason_for_unlocking: Other reason for unlocking the StudyVersion
            other_reason_for_locking: Other reason for locking the StudyVersion
            reason_for_lock_term_uid: UID of CTTerm from "Reason For Lock" codelist
            reason_for_unlock_term_uid: UID of CTTerm from "Reason For Unlock" codelist
        Returns:
            The created or updated StudyVersion node
        """

        acquire_write_lock_study_value(study_uid)

        query, params = self._study_value_query(study_uid, version)

        query += """
        OPTIONAL MATCH (study_root)--(:StudyValue)-[:HAS_STUDY_VERSION]->(existing_sv:StudyVersion)
        WHERE NOT (existing_sv)-[:BEFORE]-(:StudyAction)
        RETURN study_root, existing_sv
        """

        result, _ = db.cypher_query(query, params, resolve_objects=True)

        if not result or not result[0]:
            raise ValueError(f"Study with UID {study_uid} not found")

        study_root = result[0][0]
        existing_version = result[0][1] if len(result[0]) > 1 else None
        if existing_version:
            before_node = existing_version
            update_query, params = self._study_value_query(study_uid, version)
            # When Unlock we want to take other_reason_for_unlocking as it was get from unlock request
            # for other actions we want to keep other_reason_for_unlocking as it was before, so we take it from before_node
            if not reason_for_unlock_term_uid:
                other_reason_for_unlocking = before_node.other_reason_for_unlocking
            params.update(
                {
                    "study_version_uid": before_node.uid,
                    "other_reason_for_locking": other_reason_for_locking,
                    "other_reason_for_unlocking": other_reason_for_unlocking,
                }
            )
            update_query += """
            CREATE (new_sv:StudyVersion:StudySelection {uid: $study_version_uid, other_reason_for_locking: $other_reason_for_locking, other_reason_for_unlocking: $other_reason_for_unlocking})
            WITH new_sv, study_value
            OPTIONAL MATCH (old_sv:StudyVersion {uid: $study_version_uid})<-[old_rel:HAS_STUDY_VERSION]-(study_value)
            WHERE NOT (old_sv)-[:BEFORE]-(:StudyAction)
            DELETE old_rel
            CREATE (study_value)-[:HAS_STUDY_VERSION]->(new_sv)
            RETURN new_sv
            """
            result, _ = db.cypher_query(
                update_query,
                params,
                resolve_objects=True,
            )
            after_node = result[0][0] if result and result[0] else None
            if not after_node:
                raise ValueError(
                    f"Failed to create new StudyVersion with uid: {before_node.uid}"
                )

            self._connect_reason_relationships(
                after_node,
                reason_for_lock_term_uid=reason_for_lock_term_uid,
                reason_for_unlock_term_uid=reason_for_unlock_term_uid,
            )
            exclude_relationships = (
                [StudyVersion.has_reason_for_lock]
                if reason_for_lock_term_uid
                else [
                    StudyVersion.has_reason_for_lock,
                    StudyVersion.has_reason_for_unlock,
                ]
            )
            _manage_versioning_with_relations(
                study_root=study_root,
                action_type=Edit,
                before=before_node,
                after=after_node,
                author_id=self.author_id,
                exclude_relationships=exclude_relationships,
            )

            if release:
                before_node = after_node
                update_query = """
                MATCH (study_root:StudyRoot {uid: $study_uid})-[:LATEST]->(study_value:StudyValue)
                CREATE (new_sv:StudyVersion:StudySelection {uid: $study_version_uid, other_reason_for_unlocking: $other_reason_for_unlocking})
                WITH new_sv, study_value
                OPTIONAL MATCH (old_sv:StudyVersion {uid: $study_version_uid})<-[old_rel:HAS_STUDY_VERSION]-(study_value)
                WHERE NOT (old_sv)-[:BEFORE]-(:StudyAction)
                DELETE old_rel
                CREATE (study_value)-[:HAS_STUDY_VERSION]->(new_sv)
                RETURN new_sv
                """
                result, _ = db.cypher_query(
                    update_query,
                    {
                        "study_version_uid": before_node.uid,
                        "study_uid": study_uid,
                        "other_reason_for_unlocking": before_node.other_reason_for_unlocking,
                    },
                    resolve_objects=True,
                )
                after_node = result[0][0] if result and result[0] else None
                _manage_versioning_with_relations(
                    study_root=study_root,
                    action_type=Edit,
                    before=before_node,
                    after=after_node,
                    author_id=self.author_id,
                    # This is extra StudyVersion after just releasing a Study and we want to carry over HAS_REASON_FOR_UNLOCK that was passed when unlocking
                    exclude_relationships=[StudyVersion.has_reason_for_lock],
                )

            return after_node

        new_version = StudyVersion(
            version=version,
            other_reason_for_locking=other_reason_for_locking,
            other_reason_for_unlocking=other_reason_for_unlocking,
        ).save()

        connect_query, params = self._study_value_query(study_uid, version)
        params.update({"sv_uid": new_version.uid})
        connect_query += """
        MATCH (sv:StudyVersion {uid: $sv_uid})
        CREATE (study_value)-[:HAS_STUDY_VERSION]->(sv)
        """
        db.cypher_query(
            connect_query,
            params,
        )

        self._connect_reason_relationships(
            new_version,
            reason_for_lock_term_uid=reason_for_lock_term_uid,
            reason_for_unlock_term_uid=reason_for_unlock_term_uid,
        )

        _manage_versioning_with_relations(
            study_root=study_root,
            action_type=Create,
            after=new_version,
            author_id=self.author_id,
        )

        return new_version

    @ensure_transaction(db)
    def _connect_reason_relationships(
        self,
        study_version: StudyVersion,
        reason_for_lock_term_uid: str | None,
        reason_for_unlock_term_uid: str | None,
    ) -> None:
        """
        Helper method to connect reason relationships to StudyVersion.
        Uses get_or_create_selected_term to create CTTermContext nodes if needed.

        Args:
            study_version: The StudyVersion node to connect relationships to
            reason_for_lock_term_uid: UID of CTTerm from "Reason For Lock" codelist
            reason_for_unlock_term_uid: UID of CTTerm from "Reason For Unlock" codelist
        """
        ct_repo = CTCodelistAttributesRepository()

        if reason_for_lock_term_uid:
            term_node = CTTermRoot.nodes.get_or_none(uid=reason_for_lock_term_uid)
            if term_node is None:
                raise ValueError(
                    f"Lock CTTerm with UID '{reason_for_lock_term_uid}' not found"
                )

            ct_context = ct_repo.get_or_create_selected_term(
                term_node,
                codelist_submission_value=settings.reason_for_lock_cl_submval,
            )
            study_version.has_reason_for_lock.connect(ct_context)

        if reason_for_unlock_term_uid:
            term_node = CTTermRoot.nodes.get_or_none(uid=reason_for_unlock_term_uid)
            if term_node is None:
                raise ValueError(
                    f"Unlock CTTerm with UID '{reason_for_unlock_term_uid}' not found"
                )

            ct_context = ct_repo.get_or_create_selected_term(
                term_node,
                codelist_submission_value=settings.reason_for_unlock_cl_submval,
            )
            study_version.has_reason_for_unlock.connect(ct_context)

    def retrieve_study_snapshot_history(
        self,
        study_uid: str,
        page_size: int = 10,
        page_number: int = 1,
        total_count: bool = True,
        only_latest_major_protocol_version: bool = False,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Retrieves the complete snapshot history of a Study, including all versioned states.

        This method queries the graph database to collect information about all study versions
        (locked, released, etc.) associated with a given Study.
        The query filters out deleted versions and excludes DRAFT versions except for the
        latest draft if the Study is currently in DRAFT status.
        """

        validate_page_number_and_page_size(page_number, page_size)
        match_query = """
        MATCH (study_root:StudyRoot {uid: $study_uid})-[hv:HAS_VERSION]->(study_value:StudyValue)

        WITH *, head([(study_root)-[latest_draft:LATEST_DRAFT]->(study_value) | latest_draft]) AS latest_draft
        WHERE NOT EXISTS((study_value)<-[:BEFORE]-(:Delete)) AND
        // Filter out all DRAFT versions except the latest one if Study is currently in DRAFT status
        (hv.status <> 'DRAFT' OR (latest_draft IS NOT NULL AND latest_draft.end_date IS NULL))
    
        WITH study_value, collect(hv) as all_versions, max(coalesce(hv.end_date, hv.start_date)) as max_date
    
        WITH study_value, all_versions, max_date,
        head([v IN all_versions WHERE coalesce(v.end_date, v.start_date) = max_date]) as latest_version

        WITH study_value, max_date, latest_version, apoc.coll.sort([v IN all_versions | v.status]) as all_statuses
    
        OPTIONAL MATCH (user:User)
        WHERE user.user_id = latest_version.author_id
        WITH study_value, latest_version, max_date as date, all_statuses as statuses, coalesce(user.username, latest_version.author_id) as modified_by

        OPTIONAL MATCH (study_value)-[:HAS_STUDY_VERSION]->(sv:StudyVersion)
        OPTIONAL MATCH (sv)-[:HAS_REASON_FOR_LOCK]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-->(:CTTermNameRoot)-[:LATEST_FINAL]->(lock_term_val:CTTermNameValue)
        OPTIONAL MATCH (sv)-[:HAS_REASON_FOR_UNLOCK]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-->(:CTTermNameRoot)-[:LATEST_FINAL]->(unlock_term_val:CTTermNameValue)
        """
        protocol_header_version_match = f"{'' if only_latest_major_protocol_version else 'OPTIONAL'} MATCH (study_value)-[:HAS_STUDY_DEFINITION_DOCUMENT]->(sdd:StudyDefinitionDocument)"

        return_query = """
        RETURN
            lock_term_val.name as reason_for_lock,
            unlock_term_val.name as reason_for_unlock,
            latest_version.version as metadata_version,
            latest_version.change_description AS description,
            sv.other_reason_for_unlocking AS other_reason_for_unlocking,
            sv.other_reason_for_locking AS other_reason_for_lock_release,
            sdd.protocol_header_major_version AS protocol_header_major_version,
            sdd.protocol_header_minor_version AS protocol_header_minor_version,
            date, statuses, modified_by
        // If there is Draft version, return it first, then order by metadata_version descending
        ORDER BY 
            CASE WHEN statuses=["DRAFT"] THEN 0 ELSE 1 END, 
            toInteger(split(metadata_version,'.')[0]) DESC,
            // Applying coealesce(..) to handle cases where minor_version is null, for instance version="1" 
            toInteger(coalesce(split(metadata_version,'.')[1], '0')) DESC
        """
        query = "\n".join(
            [
                match_query,
                protocol_header_version_match,
                return_query,
                # if only latest major protocol header version is requested, we do pagination in memory after filtering, as we can't do filtering in the query
                (
                    db_pagination_clause(page_size, page_number, one_element_extra=True)
                    if not only_latest_major_protocol_version
                    else ""
                ),
            ]
        )
        rows, columns = db.cypher_query(query, {"study_uid": study_uid})
        if not rows or not rows[0]:
            return [], 0

        history = [get_db_result_as_dict(row, columns) for row in rows]
        # If only_latest_major_protocol_version is requested, we have to leave only
        # major protocol header versions and leave only latest available version of it (with highest metadata version)
        if only_latest_major_protocol_version:
            phv_to_index: dict[str, int] = {}
            filtered_history: list[dict[str, Any]] = []
            for h in history:
                major_version = h.get("protocol_header_major_version")
                minor_version = h.get("protocol_header_minor_version")
                if major_version is not None and minor_version == 0:
                    phv = f"{major_version}.{minor_version}"
                    if phv not in phv_to_index:
                        h["original_metadata_version"] = h.get("metadata_version")
                        phv_to_index[phv] = len(filtered_history)
                        filtered_history.append(h)
                    else:
                        filtered_history[phv_to_index[phv]][
                            "original_metadata_version"
                        ] = h.get("metadata_version")
            history = filtered_history

        if not only_latest_major_protocol_version:
            total = (
                calculate_total_count_from_query_result(
                    result_count=len(history),
                    page_size=page_size,
                    page_number=page_number,
                    total_count=total_count,
                    extra_requested=True,
                )
                if total_count
                else 0
            )
        else:
            # Handle pagination in memory not db as there was python post-processing
            total = len(history) if total_count else 0
            if page_size > 0:
                start_idx = (page_number - 1) * page_size
                end_idx = start_idx + page_size
                history = history[start_idx:end_idx]

        # Remove last extra_requested item if it was added
        if 0 < page_size < len(history):
            history = history[:page_size]
        return history, total
