import datetime
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Sequence

from neomodel import db
from neomodel.sync_.node import NodeMeta

from clinical_mdr_api.domain_repositories.generic_repository import (
    RepositoryClosureData,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    format_generic_header_values,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_field import (
    StudyArrayField,
    StudyBooleanField,
)
from clinical_mdr_api.domain_repositories.models.study_selections import (
    STUDY_SELECTION_CONCRETE_LABELS,
    STUDY_SELECTION_LABELS_EXCLUDED_FROM_CONTAINMENT,
)
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
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    validate_filters_and_add_search_string,
)
from common import exceptions
from common.telemetry import trace_calls
from common.utils import convert_to_datetime


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

    @trace_calls
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
        snapshot, additional_closure = self._retrieve_snapshot_by_uid(
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

    def study_structure_overview_match_clause(self):
        return """
MATCH (sr:StudyRoot)-[:LATEST]->(sv:StudyValue)
WHERE sv.study_id_prefix IS NOT NULL AND sv.study_number IS NOT NULL
OPTIONAL MATCH (sv)-[:HAS_STUDY_ARM]->(arm:StudyArm)
OPTIONAL MATCH (sv)-[:HAS_STUDY_EPOCH]->(pre_treatment_epoch:StudyEpoch)-[:HAS_EPOCH_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(:CTCodelistTerm {submission_value: "PRE TREATMENT EPOCH TYPE"})
OPTIONAL MATCH (sv)-[:HAS_STUDY_EPOCH]->(treatment_epoch:StudyEpoch)-[:HAS_EPOCH_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(:CTCodelistTerm {submission_value: "TREATMENT"})
OPTIONAL MATCH (sv)-[:HAS_STUDY_EPOCH]->(no_treatment_epoch:StudyEpoch)-[:HAS_EPOCH_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(:CTCodelistTerm {submission_value: "NO TREATMENT EPOCH TYPE"})
OPTIONAL MATCH (sv)-[:HAS_STUDY_EPOCH]->(post_treatment_epoch:StudyEpoch)-[:HAS_EPOCH_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(:CTCodelistTerm {submission_value: "POST TREATMENT EPOCH TYPE"})
OPTIONAL MATCH (sv)-[:HAS_STUDY_ELEMENT]->(treatment_element:StudyElement)-[:HAS_ELEMENT_SUBTYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_PARENT_TYPE]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(:CTCodelistTerm {submission_value: "TREATMENT ELEMENT TYPE"})
OPTIONAL MATCH (sv)-[:HAS_STUDY_ELEMENT]->(no_treatment_element:StudyElement)-[:HAS_ELEMENT_SUBTYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_PARENT_TYPE]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(:CTCodelistTerm {submission_value: "NO TREATMENT ELEMENT TYPE"})
OPTIONAL MATCH (sv)-[:HAS_STUDY_COHORT]->(cohort:StudyCohort)
"""

    def study_structure_overview_alias_clause(self):
        return """sv,
COUNT(DISTINCT arm) AS arms,
COUNT(DISTINCT pre_treatment_epoch) AS pre_treatment_epochs,
COUNT(DISTINCT treatment_epoch) AS treatment_epochs,
COUNT(DISTINCT no_treatment_epoch) AS no_treatment_epochs,
COUNT(DISTINCT post_treatment_epoch) AS post_treatment_epochs,
COUNT(DISTINCT treatment_element) AS treatment_elements,
COUNT(DISTINCT no_treatment_element) AS no_treatment_elements,
CASE COUNT(DISTINCT cohort) WHEN > 0
  THEN 'Y'
  ELSE 'N'
END AS cohorts_in_study,
sv.study_id_prefix + "-" + sv.study_number AS study_ids
"""

    def get_study_structure_overview(self):
        query = """
MATCH (sr:StudyRoot)-[:LATEST]->(sv:StudyValue)
WHERE sv.study_id_prefix IS NOT NULL AND sv.study_number IS NOT NULL
CALL (sv) {
    OPTIONAL MATCH (sv)-[:HAS_STUDY_ARM]->(arm:StudyArm)
    OPTIONAL MATCH (sv)-[:HAS_STUDY_EPOCH]->(pre_treatment_epoch:StudyEpoch)-[:HAS_EPOCH_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(:CTCodelistTerm {submission_value: "PRE TREATMENT EPOCH TYPE"})
    OPTIONAL MATCH (sv)-[:HAS_STUDY_EPOCH]->(treatment_epoch:StudyEpoch)-[:HAS_EPOCH_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(:CTCodelistTerm {submission_value: "TREATMENT"})
    OPTIONAL MATCH (sv)-[:HAS_STUDY_EPOCH]->(no_treatment_epoch:StudyEpoch)-[:HAS_EPOCH_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(:CTCodelistTerm {submission_value: "NO TREATMENT EPOCH TYPE"})
    OPTIONAL MATCH (sv)-[:HAS_STUDY_EPOCH]->(post_treatment_epoch:StudyEpoch)-[:HAS_EPOCH_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(:CTCodelistTerm {submission_value: "POST TREATMENT EPOCH TYPE"})
    OPTIONAL MATCH (sv)-[:HAS_STUDY_ELEMENT]->(treatment_element:StudyElement)-[:HAS_ELEMENT_SUBTYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_PARENT_TYPE]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(:CTCodelistTerm {submission_value: "TREATMENT ELEMENT TYPE"})
    OPTIONAL MATCH (sv)-[:HAS_STUDY_ELEMENT]->(no_treatment_element:StudyElement)-[:HAS_ELEMENT_SUBTYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_PARENT_TYPE]->(:CTTermRoot)<-[:HAS_TERM_ROOT]-(:CTCodelistTerm {submission_value: "NO TREATMENT ELEMENT TYPE"})
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

    def get_study_structure_overview_headers(
        self,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
    ) -> list[str]:
        match_clause = self.study_structure_overview_match_clause()
        alias_clause = self.study_structure_overview_alias_clause()
        filter_by = validate_filters_and_add_search_string(
            search_string, field_name, filter_by
        )
        query = CypherQueryBuilder(
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            match_clause=match_clause,
            alias_clause=alias_clause,
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

    def get_study_structure_statistics(self, uid: str) -> dict[str, int] | None:
        query = """
MATCH (sr:StudyRoot {uid: $uid})-[:LATEST]->(sv:StudyValue)
RETURN
    SIZE([(sv)-[:HAS_STUDY_ARM]->(:StudyArm) | 1]) AS arm_count,
    SIZE([(sv)-[:HAS_STUDY_BRANCH_ARM]->(:StudyBranchArm) | 1]) AS branch_count,
    SIZE([(sv)-[:HAS_STUDY_ELEMENT]->(:StudyElement) | 1]) AS element_count,
    SIZE([(sv)-[:HAS_STUDY_COHORT]->(:StudyCohort) | 1]) AS cohort_count,
    SIZE([(sv)-[:HAS_STUDY_EPOCH]->(:StudyEpoch) | 1]) AS epoch_count,
    SIZE([(sv)-[:HAS_STUDY_FOOTNOTE]->(:StudySoAFootnote)-[:REFERENCES_STUDY_EPOCH]->(:StudyEpoch) | 1]) AS epoch_footnote_count,
    SIZE([(sv)-[:HAS_STUDY_VISIT]->(:StudyVisit) | 1]) AS visit_count,
    SIZE([(sv)-[:HAS_STUDY_FOOTNOTE]->(:StudySoAFootnote)-[:REFERENCES_STUDY_VISIT]->(:StudyVisit) | 1]) AS visit_footnote_count,
    SIZE([(sv)-[:HAS_STUDY_ACTIVITY]->(:StudyActivity) | 1]) AS study_activity_count,
    SIZE([(sv)-[:HAS_STUDY_ACTIVITY_SCHEDULE]->(:StudyActivitySchedule) | 1]) AS study_activity_schedule_count
"""
        result, _ = db.cypher_query(query=query, params={"uid": uid})

        if not result:
            return None

        counts = result[0]
        return {
            "arm_count": counts[0],
            "branch_count": counts[1],
            "element_count": counts[2],
            "cohort_count": counts[3],
            "epoch_count": counts[4],
            "epoch_footnote_count": counts[5],
            "visit_count": counts[6],
            "visit_footnote_count": counts[7],
            "study_activity_count": counts[8],
            "study_activity_schedule_count": counts[9],
        }

    def get_study_selection_labels_for_study(self, study_uid: str) -> list[str]:
        """
        Distinct concrete study-selection labels present on the study's latest value
        (only labels in :data:`STUDY_SELECTION_CONCRETE_LABELS`).
        """
        query = """
        MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)-[rel]->(ss:StudySelection)
        WHERE type(rel) <> 'HAS_PROTOCOL_SOA_CELL' AND type(rel) <> 'HAS_PROTOCOL_SOA_FOOTNOTE'
        UNWIND labels(ss) AS lb
        WITH lb
        WHERE lb IN $known_labels
        RETURN DISTINCT lb AS label
        ORDER BY label
        """
        rows, _ = db.cypher_query(
            query,
            {
                "study_uid": study_uid,
                "known_labels": list(STUDY_SELECTION_CONCRETE_LABELS),
            },
        )
        return [str(r[0]) for r in rows]

    def get_study_selection_statistics_for_labels(
        self, study_uid: str, labels: list[str]
    ) -> dict[str, dict[str, int]]:
        """
        Per-label selection counts and distinct CT term root counts (via CTTermContext)
        for the given labels on the study's latest value.
        """
        if not labels:
            return {}
        query = """
        UNWIND $labels AS want
        OPTIONAL MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)-[rel]->(ss:StudySelection)
        WHERE type(rel) <> 'HAS_PROTOCOL_SOA_CELL' AND type(rel) <> 'HAS_PROTOCOL_SOA_FOOTNOTE'
          AND want IN labels(ss)
        OPTIONAL MATCH (ss)-[]->(ctx:CTTermContext)-[:HAS_SELECTED_TERM]->(tr:CTTermRoot)
        RETURN want,
               count(DISTINCT ss) AS selection_count,
               count(DISTINCT tr) AS distinct_ct_term_root_count
        ORDER BY want
        """
        rows, _ = db.cypher_query(query, {"study_uid": study_uid, "labels": labels})
        out: dict[str, dict[str, int]] = {}
        for row in rows:
            want, sel_count, term_count = row[0], int(row[1]), int(row[2])
            out[str(want)] = {
                "selection_count": sel_count,
                "distinct_ct_term_root_count": term_count,
            }
        return out

    def get_study_selection_containment(
        self, source_study_uid: str, target_study_uid: str
    ) -> dict[str, Any]:
        """
        Whether **target** selection statistics (counts only for labels that appear on
        **target**) are numerically contained in **source**:
        for each such label, target counts must be <= source counts.

        Used to compare a clone (target) against its source study when only a subset
        of labels may have been copied, or to verify full clone equality (then counts
        match and containment holds).

        ``StudySoAFootnote`` is excluded: clone copies footnotes conditionally, so
        footnote counts are not compared on source or target.
        """
        labels = [
            lb
            for lb in self.get_study_selection_labels_for_study(target_study_uid)
            if lb not in STUDY_SELECTION_LABELS_EXCLUDED_FROM_CONTAINMENT
        ]
        if not labels:
            return {
                "target_contained_in_source": True,
                "labels_from_target": [],
                "per_label": [],
            }
        src_stats = self.get_study_selection_statistics_for_labels(
            source_study_uid, labels
        )
        tgt_stats = self.get_study_selection_statistics_for_labels(
            target_study_uid, labels
        )
        per_label: list[dict[str, Any]] = []
        all_contained = True
        for lb in labels:
            s = src_stats.get(
                lb,
                {"selection_count": 0, "distinct_ct_term_root_count": 0},
            )
            t = tgt_stats.get(
                lb,
                {"selection_count": 0, "distinct_ct_term_root_count": 0},
            )
            sc, stc = s["selection_count"], s["distinct_ct_term_root_count"]
            tc, ttc = t["selection_count"], t["distinct_ct_term_root_count"]
            label_ok = tc <= sc and ttc <= stc
            if not label_ok:
                all_contained = False
            per_label.append(
                {
                    "label": lb,
                    "target_selection_count": tc,
                    "source_selection_count": sc,
                    "target_distinct_ct_term_root_count": ttc,
                    "source_distinct_ct_term_root_count": stc,
                    "label_contained": label_ok,
                }
            )
        return {
            "target_contained_in_source": all_contained,
            "labels_from_target": labels,
            "per_label": per_label,
        }

    def copy_study_items(
        self,
        study_src_uid: str,
        study_target_uid: str,
        list_of_items_to_copy: list[str],
        author_id: str,
    ) -> dict[str, int] | None:
        parameters: dict[str, str | list[str] | datetime.datetime] = {}
        exclusions = "TRUE"
        for label in (
            "StudyVisit",
            "StudyEpoch",
            "StudyActivity",
            "StudyActivitySubGroup",
            "StudyActivityGroup",
            "StudySoAGroup",
            "StudyActivitySchedule",
        ):
            if (
                "StudySoAFootnote" in list_of_items_to_copy
                and label not in list_of_items_to_copy
            ):
                exclusions += f"""
            AND NOT ((selection_src:StudySoAFootnote)--(:{label}))
        """

        # COPY NODES AND OUTBOUND RELATIONSHIPS
        query = f"""
