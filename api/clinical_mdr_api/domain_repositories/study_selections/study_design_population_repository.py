"""Repository for study design populations."""

import logging
from typing import Any

from neomodel import db

from clinical_mdr_api import utils
from clinical_mdr_api.domain_repositories._utils.helpers import (
    acquire_write_lock_study_value,
)
from clinical_mdr_api.domain_repositories.generic_repository import (
    _manage_versioning_with_relations,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
)
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyDesignPopulation as StudyDesignPopulationNeomodel,
)
from clinical_mdr_api.domains.study_selections.study_design_population import (
    StudyDesignPopulationHistoryVO,
    StudyDesignPopulationVO,
)
from common import exceptions

log = logging.getLogger(__name__)


class StudyDesignPopulationRepository:
    """
    Repository responsible for persisting and restoring StudyDesignPopulation
    study selections (as ``StudyDesignPopulationVO``) via the
    ``HAS_STUDY_DESIGN_POPULATION`` relationship, following the standard OSB
    study-selection versioning model (see ``_manage_versioning_with_relations``).
    """

    def __init__(self, author_id: str | None = None):
        self.author_id = author_id

    def find_all_by_study(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> list[StudyDesignPopulationVO]:
        """
        Return the list of ``StudyDesignPopulationVO`` for every
        StudyDesignPopulation that belongs to the given study, ordered by
        ``order``.

        When *study_value_version* is provided the query targets the matching
        released/locked snapshot (``HAS_VERSION`` relationship, matched only on
        ``version`` so that LOCKED study snapshots can be retrieved too);
        otherwise it targets the current draft (``LATEST`` relationship).
        """
        if study_value_version:
            query = """
                MATCH (sr:StudyRoot {uid: $study_uid})
                    -[:HAS_VERSION {version: $study_value_version}]
                    ->(sv:StudyValue)
                    -[:HAS_STUDY_DESIGN_POPULATION]
                    ->(sdp:StudyDesignPopulation)
                MATCH (sdp)<-[:AFTER]-(sa:StudyAction)
                RETURN DISTINCT
                    sdp.uid              AS uid,
                    sdp.group_id         AS group_id,
                    sdp.name             AS name,
                    sdp.definition       AS definition,
                    sdp.notes            AS notes,
                    sdp.order            AS order,
                    sdp.accepted_version AS accepted_version,
                    sa.date              AS start_date,
                    sa.author_id         AS author_id
                ORDER BY sdp.order
            """
            params: dict[str, Any] = {
                "study_uid": study_uid,
                "study_value_version": study_value_version,
            }
        else:
            query = """
                MATCH (sr:StudyRoot {uid: $study_uid})
                    -[:LATEST]
                    ->(sv:StudyValue)
                    -[:HAS_STUDY_DESIGN_POPULATION]
                    ->(sdp:StudyDesignPopulation)
                MATCH (sdp)<-[:AFTER]-(sa:StudyAction)
                RETURN
                    sdp.uid              AS uid,
                    sdp.group_id         AS group_id,
                    sdp.name             AS name,
                    sdp.definition       AS definition,
                    sdp.notes            AS notes,
                    sdp.order            AS order,
                    sdp.accepted_version AS accepted_version,
                    sa.date              AS start_date,
                    sa.author_id         AS author_id
                ORDER BY sdp.order
            """
            params = {"study_uid": study_uid}

        result, _ = db.cypher_query(query, params)
        rows = utils.db_result_to_list((result, _))
        return [self._row_to_vo(row, study_uid=study_uid) for row in rows]

    @staticmethod
    def _row_to_vo(row: dict[str, Any], study_uid: str) -> StudyDesignPopulationVO:
        return StudyDesignPopulationVO(
            uid=row["uid"],
            study_uid=study_uid,
            group_id=row["group_id"],
            name=row["name"],
            definition=row["definition"],
            notes=row["notes"],
            order=row["order"],
            author_id=row["author_id"],
            start_date=row["start_date"],
            accepted_version=bool(row.get("accepted_version")),
        )

    @staticmethod
    def _row_to_history_vo(
        row: dict[str, Any], study_uid: str
    ) -> StudyDesignPopulationHistoryVO:
        return StudyDesignPopulationHistoryVO(
            uid=row["uid"],
            study_uid=study_uid,
            group_id=row["group_id"],
            name=row["name"],
            definition=row["definition"],
            notes=row["notes"],
            order=row["order"],
            author_id=row["author_id"],
            start_date=row["start_date"],
            change_type=row["change_type"],
            status=row.get("status"),
            end_date=row.get("end_date"),
        )

    def find_by_uid(
        self,
        study_uid: str,
        population_uid: str,
        study_value_version: str | None = None,
    ) -> StudyDesignPopulationVO | None:
        """
        Direct single-node lookup of a StudyDesignPopulation with the given
        uid within the study, returned as a ``StudyDesignPopulationVO``, or
        ``None`` if not found.

        When *study_value_version* is provided the query targets the matching
        released/locked snapshot (``HAS_VERSION`` relationship, matched only on
        ``version`` so that LOCKED study snapshots can be retrieved too);
        otherwise it targets the current draft (``LATEST`` relationship).
        """
        if study_value_version:
            query = """
                MATCH (sr:StudyRoot {uid: $study_uid})
                    -[:HAS_VERSION {version: $study_value_version}]
                    ->(sv:StudyValue)
                    -[:HAS_STUDY_DESIGN_POPULATION]
                    ->(sdp:StudyDesignPopulation {uid: $population_uid})
                MATCH (sdp)<-[:AFTER]-(sa:StudyAction)
                RETURN
                    sdp.uid              AS uid,
                    sdp.group_id         AS group_id,
                    sdp.name             AS name,
                    sdp.definition       AS definition,
                    sdp.notes            AS notes,
                    sdp.order            AS order,
                    sdp.accepted_version AS accepted_version,
                    sa.date              AS start_date,
                    sa.author_id         AS author_id
            """
            params: dict[str, Any] = {
                "study_uid": study_uid,
                "population_uid": population_uid,
                "study_value_version": study_value_version,
            }
        else:
            query = """
                MATCH (sr:StudyRoot {uid: $study_uid})
                    -[:LATEST]
                    ->(sv:StudyValue)
                    -[:HAS_STUDY_DESIGN_POPULATION]
                    ->(sdp:StudyDesignPopulation {uid: $population_uid})
                MATCH (sdp)<-[:AFTER]-(sa:StudyAction)
                RETURN
                    sdp.uid              AS uid,
                    sdp.group_id         AS group_id,
                    sdp.name             AS name,
                    sdp.definition       AS definition,
                    sdp.notes            AS notes,
                    sdp.order            AS order,
                    sdp.accepted_version AS accepted_version,
                    sa.date              AS start_date,
                    sa.author_id         AS author_id
            """
            params = {"study_uid": study_uid, "population_uid": population_uid}

        result, _ = db.cypher_query(query, params)
        rows = utils.db_result_to_list((result, _))

        if not rows:
            log.warning(
                "StudyDesignPopulation with uid=%s not found for study_uid=%s",
                population_uid,
                study_uid,
            )
            return None

        return self._row_to_vo(rows[0], study_uid=study_uid)

    def get_all_audit_trail(
        self,
        study_uid: str,
        population_uid: str,
    ) -> list[StudyDesignPopulationHistoryVO]:
        query = """
            MATCH (sr:StudyRoot {uid: $study_uid})
                -[:AUDIT_TRAIL]->(action:StudyAction)
                -[:AFTER]->(after:StudyDesignPopulation)
            WHERE after.uid = $population_uid
                OR (after)-[:AFTER|BEFORE*1..]-(:StudyDesignPopulation {uid: $population_uid})
            OPTIONAL MATCH (after)<-[:BEFORE]-(end_action:StudyAction)
            RETURN
                after.uid        AS uid,
                after.group_id   AS group_id,
                after.name       AS name,
                after.definition AS definition,
                after.notes      AS notes,
                after.order      AS order,
                head([lbl IN labels(action) WHERE lbl IN ['Create', 'Edit', 'Delete']]) AS change_type,
                action.date      AS start_date,
                action.status    AS status,
                action.author_id AS author_id,
                end_action.date  AS end_date
            ORDER BY action.date DESC
        """
        params: dict[str, Any] = {
            "study_uid": study_uid,
            "population_uid": population_uid,
        }
        result, _ = db.cypher_query(query, params)
        rows = utils.db_result_to_list((result, _))
        return [self._row_to_history_vo(row, study_uid=study_uid) for row in rows]

    def get_all_audit_trail_for_study(
        self,
        study_uid: str,
    ) -> list[StudyDesignPopulationHistoryVO]:
        query = """
            MATCH (sr:StudyRoot {uid: $study_uid})
                -[:AUDIT_TRAIL]->(action:StudyAction)
                -[:AFTER]->(after:StudyDesignPopulation)
            OPTIONAL MATCH (after)<-[:BEFORE]-(end_action:StudyAction)
            RETURN
                after.uid        AS uid,
                after.group_id   AS group_id,
                after.name       AS name,
                after.definition AS definition,
                after.notes      AS notes,
                after.order      AS order,
                head([lbl IN labels(action) WHERE lbl IN ['Create', 'Edit', 'Delete']]) AS change_type,
                action.date      AS start_date,
                action.status    AS status,
                action.author_id AS author_id,
                end_action.date  AS end_date
            ORDER BY after.uid, action.date DESC
        """
        params: dict[str, Any] = {"study_uid": study_uid}
        result, _ = db.cypher_query(query, params)
        rows = utils.db_result_to_list((result, _))
        return [self._row_to_history_vo(row, study_uid=study_uid) for row in rows]

    def save(
        self,
        population: StudyDesignPopulationVO,
        delete_flag: bool = False,
    ) -> StudyDesignPopulationVO | None:
        """
        Persist a StudyDesignPopulationVO, following the standard OSB
        create/edit/delete before/after versioning model.

        * ``population.uid is None`` -> creates a new StudyDesignPopulation.
        * ``population.uid`` set and ``delete_flag`` False -> edits it.
        * ``population.uid`` set and ``delete_flag`` True -> soft-deletes it
          (a "tombstone" version is created and disconnected from StudyValue).
        """
        if population.uid is not None:
            if delete_flag:
                self._update(population, create=False, delete=True)
                return None
            return self._update(population, create=False)
        return self._update(population, create=True)

    def _update(
        self,
        item: StudyDesignPopulationVO,
        create: bool = False,
        delete: bool = False,
    ) -> StudyDesignPopulationVO:
        acquire_write_lock_study_value(item.study_uid)

        study_root: StudyRoot = StudyRoot.nodes.get_or_none(uid=item.study_uid)
        exceptions.NotFoundException.raise_if_not(
            study_root,
            "Study",
            item.study_uid,
        )

        study_value: StudyValue = study_root.latest_value.get_or_none()
        exceptions.ValidationException.raise_if(
            study_value is None, msg="Study doesn't have draft version."
        )

        new_node = StudyDesignPopulationNeomodel(
            accepted_version=item.accepted_version,
            order=item.order,
            group_id=item.group_id,
            name=item.name,
            definition=item.definition,
            notes=item.notes,
        )
        if item.uid is not None:
            new_node.uid = item.uid
        new_node.save()
        if item.uid is None:
            item.uid = new_node.uid

        if create:
            log.info(
                "Creating StudyDesignPopulation uid=%s for study_uid=%s",
                item.uid,
                item.study_uid,
            )
            _manage_versioning_with_relations(
                study_root=study_root,
                action_type=Create,
                before=None,
                after=new_node,
                author_id=self.author_id,
            )
            study_value.has_study_design_population.connect(new_node)
        else:
            previous_item = study_value.has_study_design_population.get_or_none(
                uid=item.uid
            )
            exceptions.NotFoundException.raise_if_not(
                previous_item,
                "StudyDesignPopulation",
                item.uid,
            )
            if not delete:
                log.info(
                    "Updating StudyDesignPopulation uid=%s for study_uid=%s",
                    item.uid,
                    item.study_uid,
                )
                _manage_versioning_with_relations(
                    study_root=study_root,
                    action_type=Edit,
                    before=previous_item,
                    after=new_node,
                    author_id=self.author_id,
                )
                study_value.has_study_design_population.connect(new_node)
            else:
                log.info(
                    "Deleting StudyDesignPopulation uid=%s for study_uid=%s",
                    item.uid,
                    item.study_uid,
                )
                _manage_versioning_with_relations(
                    study_root=study_root,
                    action_type=Delete,
                    before=previous_item,
                    after=new_node,
                    author_id=self.author_id,
                )

        return item
