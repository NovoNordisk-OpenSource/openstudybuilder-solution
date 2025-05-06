import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Sequence

from neomodel.sync_.core import NodeMeta, db
from neomodel.sync_.match import Collect, NodeNameResolver, Optional, Size

from clinical_mdr_api.domain_repositories.generic_repository import (
    RepositoryClosureData,  # type: ignore
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_field import StudyBooleanField
from clinical_mdr_api.domains.study_definition_aggregates.root import (
    StudyDefinitionAR,
    StudyDefinitionSnapshot,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyFieldAuditTrailEntryAR,
)
from clinical_mdr_api.models.study_selections.study import (
    StudyPreferredTimeUnit,
    StudySoaPreferencesInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from common import exceptions


class StudyDefinitionRepository(ABC):
    """
    Abstract Study Repository. Abstract class meant to be a base for concrete study repository implementation.
    A class provides public repository methods for Study persistence and retrieval and implements all relevant
    Memento pattern interactions with the StudyDefinitionAR class for getting StudySnapshots for save and for
    StudyDefinitionAR creation from StudyDefinitionSnapshot retrieved from repository as well as tracking of
    StudyDefinitionAR instances declared as retrieved with intent of updating.

    Concrete repository implementation is expected to:
    * provide implementation for _retrieve_snapshot_by_uid, _save, _create and _retrieve_all_snapshots methods
    (see details in abstract method
        docstrings)
    * if necessary provide a constructor with some necessary initializations (possibly injecting some dependencies, e.g.
        some transaction manager object). It's assumed that every request served creates its own instance of this class.
        NOTE: if provided, subclass constructor is expected to call super().__init__(), to allow base class to init
        properly as well.
    * if necessary override a close lifecycle method to do some cleanup or finalization (and again if that's the case
        a super().close() also should be invoked).
    """

    @dataclass
    class _RepositoryAuditInfo:
        """
        A class to communicate additional information necessary for the repository, to retain proper audit info on
        modifications and creation of study instances.
        """

        author_id: str | None = None

    __retrieved_for_update: dict[str, StudyDefinitionAR]
    __audit_info: _RepositoryAuditInfo
    __closed: bool = False

    def __init__(self):
        self.__retrieved_for_update = {}
        self.__audit_info = self._RepositoryAuditInfo()

    def _check_not_closed(self) -> None:
        """
        Protected method used internally by the repository implementation to raise an error in case of
        attempt repository after it's been closed.
        """
        exceptions.BusinessLogicException.raise_if(
            self.__closed, msg="Cannot use repository after it's closed."
        )

    @property
    def audit_info(self) -> _RepositoryAuditInfo:
        """
        A property used to set and get information needed by the repository to retain proper audit trail on
        study updates and creation.

        :return: a reference to an object containing properties which should be set to retain a proper audit info
        """
        return self.__audit_info

    def find_by_uid(
        self,
        uid: str,
        for_update: bool = False,
        study_value_version: str | None = None,
    ) -> StudyDefinitionAR | None:
        """
        Public repository method for bringing an instance of study aggregate (StudyDefinitionAR class) restored from its
        state persisted in the underlying DB.

        :param uid: uid of the study to be retrieved
        :param for_update: True - informs the repository that an application intent is to change the state of this
            instance, which implies engaging means of assuring consistent update with regard to possible concurrency
            with other processing possibly changing the state of the same aggregate instance.
        :return: A restored instance of Study aggregate (StudyDefinitionAR class) or None (if instance given by uid does
         not exist in the underlying DB).
        """
        self._check_not_closed()

        # If we have it already in memory return the same one.
        # Note that means that (in above situation) we are going to return instance which already might have been
        # somehow processed
        # by the code outside repository and possibly modified. If that is the case the state of this instance
        # may be different that the state of underlying DB. This is done on purpose to avoid very difficult to debug
        # errors caused by the situation when actually in the service execution the same aggregate instance
        # (the same instance by mean of uid) is represented as two different in-memory instances and possibly updated
        # in different way and then saved. This may lead to some unpredictable result, so to avoid that we try to
        # guarantee that once some particular instance was retrieved for update (at least once) every subsequent
        # repository request to retrieve instance with the same uid returns exactly the same in-memory instance.
        result: StudyDefinitionAR | None = self.__retrieved_for_update.get(uid)
        if result is not None:
            return result

        # now get the data from db
        snapshot: StudyDefinitionSnapshot | None
        additional_closure: Any
        (snapshot, additional_closure) = self._retrieve_snapshot_by_uid(
            uid=uid,
            for_update=for_update,
            study_value_version=study_value_version,
        )

        # if no data, then no object
        if snapshot is None:
            return None
        # if exists then prepare our result
        result = StudyDefinitionAR.from_snapshot(snapshot)
        result.repository_closure_data = RepositoryClosureData(
            not_for_update=not for_update,
            additional_closure=additional_closure,
            repository=self,
        )

        # if retrieved for update then we should remember this instance
        if for_update:
            self.__retrieved_for_update[uid] = result

        # and that's it we are done
        return result

    def get_study_structure_overview(self):
        query = """
MATCH (sr:StudyRoot)-[:LATEST]->(sv:StudyValue)
WHERE sv.study_id_prefix IS NOT NULL AND sv.study_number IS NOT NULL
CALL {
    WITH sv
    OPTIONAL MATCH (sv)-[:HAS_STUDY_ARM]->(arm:StudyArm)
    OPTIONAL MATCH (sv)-[:HAS_STUDY_EPOCH]->(pre_treatment_epoch:StudyEpoch)-[:HAS_EPOCH_TYPE]->(:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]-(:CTTermAttributesRoot)-[:LATEST]-(:CTTermAttributesValue {code_submission_value: "PRE TREATMENT EPOCH TYPE"})
    OPTIONAL MATCH (sv)-[:HAS_STUDY_EPOCH]->(treatment_epoch:StudyEpoch)-[:HAS_EPOCH_TYPE]->(:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]-(:CTTermAttributesRoot)-[:LATEST]-(:CTTermAttributesValue {code_submission_value: "TREATMENT"})
    OPTIONAL MATCH (sv)-[:HAS_STUDY_EPOCH]->(no_treatment_epoch:StudyEpoch)-[:HAS_EPOCH_TYPE]->(:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]-(:CTTermAttributesRoot)-[:LATEST]-(:CTTermAttributesValue {code_submission_value: "NO TREATMENT EPOCH TYPE"})
    OPTIONAL MATCH (sv)-[:HAS_STUDY_EPOCH]->(post_treatment_epoch:StudyEpoch)-[:HAS_EPOCH_TYPE]->(:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]-(:CTTermAttributesRoot)-[:LATEST]-(:CTTermAttributesValue {code_submission_value: "POST TREATMENT EPOCH TYPE"})
    OPTIONAL MATCH (sv)-[:HAS_STUDY_ELEMENT]->(treatment_element:StudyElement)-[:HAS_ELEMENT_SUBTYPE]->(:CTTermRoot)-[:HAS_PARENT_TYPE]->(:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]-(:CTTermAttributesRoot)-[:LATEST]-(:CTTermAttributesValue {code_submission_value: "TREATMENT ELEMENT TYPE"})
    OPTIONAL MATCH (sv)-[:HAS_STUDY_ELEMENT]->(no_treatment_element:StudyElement)-[:HAS_ELEMENT_SUBTYPE]->(:CTTermRoot)-[:HAS_PARENT_TYPE]->(:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]-(:CTTermAttributesRoot)-[:LATEST]-(:CTTermAttributesValue {code_submission_value: "NO TREATMENT ELEMENT TYPE"})
    OPTIONAL MATCH (sv)-[:HAS_STUDY_COHORT]->(cohort:StudyCohort)
    WITH
        COUNT(DISTINCT arm) AS arm_count,
        COUNT(DISTINCT pre_treatment_epoch) AS pre_treatment_epoch_count,
        COUNT(DISTINCT treatment_epoch) AS treatment_epoch_count,
        COUNT(DISTINCT no_treatment_epoch) AS no_treatment_epoch_count,
        COUNT(DISTINCT post_treatment_epoch) AS post_treatment_epoch_count,
        COUNT(DISTINCT treatment_element) AS treatment_element_count,
        COUNT(DISTINCT no_treatment_element) AS no_treatment_element_count,
        COUNT(DISTINCT cohort) AS cohort_count
    RETURN
        {
            arms: arm_count,
            pre_treatment_epochs: pre_treatment_epoch_count,
            treatment_epochs: treatment_epoch_count,
            no_treatment_epochs: no_treatment_epoch_count,
            post_treatment_epochs: post_treatment_epoch_count,
            treatment_elements: treatment_element_count,
            no_treatment_elements: no_treatment_element_count,
            cohorts: cohort_count
        } as counts
}
RETURN
    sv.study_id_prefix + "-" + sv.study_number AS study_id,
    counts
"""

        rs = db.cypher_query(query=query)

        return rs

    def get_study_structure_statistics(self, uid: str) -> dict[str, int] | None:
        result = (
            StudyValue.nodes.filter(latest_value__uid=uid)
            .traverse_relations(
                Optional("has_study_arm"),
                Optional("has_study_branch_arm"),
                Optional("has_study_element"),
                Optional("has_study_cohort"),
                Optional("has_study_epoch"),
                Optional("has_study_footnote__references_study_epoch"),
                Optional("has_study_visit"),
                Optional("has_study_footnote__references_study_visit"),
            )
            .annotate(
                arm_count=Size(
                    Collect(NodeNameResolver("has_study_arm"), distinct=True)
                ),
                branch_count=Size(
                    Collect(NodeNameResolver("has_study_branch_arm"), distinct=True)
                ),
                element_count=Size(
                    Collect(NodeNameResolver("has_study_element"), distinct=True)
                ),
                cohort_count=Size(
                    Collect(NodeNameResolver("has_study_cohort"), distinct=True)
                ),
                epoch_count=Size(
                    Collect(NodeNameResolver("has_study_epoch"), distinct=True)
                ),
                epoch_footnote_count=Size(
                    Collect(
                        NodeNameResolver("has_study_footnote__references_study_epoch"),
                        distinct=True,
                    )
                ),
                visit_count=Size(
                    Collect(NodeNameResolver("has_study_visit"), distinct=True)
                ),
                visit_footnote_count=Size(
                    Collect(
                        NodeNameResolver("has_study_footnote__references_study_visit"),
                        distinct=True,
                    )
                ),
            )
            .all()
        )
        if not result:
            return None
        return {
            "arm_count": result[0][3],
            "branch_count": result[0][4],
            "element_count": result[0][5],
            "cohort_count": result[0][6],
            "epoch_count": result[0][7],
            "epoch_footnote_count": result[0][8],
            "visit_count": result[0][9],
            "visit_footnote_count": result[0][10],
        }

    def copy_study_items(
        self,
        study_src_uid: str,
        study_target_uid: str,
        list_of_items_to_copy: list[bool],
        author_id: str,
    ) -> dict[str, int] | None:
        exclusions = """
            NOT EXISTS((selection_src)--(:StudyActivity))
            AND NOT EXISTS((selection_src)--(:StudyActivitySubGroup))
            AND NOT EXISTS((selection_src)--(:StudyActivityGroup))
            AND NOT EXISTS((selection_src:StudySoAFootnote)--(:StudyActivitySchedule))
            AND NOT EXISTS((selection_src)--(:StudyActivityInstance))
            AND NOT EXISTS((selection_src)--(:StudySoAGroup))
        """
        if (
            "StudySoAFootnote" in list_of_items_to_copy
            and "StudyVisit" not in list_of_items_to_copy
        ):
            exclusions += """
            AND NOT EXISTS((selection_src:StudySoAFootnote)--(:StudyVisit))
        """
        if (
            "StudySoAFootnote" in list_of_items_to_copy
            and "StudyEpoch" not in list_of_items_to_copy
        ):
            exclusions += """
            AND NOT EXISTS((selection_src:StudySoAFootnote)--(:StudyEpoch))
        """

        # COPY NODES AND OUTBOUND RELATIONSHIPS
        query = f"""
WITH $study_src_uid as study_src, $study_target_uid as study_target, $to_copy_labels as to_copy_labels
with study_src, study_target, apoc.text.join(to_copy_labels, '|') AS to_copy_labels_text

MATCH (sr_src:StudyRoot)-[:LATEST]-(sv_src:StudyValue)
    WHERE sr_src.uid = study_src
MATCH (sr_target:StudyRoot)-[:LATEST]-(sv_target:StudyValue)
    WHERE sr_target.uid = study_target


CALL apoc.cypher.run("
    MATCH path = ((sr_src)--(saction_src:StudyAction)--(selection_src:StudySelection&(" + to_copy_labels_text + "))--(sv_src))
        WHERE {exclusions}
    return sr_src, sv_src,collect(path) as paths ", 
{{sr_src:sr_src, sv_src:sv_src }})
YIELD value

WITH  sr_target, value.sr_src as sr_src, sv_target, value.sv_src as sv_src,value.paths as paths
    
CALL apoc.refactor.cloneSubgraphFromPaths(paths, {{
    standinNodes:[[sv_src, sv_target], [sr_src,sr_target]]
}})
YIELD input, output, error
SET output:TEMP
WITH input,output
MATCH (selection_src:StudySelection)-[r_ext_src]-(ext_src)
    where ID(selection_src)=input
    and not "StudySelection" in labels(ext_src)
    and not "StudyAction" in labels(ext_src)
    and not "StudyValue" in labels(ext_src)
call apoc.create.relationship(output, type(r_ext_src), Null, ext_src)
yield rel
RETURN rel
"""
        parameters = {
            "study_src_uid": study_src_uid,
            "study_target_uid": study_target_uid,
            "to_copy_labels": list_of_items_to_copy,
        }
        db.cypher_query(query=query, params=parameters)

        # COPY BETWEEN SELECTIONS RELATIONSHIPS
        query = """
WITH $study_src_uid as study_src, $study_target_uid as study_target, $to_copy_labels as to_copy_labels

MATCH (sr_from:StudyRoot)-[:LATEST]-(sv_from:StudyValue)--(selection_src_from:StudySelection)-[r_ext_src]->(selection_src_to:StudySelection)
    where sr_from.uid = study_src
WITH selection_src_from.uid as from_uid, type(r_ext_src) AS from_rel_type_to, selection_src_to.uid as to_uid, study_target, to_copy_labels
match (sr_to:StudyRoot)-[:LATEST]-(sv_to:StudyValue)--(a:StudySelection)
    where sr_to.uid = study_target
match (sr_to)-[:LATEST]-(sv_to)--(b:StudySelection) 
WITH a,b, from_rel_type_to
    where a.uid = from_uid
    and b.uid = to_uid
    AND ANY(label IN labels(a) WHERE label IN to_copy_labels)
WITH DISTINCT a,b,from_rel_type_to

call apoc.merge.relationship(a, from_rel_type_to, null, Null, b)
yield rel


return *
"""
        parameters = {
            "study_src_uid": study_src_uid,
            "study_target_uid": study_target_uid,
            "to_copy_labels": list_of_items_to_copy,
        }
        db.cypher_query(query=query, params=parameters)

        # REFACTOR UIDS AND STUDY ACTIONS
        query = """


WITH $study_src_uid as study_src, $study_target_uid as study_target, $to_copy_labels as to_copy_labels, $date as date, $author_id as author_id

unwind to_copy_labels as to_copy_labels_unw

MATCH (sr_target:StudyRoot)-[:LATEST]-(sv_target:StudyValue)--(selection_target:StudySelection)
    where sr_target.uid = study_target

CALL {
    WITH to_copy_labels_unw, selection_target
    WITH to_copy_labels_unw, selection_target
        WHERE to_copy_labels_unw in labels(selection_target)
    MATCH (m:Counter{counterId:to_copy_labels_unw+'Counter'})
    WITH m,to_copy_labels_unw, selection_target
    CALL apoc.atomic.add(m,'count',1,1) yield oldValue, newValue
    WITH toInteger(newValue) as uid_number,to_copy_labels_unw, selection_target
    with to_copy_labels_unw+"_"+apoc.text.lpad(""+(uid_number), 6, "0") as new_uid, selection_target
    SET selection_target.uid = new_uid
    REMOVE selection_target:TEMP
}

WITH $study_src_uid as study_src, $study_target_uid as study_target, $to_copy_labels as to_copy_labels, $date as date, $author_id as author_id

MATCH (sr_target)--(saction:StudyAction:TEMP)
    where sr_target.uid = study_target
    and "TEMP" in labels(saction)
WITH distinct saction, author_id, date
SET saction.author_id = author_id
SET saction.date = date
REMOVE saction:TEMP
REMOVE saction:Edit
REMOVE saction:Create
SET saction:Create

return *
"""
        parameters = {
            "study_src_uid": study_src_uid,
            "study_target_uid": study_target_uid,
            "to_copy_labels": list_of_items_to_copy,
            "date": datetime.datetime.now(datetime.timezone.utc),
            "author_id": author_id,
        }
        result = db.cypher_query(query=query, params=parameters)

        return result

    def update_subpart_relationship(
        self,
        subpart_ar: StudyDefinitionAR,
        patch_parent_uid: str | None = None,
        new_parent: bool = True,
    ):
        if subpart_ar.study_parent_part_uid == patch_parent_uid:
            return

        parent_part_uid = patch_parent_uid or subpart_ar.study_parent_part_uid

        if new_parent:
            parent_study_ar = self.find_by_uid(parent_part_uid, for_update=True)

            self.save(study=parent_study_ar, is_subpart_relationship_update=True)

        study_subpart_root = StudyRoot.nodes.get(uid=subpart_ar.uid)
        latest_study_subpart_value = study_subpart_root.latest_value.single()

        study_parent_root = StudyRoot.nodes.get(uid=parent_part_uid)
        latest_study_parent_value = study_parent_root.latest_value.single()

        db.cypher_query(
            """
            MATCH (:StudyRoot {uid: $parent_uid})-[:LATEST]-(:StudyValue)
            -[pr:HAS_STUDY_SUBPART]->(:StudyValue)--(:StudyRoot {uid: $subpart_uid})
            DELETE pr

            WITH *

            MATCH (:StudyRoot {uid: $subpart_uid})-[:LATEST]-(:StudyValue)
            <-[sr:HAS_STUDY_SUBPART]-(:StudyValue)--(:StudyRoot {uid: $parent_uid})
            DELETE sr
            """,
            params={"parent_uid": parent_part_uid, "subpart_uid": subpart_ar.uid},
        )
        if patch_parent_uid:
            latest_study_parent_value.has_study_subpart.connect(
                latest_study_subpart_value
            )

    @staticmethod
    def find_uid_by_study_number(
        project_id: str, study_number: str, subpart_acronym: str | None = None
    ):
        if subpart_acronym:
            all_study_values = StudyValue.nodes.filter(
                study_id_prefix=project_id,
                study_number=study_number,
                study_subpart_acronym=subpart_acronym,
            )
        else:
            all_study_values = StudyValue.nodes.filter(
                study_id_prefix=project_id,
                study_number=study_number,
                study_subpart_acronym__isnull=True,
            )
        for study_value in all_study_values:
            study_root = study_value.latest_value.get_or_none()
            if study_root is not None:
                return study_root.uid
        return None

    @staticmethod
    def study_number_exists(study_number: str, uid: str | None = None) -> bool:
        """
        Checks whether a normal study or a parent study with specified study number already exists within the database.
        """
        params = {"study_number": study_number}

        query = """
            MATCH (value:StudyValue {study_number: $study_number})<-[:LATEST]-(root:StudyRoot)
            WHERE NOT (value)<-[:HAS_STUDY_SUBPART]-(:StudyValue)
        """

        if uid:
            query += " AND NOT root.uid = $uid "
            params |= {"uid": uid}

        query += " RETURN value"

        rs = db.cypher_query(query, params=params)

        return bool(rs[0])

    def save(
        self, study: StudyDefinitionAR, is_subpart_relationship_update=False
    ) -> None:
        """
        Public repository method for persisting a (possibly modified) state of the Study instance into the underlying
        DB. Provided instance can be brand new instance (never persisted before) or an instance which has been
        retrieved with find_by_uid(..., for_update=True). Attempt to persist an instance which was retrieved with
        for_update==False ends in error.

        :param study: an instance of Study aggregate (StudyDefinitionAR class) to persist
        """
        self._check_not_closed()
        repository_closure_data: RepositoryClosureData = study.repository_closure_data
        snapshot: StudyDefinitionSnapshot = study.get_snapshot()

        assert (
            snapshot.uid is not None
        )  # this should always hold (if not something must be wrong)

        if repository_closure_data is None:
            # this is the case of new instance (not persisted yet)
            self._create(snapshot)
        elif repository_closure_data.repository is not self:
            raise exceptions.BusinessLogicException(
                msg="Aggregate instances can be save only by repository which has retrieved the instance."
            )
        elif repository_closure_data.not_for_update:
            raise exceptions.BusinessLogicException(
                msg="Only aggregate instances retrieved for update can be saved."
            )
        else:
            # this is the case of saving an instance which was retrieved for update from this repository
            # if no one fiddled with repository closure data (which is strictly forbidden, only repository can do it)
            # following assertion should hold
            assert self.__retrieved_for_update[snapshot.uid] == study

            self._save(
                snapshot,
                repository_closure_data.additional_closure,
                is_subpart_relationship_update,
            )
            self.__retrieved_for_update.pop(snapshot.uid)

        # we assume save is possible only once per instance
        # the following prevent future saves for this instance
        # i.e. the instance is now marked as if it was retrieved with for_update==False
        study.repository_closure_data = RepositoryClosureData(
            not_for_update=True, repository=self, additional_closure=None
        )

    def find_all(
        self,
        has_study_footnote: bool | None = None,
        has_study_objective: bool | None = None,
        has_study_endpoint: bool | None = None,
        has_study_criteria: bool | None = None,
        has_study_activity: bool | None = None,
        has_study_activity_instruction: bool | None = None,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        deleted: bool = False,
    ) -> GenericFilteringReturn[StudyDefinitionAR]:
        """
        Public method which is to retrieve (a part of) whole Study repository content in the form of Study aggregate
        instances (StudyDefinitionAR class). The part of the content is given by pagination type parameters, accompanied
        with assumed sort of order of the repository given by identifying a sort key (currently only by uid supported)
        and possibility to request the order to be reverse. Instances are retrieved with for_update=False semantics (see
        description of find_by_uid method). Moreover it's forbidden to retrieve any Study instance for update before
        invoking this method (attempt to do that ends in Error).

        NOTE: Normally queried like this should not make use of domain model  since in most cases domain objects are
        too heavy to support reporting (meant as any queries that use data from numerous instances of aggregate).
        This has a chance to work fine only for very light aggregates and queries which do not need to use many
        instances. Currently this is a case for StudyDefinitionAR, so we do that (however we must be prepared for
        refactoring and reimplementation of those reporting methods as we progress).

        has_study_footnote: boolean to specify if returned studies must be linked to study footnotes or not
        has_study_objective: boolean to specify if returned studies must be linked to study objectives or not
        has_study_endpoint: boolean to specify if returned studies must be linked to study endpoints or not
        has_study_criteria: boolean to specify if returned studies must be linked to study criteria or not
        has_study_activity: boolean to specify if returned studies must be linked to study activities or not
        has_study_activity_instruction: boolean to specify if returned studies must be linked to activity instruction or not
        sort_by: dictionary of Cypher aliases on which to apply sorting as keys, and boolean to define sort direction (true=ascending) as values
        page_number : int, number of the page to return. 1-based
        page_size : int, number of results per page
        filter_by : dict, keys are field names for filter_variable and values are objects describing the filtering to execute
        total_count : boolean, indicates if total count of results should be returned
        :return: Dictionary of 'items' and 'total_count'. 'items' contains the results in the form of StudyDefinitionAR instances.
        Not more than page_size items. Can be less than than that in case of the last page.
        Empty sequence in case page_number and page_size parameters pass out of the whole repository content.
        """
        self._check_not_closed()
        # since query works in db so it cannot give proper result if we have some instances retrieved
        # for update
        assert len(self.__retrieved_for_update) == 0

        # delegating the real work to abstract method
        snapshots: GenericFilteringReturn[StudyDefinitionSnapshot] = (
            self._retrieve_all_snapshots(
                has_study_footnote=has_study_footnote,
                has_study_objective=has_study_objective,
                has_study_endpoint=has_study_endpoint,
                has_study_criteria=has_study_criteria,
                has_study_activity=has_study_activity,
                has_study_activity_instruction=has_study_activity_instruction,
                sort_by=sort_by,
                page_number=page_number,
                page_size=page_size,
                total_count=total_count,
                filter_by=filter_by,
                filter_operator=filter_operator,
                deleted=deleted,
            )
        )
        # projecting results to StudyDefinitionAR instances
        studies: list[StudyDefinitionAR] = [
            StudyDefinitionAR.from_snapshot(s) for s in snapshots.items
        ]

        # attaching a proper repository closure data
        repository_closure_data = RepositoryClosureData(
            not_for_update=True, repository=self, additional_closure=None
        )
        for study in studies:
            study.repository_closure_data = repository_closure_data

        # and we are done
        return GenericFilteringReturn.create(items=studies, total=snapshots.total)

    def find_study_snapshot_history(
        self,
        study_uid: str,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[StudyDefinitionAR]:
        study_snapshots = self._retrieve_study_snapshot_history(
            study_uid=study_uid,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=filter_by,
            filter_operator=filter_operator,
            total_count=total_count,
        )

        studies: list[StudyDefinitionAR] = [
            StudyDefinitionAR.from_snapshot(s) for s in study_snapshots.items
        ]

        study_snapshots.items = studies
        return study_snapshots

    def _retrieve_study_snapshot_history(
        self,
        study_uid: str,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[StudyDefinitionSnapshot]:
        raise NotImplementedError

    def get_occupied_study_subpart_ids(
        self, study_parent_part_uid: str, subpart_uid: str | None = None
    ):
        query = """
            MATCH (:StudyRoot {uid: $uid})-[:LATEST]->(:StudyValue)-[:HAS_STUDY_SUBPART]->(sv:StudyValue)<-[:LATEST]-(sr:StudyRoot)
            WHERE NOT EXISTS((sv)<-[:BEFORE]-(:StudyAction:`Delete`))"""

        if subpart_uid:
            query += " AND sr.uid <> $subpart_uid"

        query += """
            RETURN sv.subpart_id
            ORDER BY sv.subpart_id
            """

        return db.cypher_query(
            query,
            {"uid": study_parent_part_uid, "subpart_uid": subpart_uid},
        )

    def find_all_by_library_item_uid(
        self,
        uid: str,
        library_item_type: NodeMeta,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 50,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
    ) -> GenericFilteringReturn[StudyDefinitionAR]:
        """
        Public method which is to retrieve the list of studies having selected the library item with provided uid
        in the form of Study aggregate instances (StudyDefinitionAR class).

        :param uid: The uid of the library item that the study must have selected
        """
        self._check_not_closed()
        # Since query works in db so it cannot give proper result if we have some instances retrieved for update
        assert len(self.__retrieved_for_update) == 0

        # Find all studies referencing given library item
        # Get snapshots through implementation
        snapshots: GenericFilteringReturn[StudyDefinitionSnapshot] = (
            self._retrieve_all_snapshots(
                page_number=page_number,
                page_size=page_size,
                sort_by=sort_by,
                filter_by=filter_by,
                filter_operator=filter_operator,
                study_selection_object_node_id=uid,
                study_selection_object_node_type=library_item_type,
            )
        )
        # Project results to StudyDefinitionAR instances
        studies: list[StudyDefinitionAR] = [
            StudyDefinitionAR.from_snapshot(s) for s in snapshots.items
        ]

        # Attach a proper repository closure data
        repository_closure_data = RepositoryClosureData(
            not_for_update=True, repository=self, additional_closure=None
        )
        for study in studies:
            study.repository_closure_data = repository_closure_data

        # Return output
        return GenericFilteringReturn.create(items=studies, total=0)

    def close(self) -> None:
        """
        Marks this repository instance as closed. Closed repository cannot be used anymore.
        If concrete repository has some more cleanup to do it should override this method (but call super().close()).
        """
        self.__retrieved_for_update = {}
        self.__closed = True

    def __del__(self):
        if not self.__closed:
            self.close()

    @abstractmethod
    def _retrieve_snapshot_by_uid(
        self,
        uid: str,
        for_update: bool,
        study_value_version: str | None = None,
    ) -> tuple[StudyDefinitionSnapshot | None, Any]:
        """
        Abstract method of the study repository, which is supposed to:

        * retrieve a representation of study aggregate given by uid in a form of StudyDefinitionSnapshot object

        * if called with for_update == True the method should also either acquire relevant write locks (in case
            a repository implementation assumes pessimistic locking strategy) or provide information necessary to
            implement optimistic concurrency checks when this particular instance of aggregate is saved with _save
            method (a method can also do some combination of those or skip this for some part of aggregate state in case
            it's sure they are never updated).

        It's useful if the method makes as few as possible assumptions on aggregate behavior (i.e. what changes
        of aggregate state are possible/impossible) since it minimizes repository breakages in case of changes in
        business logic. However usually completely agnostic implementation will be very inefficient (or even
        impossible) hence it's expected there may be some assumptions.

        :param uid: uid of study representation to retrieve from db
        :param for_update: informs a method that the instance is retrieved to perform some update transaction
        :return: A two position tuple. First being state of the Study retrieved form db (or None if not exists), the
            second a reference to any additional object (or None) which will be passed on to the _save method at the
            time of saving the new state of aggregate back into repository as additional_closure parameter (this may
            contain whatever information are helpful for proper saving, e.g. above mentioned information needed for
            optimistic concurrency checks). NOTE: expected result in case a study with given uid does not exists in the
            underlying DB is (None, None) tuple.
        """
        raise NotImplementedError

    @abstractmethod
    def _save(
        self,
        snapshot: StudyDefinitionSnapshot,
        additional_closure: Any,
        is_subpart_relationship_update: bool = False,
    ) -> None:
        """
        Abstract method of the study repository, which is supposed to update and instance of the study aggregate, which
        was earlier retrieved with _get_by_uid (with for_update == True). The method is expected to save a new state
        of aggregate into database, assuring proper concurrency control (especially in case when concrete repository
        implementation assumes optimistic concurrency control) and assuring retaining all required audit information in
        the underlying DB (a method should read data from self.audit_info property to get relevant information).
        In case of concurrency control failure a method is expected to throw an Error.

        :param snapshot: A StudyDefinitionSnapshot representing a new state of the study. WARNING!: when this method
        is called it's not known for sure whether the state of the aggregate actually has changed. If it's important
        for the concrete repository implementation to know that then it must provide some mean of detecting this by
        attaching relevant additional_closure while performing _get_by_uid(..., for_update=True) and use this
        information here to detect if/what parts of the aggregate state has changed.

        :param additional_closure: A reference to object which was returned on index 2 of the tuple returned by
            _get_by_id when the instance of the aggregate was retrieved from the DB.

        :param is_subpart_relationship_update:
        """
        raise NotImplementedError

    @abstractmethod
    def _create(self, snapshot: StudyDefinitionSnapshot) -> None:
        """
        Abstract method of the study repository, which is supposed to persist a new instance of Study aggregate (the
        brand new study, not retrieved from repo) including retaining a proper audit information (a method should read
        data from self.audit_info property to get relevant information).

        :param snapshot: A state of the new study to persist.
        """
        raise NotImplementedError

    @abstractmethod
    def _retrieve_all_snapshots(
        self,
        has_study_footnote: bool | None = None,
        has_study_objective: bool | None = None,
        has_study_endpoint: bool | None = None,
        has_study_criteria: bool | None = None,
        has_study_activity: bool | None = None,
        has_study_activity_instruction: bool | None = None,
        sort_by: dict | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
        study_selection_object_node_id: int | None = None,
        study_selection_object_node_type: NodeMeta | None = None,
        deleted: bool = False,
    ) -> GenericFilteringReturn[StudyDefinitionSnapshot]:
        """
        Abstract method which is expected to retrieve (a part of) whole Study
        repository content in the form of
        sequence of StudySnapshots. This method allows for filtering, sorting and
        pagination scenarios.

        sort_by: dictionary of Cypher aliases on which to apply sorting as keys, and
        boolean to define sort direction (true=ascending) as values

        page_number : int, number of the page to return. 1-based

        page_size : int, number of results per page

        filter_by : dict, keys are field names for filter_variable and values are
        objects describing the filtering to execute

        total_count : boolean, indicates if total count of results should be returned

        :return: Dictionary of 'items' and 'total_count'. 'items' contains the
        results in the form of StudyDefinitionSnapshot instances. Not more than
        page_size items. Can
            be less than than that in case of the last page. Empty sequence in case
            page_number and page_size parameters
            pass out of the whole repository content.
        """
        raise NotImplementedError

    @abstractmethod
    def _retrieve_fields_audit_trail(
        self, uid: str
    ) -> list[StudyFieldAuditTrailEntryAR] | None:
        """
        Private method to retrieve an audit trail for a study by UID.
        :return: A list of Study field audit trail objects.
        """

    def get_audit_trail_by_uid(
        self, uid: str
    ) -> list[StudyFieldAuditTrailEntryAR] | None:
        """
        Public method which is to retrieve the audit trail for a given study identified by UID.
        :return: A list of retrieved data in a form StudyAuditTrailAR instances.
        """
        return self._retrieve_fields_audit_trail(uid)

    @abstractmethod
    def _retrieve_study_subpart_with_history(
        self, uid: str, is_subpart: bool = False, study_value_version: str | None = None
    ):
        """
        Private method to retrieve an audit trail for a study's subparts by UID.
        :return: A list of Study subpart audit trail objects.
        """

    def get_subpart_audit_trail_by_uid(
        self, uid: str, is_subpart: bool = False, study_value_version: str | None = None
    ) -> list:
        """
        Public method which is to retrieve the audit trail for a given study identified by UID.
        :return: A list of retrieved data in a form StudyAuditTrailAR instances.
        """
        return self._retrieve_study_subpart_with_history(
            uid, is_subpart, study_value_version=study_value_version
        )

    @abstractmethod
    def generate_uid(self) -> str:
        """
        A method that generates a new unique id
        for the StudyDefinition which is about to be created. It's meant to be used as a callback for some
        StudyDefinitionAR factories.
        :return: a string, an uid for the object about to be created
        """

    @abstractmethod
    def get_preferred_time_unit(
        self,
        study_uid: str,
        for_protocol_soa: bool = False,
        study_value_version: str | None = None,
    ) -> StudyPreferredTimeUnit:
        """
        A method that gets a StudyTimeField for the study preferred time unit. The preferred time unit is the unit definition
        that is used to display items like study visits on the timescale.
        :return: StudyPreferredTimeUnit
        """

    @abstractmethod
    def post_preferred_time_unit(
        self, study_uid: str, unit_definition_uid: str, for_protocol_soa: bool = False
    ) -> StudyPreferredTimeUnit:
        """
        A method that creates a StudyTimeField for the study preferred time unit. The preferred time unit is the unit definition
        that is used to display items like study visits on the timescale.
        :return: StudyPreferredTimeUnit
        """

    @abstractmethod
    def edit_preferred_time_unit(
        self, study_uid: str, unit_definition_uid: str, for_protocol_soa: bool = False
    ) -> StudyPreferredTimeUnit:
        """
        A method that edits a StudyTimeField for the study preferred time unit. The preferred time unit is the unit definition
        that is used to display items like study visits on the timescale.
        :return: StudyPreferredTimeUnit
        """

    @abstractmethod
    def get_soa_preferences(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        field_names: Sequence[str] | None = None,
    ) -> list[StudyBooleanField]:
        """
        Gets study SoA preferences.

        :return: list[StudyBooleanField]
        """

    @abstractmethod
    def post_soa_preferences(
        self,
        study_uid: str,
        soa_preferences: StudySoaPreferencesInput,
    ) -> list[StudyBooleanField]:
        """
        Creates study SoA preferences.

        :return: list[StudyBooleanField]
        """

    @abstractmethod
    def edit_soa_preferences(
        self,
        study_uid: str,
        soa_preferences: StudySoaPreferencesInput,
    ) -> list[StudyBooleanField]:
        """
        Updates study SoA preferences.

        :return: list[StudyBooleanField]
        """

    @abstractmethod
    def study_exists_by_uid(self, study_uid: str) -> bool:
        """
        A method that checks whether a Study exists with a specified study_uid
        :return: bool
        """

    @abstractmethod
    def check_if_study_is_locked(self, study_uid: str) -> bool:
        """
        A method that checks whether a Study with specified study_uid is locked
        :return: bool
        """

    @abstractmethod
    def check_if_study_is_deleted(self, study_uid: str) -> bool:
        """
        A method that checks whether a Study with specified study_uid is deleted
        :return: bool
        """

    @staticmethod
    @abstractmethod
    def check_if_study_uid_and_version_exists(
        study_uid: str, study_value_version: str | None = None
    ) -> bool:
        """
        Check if the study with the given study_uid and optionally with the study_value_version exists.

        Args:
            study_uid (str): The unique identifier of the study.
            study_value_version (str | None): The version of the study to check. Defaults to None.

        Returns:
            bool: True if the study exists, False otherwise.
        """