WITH
    $study_src_uid as study_src,
    $study_target_uid as study_target,
    $to_copy_labels as to_copy_labels
with
    study_src,
    study_target,
    apoc.text.join(to_copy_labels, '|') AS to_copy_labels_text

MATCH
    (sr_src:StudyRoot)-[:LATEST]->
    (sv_src:StudyValue)
    WHERE
        sr_src.uid = study_src
MATCH
    (sr_target:StudyRoot)-[:LATEST]->
    (sv_target:StudyValue)
    WHERE
        sr_target.uid = study_target

CALL apoc.cypher.run("
    MATCH
        (selection_src:StudySelection&(" + to_copy_labels_text + "))<-[sv_has_selection]-
        (sv_src)
    WHERE type(sv_has_selection) <> 'HAS_PROTOCOL_SOA_CELL' AND type(sv_has_selection) <> 'HAS_PROTOCOL_SOA_FOOTNOTE'
    MATCH
        (sr_src)-[audit_trail:AUDIT_TRAIL]->
        (saction_src:StudyAction)-[saction_selection:AFTER]->
        (selection_src)
    MATCH path = (
            (sr_src)-[audit_trail]->
            (saction_src)-[saction_selection]-
            (selection_src)<-[sv_has_selection]-
            (sv_src)
        )
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
WITH
    $study_src_uid as study_src,
    $study_target_uid as study_target,
    $to_copy_labels as to_copy_labels

MATCH
    (sr_from:StudyRoot)-[:LATEST]->
    (sv_from:StudyValue)-[sv_to_ss_source]->
    (selection_src_from:StudySelection)-[r_ext_src]->
    (selection_src_to:StudySelection)
        where
            sr_from.uid = study_src
            AND type(sv_to_ss_source) <> "HAS_PROTOCOL_SOA_CELL"
            AND type(sv_to_ss_source) <> "HAS_PROTOCOL_SOA_FOOTNOTE"
MATCH (selection_src_to)--(sv_from)

WITH
    selection_src_from.uid as from_uid,
    type(r_ext_src) AS from_rel_type_to,
    selection_src_to.uid as to_uid,
    study_target,
    to_copy_labels
MATCH
    (sr_to:StudyRoot)-[:LATEST]->
    (sv_to:StudyValue)-->
    (a:StudySelection)
        where
            sr_to.uid = study_target
MATCH
    (sr_to)-[:LATEST]->
    (sv_to)-[sv_to__b]->
    (b:StudySelection)
        WHERE
            type(sv_to__b) <> "HAS_PROTOCOL_SOA_CELL"
            AND type(sv_to__b) <> "HAS_PROTOCOL_SOA_FOOTNOTE"
WITH
    a,
    b,
    from_rel_type_to
        where
            a.uid = from_uid
            and b.uid = to_uid
            AND ANY(
                label IN labels(a)
                    WHERE
                        label IN to_copy_labels
            )
WITH DISTINCT
    a,
    b,
    from_rel_type_to

call apoc.merge.relationship(
    a,
    from_rel_type_to,
    null,
    Null,
    b
)
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

// GO ONE BY ONE LABEL TO COPY
unwind to_copy_labels as to_copy_labels_unw

MATCH (sr_target:StudyRoot)-[:LATEST]->(sv_target:StudyValue)-[relationship]-(selection_target:StudySelection)
    where sr_target.uid = study_target AND type(relationship) <> "HAS_PROTOCOL_SOA_CELL" AND type(relationship) <> "HAS_PROTOCOL_SOA_FOOTNOTE"

// Update the counter value and generate new UID and
CALL (to_copy_labels_unw, selection_target) {
    WITH to_copy_labels_unw, selection_target
        WHERE to_copy_labels_unw in labels(selection_target)
    MATCH (m:Counter{counterId:to_copy_labels_unw+'Counter'})
    WITH m,to_copy_labels_unw, selection_target
    CALL apoc.atomic.add(m,'count',1,1) yield oldValue, newValue
    WITH toInteger(newValue) as uid_number,to_copy_labels_unw, selection_target
    with to_copy_labels_unw+"_"+apoc.text.lpad(""+(uid_number), 6, "0") as new_uid, selection_target
    SET selection_target.old_uid = selection_target.uid
    SET selection_target.uid = new_uid
}

// find the visit_anchor
CALL (to_copy_labels_unw, selection_target) {
    WITH to_copy_labels_unw, selection_target
        WHERE "StudyVisit" in labels(selection_target) and selection_target.visit_sublabel_reference IS NOT NULL
    MATCH (ref_svis:StudyVisit:TEMP{old_uid:selection_target.visit_sublabel_reference})
    set selection_target.visit_sublabel_reference = ref_svis.uid
}

// remove TEMP label, remove old_uid
CALL (to_copy_labels_unw, selection_target) {
    WITH to_copy_labels_unw, selection_target
        WHERE to_copy_labels_unw in labels(selection_target)
    SET selection_target.old_uid = NULL
    REMOVE selection_target:TEMP
}

WITH $study_src_uid as study_src, $study_target_uid as study_target, $to_copy_labels as to_copy_labels, $date as date, $author_id as author_id

// Update action metadata and clean up temp labels
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

    @staticmethod
    def study_acronym_exists(study_acronym: str, uid: str | None = None) -> bool:
        """
        Checks whether a normal study or a parent study with specified study acronym already exists within the database.
        """
        params = {"study_acronym": study_acronym}

        query = """
            MATCH (value:StudyValue {study_acronym: $study_acronym})<-[:LATEST]-(root:StudyRoot)
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

    def get_studies_list(
        self,
        minimal_response: bool = True,
        has_study_objective: bool | None = None,
        has_study_footnote: bool | None = None,
        has_study_endpoint: bool | None = None,
        has_study_criteria: bool | None = None,
        has_study_activity: bool | None = None,
        has_study_activity_instruction: bool | None = None,
        deleted: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Public method to retrieve a list of all studies in the repository.
        Returns a list of dictionaries.
        """

        def where_stmt():
            conditions = []

            checks = [
                (has_study_objective, "HAS_STUDY_OBJECTIVE", "StudyObjective"),
                (has_study_footnote, "HAS_STUDY_FOOTNOTE", "StudySoAFootnote"),
                (has_study_endpoint, "HAS_STUDY_ENDPOINT", "StudyEndpoint"),
                (has_study_criteria, "HAS_STUDY_CRITERIA", "StudyCriteria"),
                (has_study_activity, "HAS_STUDY_ACTIVITY", "StudyActivity"),
                (
                    has_study_activity_instruction,
                    "HAS_STUDY_ACTIVITY_INSTRUCTION",
                    "StudyActivityInstruction",
                ),
            ]

            for flag, relationship, node_label in checks:
                if flag is not None:
                    prefix = "" if flag else "NOT "
                    conditions.append(
                        f"{prefix}EXISTS((sv)-[:{relationship}]->(:{node_label}))"
                    )

            if not deleted:
                conditions.append("NOT EXISTS((sv)<-[:BEFORE]-(:Delete))")
            else:
                conditions.append("EXISTS((sv)<-[:BEFORE]-(:Delete))")

            return f"WHERE {' AND '.join(conditions)}" if conditions else ""

        self._check_not_closed()

        if minimal_response:
            query = f"""
                MATCH (sr:StudyRoot)-[:LATEST]->(sv:StudyValue)
                {where_stmt()}

                RETURN sr.uid AS uid,
                    sv.study_id_prefix + '-' + sv.study_number + COALESCE(nullif('-' + sv.study_subpart_acronym, '-'), '') as id,
                    sv.study_acronym,
                    sv.study_subpart_acronym
                ORDER BY uid
            """
            rs = db.cypher_query(query)
            return [
                {
                    "uid": row[0],
                    "id": row[1],
                    "acronym": row[2],
                    "subpart_acronym": row[3],
                }
                for row in rs[0]
            ]

        query = f"""
            MATCH (sr:StudyRoot)-[:LATEST]->(sv:StudyValue)-[:HAS_PROJECT]-(:StudyProjectField)<-[:HAS_FIELD]-(p:Project)<-[:HOLDS_PROJECT]-(cp:ClinicalProgramme)
            {where_stmt()}

            WITH sr,sv,p,cp
            OPTIONAL MATCH (sv)-[:HAS_TEXT_FIELD]->(stf:StudyTextField {{field_name: 'study_title'}})
            WITH sr, sv, p, cp, stf, COLLECT {{
                MATCH (sr)-[ver:HAS_VERSION|LATEST_DRAFT|LATEST_LOCKED|LATEST_RELEASED]->(sv)
                RETURN ver
                order by ver.start_date desc
                limit 1
            }} as versions,
            COLLECT {{
                MATCH (sr)-[ver:LATEST_RELEASED]->(:StudyValue)
                RETURN {{version_number: ver.version, change_description: ver.change_description}}
            }} as latest_released,
            COLLECT {{
                MATCH (sr)-[ver:LATEST_LOCKED]->(:StudyValue)
                RETURN {{version_number: ver.version, change_description: ver.change_description}}
            }} as latest_locked
            WITH sr, sv, p, cp, stf,
                head(versions) as current_version,
                head(latest_released) as latest_released_version,
                head(latest_locked) as latest_locked_version
            OPTIONAL MATCH (author:User {{user_id: current_version.author_id}})
            RETURN sr.uid AS uid,
                sv.study_acronym,
                sv.study_id_prefix + '-' + sv.study_number + COALESCE(nullif('-' + sv.study_subpart_acronym, '-'), '') as id,
                sv.study_id_prefix + '-' + sv.study_number as main_id,
                sv.study_number,
                sv.subpart_id,
                sv.study_subpart_acronym,
                stf.value as study_title,
                cp.name as clinical_programme,
                p.project_number as project_number,
                p.name as project_name,
                current_version.author_id as version_author_id,
                current_version.status as version_status,
                current_version.start_date as version_start_date,
                current_version.version as version_number,
                COALESCE(author.username, current_version.author_id) as author,
                latest_locked_version,
                latest_released_version,
                [(sr)-[:HAS_COMPLETENESS_TAG]->(t:DataCompletenessTag) | t.name] as data_completeness_tags,
                sv.description
            ORDER BY uid
        """
        rs = db.cypher_query(query)
        return [
            {
                "uid": row[0],
                "acronym": row[1],
                "id": row[2],
                "main_id": row[3],
                "study_number": row[4],
                "subpart_id": row[5],
                "subpart_acronym": row[6],
                "title": row[7],
                "clinical_programme_name": row[8],
                "project_number": row[9],
                "project_name": row[10],
                "version_author_id": row[11],
                "version_status": row[12],
                "version_start_date": convert_to_datetime(row[13]),
                "version_number": row[14],
                "version_author": row[15],
                "latest_locked_version": row[16],
                "latest_released_version": row[17],
                "data_completeness_tags": row[18],
                "description": row[19],
            }
            for row in rs[0]
        ]

    @trace_calls
    def find_all(
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
        return GenericFilteringReturn(items=studies, total=snapshots.total)

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
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 50,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
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
        return GenericFilteringReturn(items=studies, total=0)

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
        self,
        uid: str,
        is_subpart: bool = False,
        study_value_version: str | None = None,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """
        Private method to retrieve an audit trail for a study's subparts by UID.
        :return: A GenericFilteringReturn containing Study subpart audit trail objects.
        """

    def get_subpart_audit_trail_by_uid(
        self,
        uid: str,
        is_subpart: bool = False,
        study_value_version: str | None = None,
        page_number: int = 1,
        page_size: int = 0,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """
        Public method which is to retrieve the audit trail for a given study identified by UID.
        :return: A GenericFilteringReturn containing StudySubpartAuditTrail instances.
        """
        return self._retrieve_study_subpart_with_history(
            uid,
            is_subpart,
            study_value_version=study_value_version,
            page_number=page_number,
            page_size=page_size,
            total_count=total_count,
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
    ) -> list[StudyPreferredTimeUnit]:
        """
        A method that gets a StudyTimeField for the study preferred time unit. The preferred time unit is the unit definition
        that is used to display items like study visits on the timescale.
        :return: StudyPreferredTimeUnit
        """

    @abstractmethod
    def post_preferred_time_unit(
        self, study_uid: str, unit_definition_uid: str, for_protocol_soa: bool = False
    ) -> list[StudyPreferredTimeUnit]:
        """
        A method that creates a StudyTimeField for the study preferred time unit. The preferred time unit is the unit definition
        that is used to display items like study visits on the timescale.
        :return: StudyPreferredTimeUnit
        """

    @abstractmethod
    def edit_preferred_time_unit(
        self, study_uid: str, unit_definition_uid: str, for_protocol_soa: bool = False
    ) -> list[StudyPreferredTimeUnit]:
        """
        A method that edits a StudyTimeField for the study preferred time unit. The preferred time unit is the unit definition
        that is used to display items like study visits on the timescale.
        :return: StudyPreferredTimeUnit
        """

    @staticmethod
    @abstractmethod
    def get_soa_preferences(
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

    @staticmethod
    @abstractmethod
    def get_study_id(
        study_uid: str, study_value_version: str | None = None
    ) -> str | None:
        """Returns Study id if Study exists and StudyVersion exists and not deleted, and both study_id_prefix and study_number are defined, otherwise None."""

    @staticmethod
    @abstractmethod
    def get_soa_split_uids(
        study_uid: str,
        study_value_version: str | None,
    ) -> StudyArrayField | None:
        """
        Returns StudyArrayField with value as a list of StudyVisit uids for splitting SoA

        Args:
            study_uid (str): The unique identifier of the study.
            study_value_version (str | None): The version of the Study. Defaults to None for latest version.

        Raises:
             NotFoundException: if SoA splitting StudyArrayField does not exist for the given study
        Returns:
            StudyArrayField | None: StudyArrayField with value as a list of StudyVisit uids for splitting SoA,
                                    or None if splitting is not set.
        """

    @abstractmethod
    def add_soa_split_uid(
        self,
        study_uid: str,
        uid: str,
    ) -> StudyArrayField:
        """
        Adds StudyVisit uid to StudyArrayField for splitting SoA

        Args:
            study_uid (str): The unique identifier of the study.
            uid (str): The StudyVisit uid to add.

        Raises:
            NotFoundException: if StudyVisit uid does not exist for the given study
            AlreadyExistsException: if StudyVisit uid is already in the value of SoA splitting StudyArrayField
        Returns:
            StudyArrayField: updated StudyArrayField with the new StudyVisit uid added
        """

    @abstractmethod
    def remove_soa_split_uid(
        self,
        study_uid: str,
        uid: str,
    ) -> StudyArrayField | None:
        """
        Removes StudyVisit uid from StudyArrayField for splitting SoA

        Args:
            study_uid (str): The unique identifier of the study.
            uid (str): The uid to remove.

        Raises:
            NotFoundException: if StudyVisit uid is not in the value of SoA splitting StudyArrayField
        Returns:
            StudyArrayField | None: updated StudyArrayField with the StudyVisit uid removed, or None if no uids remain.
        """

    @abstractmethod
    def remove_soa_splits(
        self,
        study_uid: str,
    ) -> None:
        """
        Removes StudyArrayField for splitting SoA

        Args:
            study_uid (str): The unique identifier of the study.

        Returns:
            None
        """
