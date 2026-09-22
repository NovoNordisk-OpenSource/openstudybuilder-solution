import datetime
from dataclasses import dataclass

from neomodel import db

from clinical_mdr_api.domain_repositories.generic_repository import (
    _manage_versioning_with_relations,
)
from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
)
from common.exceptions import NotFoundException
from common.telemetry import trace_calls


@dataclass
class SelectionHistory:
    """Class for selection history items"""

    study_selection_uid: str
    study_uid: str
    author_id: str
    change_type: str
    start_date: datetime.datetime
    end_date: datetime.datetime | None


class StudySelectionRepository:
    """
    Base class for study selection.

    We handle common operations here.
    """

    def _from_repository_values(self, study_uid: str, selection, selection_vo=None):
        """Must be defined by subclasses."""
        raise NotImplementedError

    def exclude_relationships(self):
        """Must be defined by subclasses."""
        raise NotImplementedError

    def perform_save(
        self,
        study_value_node: StudyValue,
        selection_vo,
        author_id: str,
    ):
        """Must be defined by subclasses."""
        raise NotImplementedError

    def save(self, selection_vo, author_id: str):
        # Single Cypher to fetch StudyRoot + latest StudyValue (replaces 2 neomodel lookups)
        results, _ = db.cypher_query(
            "MATCH (sr:StudyRoot {uid: $uid})-[:LATEST]->(sv:StudyValue) RETURN sr, sv",
            {"uid": selection_vo.study_uid},
            resolve_objects=True,
        )
        NotFoundException.raise_if(not results, "Study", selection_vo.study_uid)
        study_root_node, latest_study_value_node = results[0]

        new_selection = self.perform_save(
            latest_study_value_node, selection_vo, author_id
        )
        # Update audit trail
        if selection_vo.uid is not None:
            selection = self.get_study_selection(
                latest_study_value_node, selection_vo.uid
            )
            _manage_versioning_with_relations(
                study_root=study_root_node,
                action_type=Edit,
                before=selection,
                after=new_selection,
                exclude_relationships=self.exclude_relationships(),
                author_id=author_id,
            )
        else:
            _manage_versioning_with_relations(
                study_root=study_root_node,
                action_type=Create,
                before=None,
                after=new_selection,
                author_id=author_id,
            )

        return self._from_repository_values(
            selection_vo.study_uid, new_selection, selection_vo=selection_vo
        )

    def get_study_selection(self, study_value_node: StudyValue, selection_uid: str):
        """Must be defined by subclasses."""
        raise NotImplementedError

    @trace_calls(args=[1, 2], kwargs=["study_uid", "selection_uid"])
    def delete(self, study_uid: str, selection_uid: str, author_id: str) -> None:
        # Single Cypher to fetch StudyRoot + latest StudyValue (replaces 2 neomodel lookups)
        results, _ = db.cypher_query(
            "MATCH (sr:StudyRoot {uid: $uid})-[:LATEST]->(sv:StudyValue) RETURN sr, sv",
            {"uid": study_uid},
            resolve_objects=True,
        )
        NotFoundException.raise_if(not results, "Study", study_uid)
        study_root_node, latest_study_value_node = results[0]

        selection = self.get_study_selection(latest_study_value_node, selection_uid)
        selection_vo = self._from_repository_values(study_uid, selection)
        new_selection = self.perform_save(
            latest_study_value_node, selection_vo, author_id
        )
        # Audit trail — _manage_versioning_with_relations also disconnects `selection`
        # from the StudyValue, so we only need to disconnect `new_selection` here.
        _manage_versioning_with_relations(
            study_root=study_root_node,
            action_type=Delete,
            before=selection,
            after=new_selection,
            exclude_relationships=self.exclude_relationships(),
            author_id=author_id,
        )
        new_selection.study_value.disconnect(latest_study_value_node)

    def _get_selection_with_history(
        self, study_uid: str, selection_uid: str | None = None
    ):
        """Must be defined by subclasses."""
        raise NotImplementedError

    def find_selection_history(self, study_uid: str, selection_uid: str | None = None):
        kwargs = {}
        if selection_uid:
            kwargs["selection_uid"] = selection_uid
        return self._get_selection_with_history(study_uid=study_uid, **kwargs)
