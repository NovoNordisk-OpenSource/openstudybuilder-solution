from neomodel import db

from clinical_mdr_api.domain_repositories._utils.helpers import (
    acquire_write_lock_study_value,
)
from clinical_mdr_api.domain_repositories.generic_repository import (
    _manage_versioning_with_relations,
)
from clinical_mdr_api.domain_repositories.models.study_audit_trail import Create, Edit
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyDefinitionDocument,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyStatus,
)
from clinical_mdr_api.services._utils import ensure_transaction
from common.auth.user import user
from common.config import settings


class StudyDefinitionDocumentRepository:
    """
    Repository for managing StudyDefinitionDocument nodes.
    """

    def __init__(self):
        self.author_id = user().id()

    @staticmethod
    def _study_value_query(
        study_uid: str, version: str | None = None
    ) -> tuple[str, dict[str, str | int | None]]:
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
    def get_latest_protocol_header_version(
        self, study_uid: str, study_value_version: str | None = None
    ) -> str | None:
        params = {
            "study_uid": study_uid,
        }
        if not study_value_version:
            query = """
            MATCH (:StudyRoot{uid:$study_uid})-[:HAS_VERSION]->(:StudyValue)-[:HAS_STUDY_DEFINITION_DOCUMENT]->(latest_sdd:StudyDefinitionDocument)
            WHERE NOT (latest_sdd)-[:BEFORE]-(:StudyAction)
            RETURN latest_sdd
            """
        else:
            query = """
                MATCH (:StudyRoot {uid: $study_uid})-[:HAS_VERSION{status:'RELEASED',version:$version}]->(:StudyValue)
                    -[:HAS_STUDY_DEFINITION_DOCUMENT]->(study_definition_document:StudyDefinitionDocument)
                RETURN study_definition_document
            """
            params["version"] = study_value_version
        result, _ = db.cypher_query(query, params=params, resolve_objects=True)

        if not result or not result[0]:
            return None

        study_definition_document = result[0][0]
        return f"{study_definition_document.protocol_header_major_version}.{study_definition_document.protocol_header_minor_version}"

    def has_final_protocol_locked_version(
        self, study_uid: str, study_value_version: str | None = None
    ) -> bool:
        params: dict[str, str | int | None] = {
            "study_uid": study_uid,
            "final_protocol_submval": settings.final_protocol_term_submval,
        }
        if study_value_version:
            params["version"] = study_value_version
            query = "MATCH (:StudyRoot {uid: $study_uid})-[:HAS_VERSION{status:'LOCKED',version:$version}]->(:StudyValue)"
        else:
            query = "MATCH (:StudyRoot {uid: $study_uid})-[:HAS_VERSION{status:'LOCKED'}]->(:StudyValue)"
        query += """
            -[:HAS_STUDY_VERSION]->(sv:StudyVersion)
            -[:HAS_REASON_FOR_LOCK]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(term_root:CTTermRoot)
            <-[:HAS_TERM_ROOT]-(codelist_term:CTCodelistTerm)
        WHERE codelist_term.submission_value = $final_protocol_submval
        RETURN count(sv) > 0 AS has_final_protocol
        """
        result, _ = db.cypher_query(query, params=params)
        return bool(result and result[0] and result[0][0])

    @ensure_transaction(db)
    def create_or_update_study_definition_document(
        self,
        study_uid: str,
        protocol_header_major_version: int,
        protocol_header_minor_version: int,
        version: str | None = None,
    ) -> StudyDefinitionDocument:

        acquire_write_lock_study_value(study_uid)

        query, params = self._study_value_query(study_uid, version=version)

        query += """
        OPTIONAL MATCH (study_root)--(:StudyValue)-[:HAS_STUDY_DEFINITION_DOCUMENT]->(existing_sdd:StudyDefinitionDocument)
        WHERE NOT (existing_sdd)-[:BEFORE]-(:StudyAction)
        RETURN study_root, existing_sdd
        """

        result, _ = db.cypher_query(query, params, resolve_objects=True)

        if not result or not result[0]:
            raise ValueError(f"Study with UID {study_uid} not found")

        study_root = result[0][0]
        existing_study_definition_document = (
            result[0][1] if len(result[0]) > 1 else None
        )
        if existing_study_definition_document:
            before_node = existing_study_definition_document
            update_query, params = self._study_value_query(study_uid, version=version)
            params.update(
                {
                    "study_definition_document": before_node.uid,
                    "protocol_header_major_version": protocol_header_major_version,
                    "protocol_header_minor_version": protocol_header_minor_version,
                }
            )
            update_query += """
            CREATE (new_sdd:StudyDefinitionDocument:StudySelection {uid: $study_definition_document, protocol_header_major_version: $protocol_header_major_version, protocol_header_minor_version: $protocol_header_minor_version})
            WITH new_sdd, study_value
            OPTIONAL MATCH (old_sdd:StudyDefinitionDocument {uid: $study_definition_document})<-[old_rel:HAS_STUDY_DEFINITION_DOCUMENT]-(study_value)
            WHERE NOT (old_sdd)-[:BEFORE]-(:StudyAction)
            DELETE old_rel
            CREATE (study_value)-[:HAS_STUDY_DEFINITION_DOCUMENT]->(new_sdd)
            RETURN new_sdd
            """
            result, _ = db.cypher_query(
                update_query,
                params,
                resolve_objects=True,
            )
            after_node = result[0][0] if result and result[0] else None
            if not after_node:
                raise ValueError(
                    f"Failed to create new StudyDefinitionDocument with uid: {before_node.uid}"
                )

            _manage_versioning_with_relations(
                study_root=study_root,
                action_type=Edit,
                before=before_node,
                after=after_node,
                author_id=self.author_id,
            )

            return after_node

        new_version = StudyDefinitionDocument(
            protocol_header_major_version=protocol_header_major_version,
            protocol_header_minor_version=protocol_header_minor_version,
        ).save()

        connect_query, params = self._study_value_query(study_uid, version=version)
        params.update({"study_definition_document_uid": new_version.uid})
        connect_query += """
        MATCH (sdd:StudyDefinitionDocument {uid: $study_definition_document_uid})
        CREATE (study_value)-[:HAS_STUDY_DEFINITION_DOCUMENT]->(sdd)
        """
        db.cypher_query(
            connect_query,
            params,
        )
        _manage_versioning_with_relations(
            study_root=study_root,
            action_type=Create,
            after=new_version,
            author_id=self.author_id,
        )

        return new_version
