import json
import os
from datetime import datetime
from typing import Any

from neomodel import db

from clinical_mdr_api import utils
from clinical_mdr_api.domains.study_definition_aggregates.study_configuration import (
    FieldConfiguration,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    calculate_total_count_from_query_result,
)
from common.config import settings

MATCH_SPECIFIC_STUDY_VERSION = """
    MATCH (sr:StudyRoot {uid: $study_uid})-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]->(sv:StudyValue)
"""

MATCH_LATEST_STUDY = """
    MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)
"""

# TS parameter term UIDs for computed/derived parameters (not from StudyField).
TS_COHORT_COUNT_TERM_UID = "C126063"
TS_ARM_COUNT_TERM_UID = "C98771"
TS_PHARMA_CLASS_TERM_UID = "C98768"
TS_RANDOMIZATION_QUOTIENT_TERM_UID = "C98775"

# Submission value for the Registry Identifier TS parameter.
TS_REGID_SUBMVAL = "REGID"


def _build_registry_identifier_cypher_fragment() -> tuple[str, str]:
    """Build the CASE and IN-list fragments for registry identifier fields from FieldConfiguration."""
    vcdref_map = FieldConfiguration.registry_identifier_vcdref_map()
    field_names_list = ", ".join(f"'{name}'" for name in vcdref_map)
    case_lines = "\n                ".join(
        f"WHEN '{name}' THEN '{ref}'" for name, ref in vcdref_map.items()
    )
    return field_names_list, case_lines


class QueryService:
    """class holding the queries for the listing endpoints."""

    @staticmethod
    def _filter_for_cdisc_ct(
        catalogue_name: str | None = None,
        package: str | None = None,
        after_date: str | None = None,
    ) -> tuple[str, dict[Any, Any]]:
        """Create filter to use in cypher query"""
        filter_parameters = []
        filter_query_parameters = {}
        if catalogue_name:
            filter_by_catalogue = "toUpper(cat.name) in apoc.text.split(toUpper($catalogue_name), '[ ]*,[ ]*')"
            filter_parameters.append(filter_by_catalogue)
            filter_query_parameters["catalogue_name"] = catalogue_name
        if package:
            filter_by_package_name = "toUpper(package.name) in apoc.text.split(toUpper($package_name), '[ ]*,[ ]*')"
            filter_parameters.append(filter_by_package_name)
            filter_query_parameters["package_name"] = package
        if after_date:
            filter_by_after_date = """
                package.effective_date >= date($after_date)
            """
            filter_parameters.append(filter_by_after_date)
            filter_query_parameters["after_date"] = after_date

        filter_statements = " AND ".join(filter_parameters)
        filter_statements = (
            "WHERE " + filter_statements if len(filter_statements) > 0 else ""
        )
        return filter_statements, filter_query_parameters

    def get_metadata(self, dataset_name) -> list[Any]:
        """Get metadata for legacy (and other) datasets"""

        with open(
            os.getcwd() + "/clinical_mdr_api/listings/metadata.json",
            "r",
            encoding="UTF-8",
        ) as metadata:
            meta = json.load(metadata)

        if dataset_name:
            meta = [
                x
                for x in meta
                if x["dataset_name"] in dataset_name.replace(" ", "").lower().split(",")
            ]

        return meta

    def get_topic_codes(
        self,
        at_specific_date: datetime | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """Query to get the legacy dataset topic_cd_def."""

        match_clause = """
            MATCH (r:ActivityInstanceRoot)-[l]->(n:ActivityInstanceValue) 
            """

        if at_specific_date:
            filter_query = """
                WHERE (type(l)='HAS_VERSION' and l.status='Final'
                      and l.start_date < datetime($at_specific_date) <= l.end_date)
            """
        else:
            filter_query = """
                WHERE type(l)='LATEST_FINAL'
            """

        alias_clause = """
        
              n.name                       as lb,
              n.topic_code                 as topic_cd,
              n.adam_param_code            as short_topic_cd,
              coalesce(n.is_required_for_activity, false)   as is_required_for_activity,
              coalesce(n.is_default_selected_for_activity, false) as is_default_selected_for_activity,
              coalesce(n.is_data_sharing, false) as is_data_sharing,
              coalesce(n.is_legacy_usage, false) as is_legacy_usage,
              n.legacy_description         as description,
              n.molecular_weight           as molecular_weight,
              n.value_sas_display_format   as sas_display_format,
             CASE
              WHEN (n:FindingValue) THEN 'Findings'
              WHEN (n:InterventionValue) THEN 'Interventions'
              WHEN (n:EventValue) THEN 'Events'
              ELSE 'Other'
             END as general_domain_class,
             CASE
              WHEN (n:NumericFindingValue) THEN 'NumericFinding'
              WHEN (n:CategoricFindingValue) THEN 'CategoricFinding'
              WHEN (n:TextualFindingValue) THEN 'TextualFinding'
              WHEN (n:CompoundDosingValue) THEN 'CompoundDosing'
              ELSE 'Other'
             END as sub_domain_class,
             CASE
              WHEN (n:CompoundValue) THEN 'Compound'
              WHEN (n:LaboratoryActivityValue) THEN 'LaboratoryActivity'
              WHEN (n:RatingScaleValue) THEN 'RatingScale'
              ELSE 'Other'
             END as sub_domain_type
            ORDER BY n.name
                   
              
            """
        match_clause = match_clause + filter_query

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
        )

        if at_specific_date:
            query.parameters.update({"at_specific_date": at_specific_date})
        result_array, attributes_names = query.execute()

        res = (result_array, attributes_names)
        result = utils.db_result_to_list(res)

        total = calculate_total_count_from_query_result(
            len(result), page_number, page_size, total_count
        )
        if total is None:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            total = count_result[0][0] if len(count_result) > 0 else 0

        return GenericFilteringReturn(items=result, total=total)

    def get_cdisc_ct_ver(
        self,
        catalogue_name: str | None = None,
        after_date: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """Query to get the legacy dataset cdisc_ct_ver."""

        match_clause = """
            MATCH (cat:CTCatalogue)-[:CONTAINS_PACKAGE]->(package:CTPackage)
            """
        alias_clause = """
             cat.name as ct_scope, 
             toString(date(package.effective_date)) as ct_ver,
             package.name as pkg_nm
             
            """
        # get filters and update match clause
        filter_statements, filter_query_parameters = self._filter_for_cdisc_ct(
            catalogue_name=catalogue_name, after_date=after_date
        )
        match_clause += filter_statements

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()
        res = (result_array, attributes_names)
        result = utils.db_result_to_list(res)

        total = calculate_total_count_from_query_result(
            len(result), page_number, page_size, total_count
        )
        if total is None:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            total = count_result[0][0] if len(count_result) > 0 else 0

        return GenericFilteringReturn(items=result, total=total)

    def get_cdisc_ct_pkg(
        self,
        catalogue_name: str | None = None,
        after_date: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """Query to get the legacy dataset cdisc_ct_pkg."""

        match_clause = """
               MATCH (cat:CTCatalogue)-[:CONTAINS_PACKAGE]->(package:CTPackage)
               """
        alias_clause = """
            cat.name as pkg_scope,
            package.name as pkg_nm
            """
        # get filters and update match clause
        filter_statements, filter_query_parameters = self._filter_for_cdisc_ct(
            catalogue_name=catalogue_name, after_date=after_date
        )
        match_clause += filter_statements

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()

        res = (result_array, attributes_names)
        result = utils.db_result_to_list(res)

        total = calculate_total_count_from_query_result(
            len(result), page_number, page_size, total_count
        )
        if total is None:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            total = count_result[0][0] if len(count_result) > 0 else 0

        return GenericFilteringReturn(items=result, total=total)

    def get_cdisc_ct_list(
        self,
        catalogue_name: str | None = None,
        package: str | None = None,
        after_date: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """Query to get the legacy dataset cdisc_ct_list."""

        match_clause = """
        
            MATCH (cat:CTCatalogue)-[:CONTAINS_PACKAGE]-> (package:CTPackage)-[:CONTAINS_CODELIST]
            -> (package_codelist:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]
            -> (codelist_attributes_value:CTCodelistAttributesValue)
            """

        alias_clause = """
             
            replace(package_codelist.uid,package.uid+'_','')        as ct_cd_list_cd, 
            CASE codelist_attributes_value.extensible
              WHEN false THEN 'N'
              WHEN true THEN 'Y'
            END                                                         as ct_cd_list_extensible,
            codelist_attributes_value.name                              as ct_cd_list_nm,
            codelist_attributes_value.submission_value                  as ct_cd_list_submval,
            cat.name                                                    as ct_scope,
            toString(date(package.effective_date))                      as ct_ver,
            codelist_attributes_value.definition                        as definition,
            codelist_attributes_value.preferred_term                    as nci_pref_term,
            package.name                                                as pkg_nm,
            apoc.text.join(codelist_attributes_value.synonyms,';')      as synonyms
            """

        # get filters and update match clause
        filter_statements, filter_query_parameters = self._filter_for_cdisc_ct(
            catalogue_name=catalogue_name, package=package, after_date=after_date
        )
        match_clause += filter_statements

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()

        res = (result_array, attributes_names)
        result = utils.db_result_to_list(res)

        total = calculate_total_count_from_query_result(
            len(result), page_number, page_size, total_count
        )
        if total is None:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            total = count_result[0][0] if len(count_result) > 0 else 0

        return GenericFilteringReturn(items=result, total=total)

    def get_cdisc_ct_val(
        self,
        catalogue_name: str | None = None,
        package: str | None = None,
        after_date: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """Query to get the legacy dataset cdisc_ct_val."""
        match_clause = """
            MATCH (cat:CTCatalogue)-[:CONTAINS_PACKAGE]-> (package:CTPackage)-[:CONTAINS_CODELIST]
            -> (package_codelist:CTPackageCodelist)-[:CONTAINS_TERM] -> (pt:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]
            -> (term_attributes_value:CTTermAttributesValue)
            MATCH (package_codelist)-[:CONTAINS_ATTRIBUTES]-> (codelist_attributes_value:CTCodelistAttributesValue)
            MATCH (pt)-[:CONTAINS_SUBMISSION_VALUE]->(codelist_term:CTCodelistTerm)
            //MATCH (codelist_attributes_value)<-[:HAS_VERSION]-(:CTCodelistAttributesRoot)<-[:HAS_ATTRIBUTES_ROOT]-(cl_root:CTCodelistRoot)-[:HAS_TERM]->(codelist_term)
            """

        alias_clause = """

            term_attributes_value.concept_id                    as ct_cd,
            codelist_term.submission_value                      as ct_submval,
            codelist_attributes_value.submission_value          as ct_cd_list_submval,
            cat.name                                            as ct_scope,
            toString(date(package.effective_date))              as ct_ver,
            term_attributes_value.definition                    as definition,
            term_attributes_value.preferred_term                as nci_pref_term,
            package.name                                        as pkg_nm,
            apoc.text.join(term_attributes_value.synonyms,';')  as synonyms

            """

        # get filters and update match clause
        filter_statements, filter_query_parameters = self._filter_for_cdisc_ct(
            catalogue_name=catalogue_name, package=package, after_date=after_date
        )
        match_clause += filter_statements

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()

        res = (result_array, attributes_names)
        result = utils.db_result_to_list(res)

        total = calculate_total_count_from_query_result(
            len(result), page_number, page_size, total_count
        )
        if total is None:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            total = count_result[0][0] if len(count_result) > 0 else 0

        return GenericFilteringReturn(items=result, total=total)

    def get_tv(
        self,
        study_uid,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_value_version:
            query = MATCH_SPECIFIC_STUDY_VERSION
        else:
            query = MATCH_LATEST_STUDY
        query = query + """
        // Query to retrieve TV data from the Study Visit table
        // We are looking for the latest visit name, study day, and study week values associated with a specific study value version or all (latest) study versions.
        // The query filters by domain (TV), selecting the 'StudID', 'VisitNum', 'StudyDayValue' (or 'StudyWeekValue'), 'ArmCD', 'Arm', and any other fields we want to include.
        // We use optional matches for the visit name, day, and week to avoid errors in case these fields are missing. We also add a condition to handle the situation when only one of these fields is present.
        MATCH (sv)-[:HAS_STUDY_VISIT]->(v:StudyVisit)
        OPTIONAL MATCH  (v)-->(nr:VisitNameRoot)-[:LATEST]->(nv:VisitNameValue),
                        (v)-->(dr:StudyDayRoot)-[:LATEST]->(dv:StudyDayValue),
                        (v)-->(wr:StudyWeekRoot)-[:LATEST]->(wv:StudyWeekValue)
        OPTIONAL MATCH (udv:UnitDefinitionValue)-[:LATEST_FINAL]-(udr:UnitDefinitionRoot)--(stf:StudyTimeField {field_name: "soa_preferred_time_unit"}),
            (stf)--(sv)

        RETURN toUpper(sv.study_id_prefix + '-' + sv.study_number) AS STUDYID,
            'TV' AS DOMAIN,
            toInteger(v.unique_visit_number) AS VISITNUM,
            CASE
                // WEEK
                WHEN udv.name = "week" THEN toUpper(nv.name + " (" +udv.name + " "+toInteger(wv.value)+")")
                // DAY
                WHEN udv.name = "day" THEN toUpper(nv.name + " (" +udv.name + " "+toInteger(dv.value)+")")
            ELSE toUpper(nv.name)
            END AS VISIT,
            toInteger(dv.value) AS VISITDY,
            NULL AS ARMCD,
            NULL AS ARM,
            toUpper(v.start_rule) AS TVSTRL,
            toUpper(v.end_rule) AS TVENRL
        ORDER BY v.unique_visit_number;
        """
        result_array = db.cypher_query(
            query=query,
            params={
                "study_uid": str(study_uid),
                "study_value_version": str(study_value_version),
            },
        )

        return utils.db_result_to_list(result_array)

    def get_mdvisit(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_value_version:
            query = MATCH_SPECIFIC_STUDY_VERSION
        else:
            query = MATCH_LATEST_STUDY
        query = query + """
        MATCH (sv)-[:HAS_STUDY_VISIT]->(v:StudyVisit)
        OPTIONAL MATCH  (v)-->(nr:VisitNameRoot)-[:LATEST]->(nv:VisitNameValue)
        OPTIONAL MATCH  (v)-->(dr:StudyDayRoot)-[:LATEST]->(dv:StudyDayValue)
        OPTIONAL MATCH  (v)-->(wr:StudyWeekRoot)-[:LATEST]->(wv:StudyWeekValue)
        OPTIONAL MATCH  (v)-[:HAS_VISIT_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]-(vtnv:CTTermNameValue)
        OPTIONAL MATCH (udv:UnitDefinitionValue)-[:LATEST_FINAL]-(udr:UnitDefinitionRoot)--(stf:StudyTimeField {field_name: "soa_preferred_time_unit"}),
            (stf)--(sv)
        RETURN
            toUpper(sv.study_id_prefix + '-' + sv.study_number) AS STUDYID,
            toInteger(v.unique_visit_number) AS VISIT_NUM,
            toUpper(nv.name) AS VISIT_NAME,
            CASE
                // WEEK
                WHEN udv.name = "week" THEN nv.name + " (" +udv.name + " "+toInteger(wv.value)+")"
                // DAY
                WHEN udv.name = "day" THEN nv.name + " (" +udv.name + " "+toInteger(dv.value)+")"
            ELSE NULL
            END AS AVISIT,
            toInteger(dv.value) AS DAY_VALUE,
            v.short_visit_label as VISIT_SHORT_LABEL,
            dv.name AS DAY_NAME,
            wv.name AS WEEK_NAME,
            toInteger(wv.value) AS WEEK_VALUE,
            vtnv.name as VISIT_TYPE_NAME
        ORDER BY VISIT_NUM;
        """
        result_array = db.cypher_query(
            query=query,
            params={
                "study_uid": str(study_uid),
                "study_value_version": str(study_value_version),
            },
        )

        return utils.db_result_to_list(result_array)

    def get_mdflow(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_value_version:
            query = MATCH_SPECIFIC_STUDY_VERSION
        else:
            query = MATCH_LATEST_STUDY
        query = query + """
        MATCH (sv)--(sact_schedule:StudyActivitySchedule)
        MATCH (sact_schedule)--(v:StudyVisit)--(sv)
        OPTIONAL MATCH (v)-[:HAS_VISIT_TYPE]-(:CTTermRoot)-[:HAS_NAME_ROOT]-(:CTTermNameRoot)-[:LATEST_FINAL]-(ctterm_name_value_visit_type:CTTermNameValue)
            where v.is_global_anchor_visit = True
        OPTIONAL MATCH  (v)-->(nr:VisitNameRoot)-[:LATEST_FINAL]->(nv:VisitNameValue)
        MATCH (sact_schedule)--(sact:StudyActivity)--(sv)
        OPTIONAL MATCH (sact)--(sactins:StudyActivityInstance)--(sv)
        OPTIONAL MATCH (sactins)--(act_inst_value:ActivityInstanceValue)
        OPTIONAL MATCH (act_inst_value)-[:ACTIVITY_INSTANCE_CLASS]-(aicr:ActivityInstanceClassRoot)-[:LATEST_FINAL]-(aicv:ActivityInstanceClassValue)
            WHERE aicv.name = "NumericFinding" 
                OR aicv.name = "CategoricFinding" 
                OR aicv.name = "TextualFinding" 

        OPTIONAL MATCH (act_inst_value:ActivityInstanceValue)--(act_item:ActivityItem)--(unit_definition_root:UnitDefinitionRoot)-[:LATEST]-(unit_definition_value:UnitDefinitionValue)
            WHERE aicv.name = "NumericFinding" 

        OPTIONAL MATCH  (v)-->(dr:StudyDayRoot)-[:LATEST]->(dv:StudyDayValue)
        OPTIONAL MATCH  (v)-->(wr:StudyWeekRoot)-[:LATEST]->(wv:StudyWeekValue)
        OPTIONAL MATCH (udv:UnitDefinitionValue)-[:LATEST_FINAL]-(udr:UnitDefinitionRoot)--(stf:StudyTimeField {field_name: "soa_preferred_time_unit"}),
            (stf)--(sv)
        WITH  toUpper(sv.study_id_prefix + '-' + sv.study_number) AS STUDYID_FLOWCHART,
            v.unique_visit_number AS AVISITN,
            act_inst_value.adam_param_code AS PARAMCD,
            CASE 
                // WEEK
                WHEN udv.name = "week" THEN nv.name + " (" +udv.name + " "+toInteger(wv.value)+")"
                // DAY
                WHEN udv.name = "day" THEN nv.name + " (" +udv.name + " "+toInteger(dv.value)+")"
            ELSE NULL
            END AS AVISIT,
            CASE 
                WHEN (NOT aicv IS NULL) THEN 
                    CASE 
                        WHEN aicv.name = "NumericFinding" AND NOT unit_definition_value IS NULL THEN act_inst_value.adam_param_code+" ("+unit_definition_value.name+")"
                    ELSE act_inst_value.adam_param_code
                    END
                ELSE NULL
            END AS PARAM,
            sact.order AS PARAMN,
            NULL AS ATPTN,
            NULL AS ATPT,
            act_inst_value.topic_code AS TOPICCD,
            CASE 
                WHEN v.is_global_anchor_visit THEN ctterm_name_value_visit_type.name 
                ELSE NULL
            END AS BASETYPE,
            CASE
                WHEN v.is_global_anchor_visit THEN "Y"
                ELSE NULL
            END AS ABLFL,
            ctterm_name_value_visit_type.name AS ASSMTYPE
        RETURN distinct  STUDYID_FLOWCHART,
            AVISITN,
            PARAMCD,
            AVISIT,
            PARAM,
            PARAMN,
            ATPTN,
            ATPT,
            TOPICCD,
            BASETYPE,
            ABLFL,
            ASSMTYPE
        ORDER BY STUDYID_FLOWCHART, AVISITN, PARAMN;
        """
        result_array = db.cypher_query(
            query=query,
            params={
                "study_uid": str(study_uid),
                "study_value_version": str(study_value_version),
            },
        )

        return utils.db_result_to_list(result_array)

    def get_mdendpnt(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_value_version:
            query = "MATCH (s_r:StudyRoot {uid: $study_uid})-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]->(s_v:StudyValue) "
        else:
            query = (
                "MATCH (s_r:StudyRoot {uid: $study_uid})-[:LATEST]->(s_v:StudyValue)"
            )
        query = query + """
        MATCH (s_v)-[:HAS_STUDY_OBJECTIVE]-(s_obj:StudyObjective)
        // fetch objective data
        OPTIONAL MATCH (s_obj)-[:HAS_OBJECTIVE_LEVEL]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(obj_lev:CTTermNameValue)
        OPTIONAL MATCH (s_obj)-[:HAS_SELECTED_OBJECTIVE]->(obj_val:ObjectiveValue)<--(obj_roo:ObjectiveRoot)
        OPTIONAL MATCH (s_obj)<-[:STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE]-(s_end:StudyEndpoint)<-[:HAS_STUDY_ENDPOINT]-(s_v)
        // fetch endpoint data
        OPTIONAL MATCH (s_end)-[:HAS_ENDPOINT_LEVEL]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(end_lev:CTTermNameValue)
        OPTIONAL MATCH (s_end)-[:HAS_ENDPOINT_SUB_LEVEL]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(end_sublev:CTTermNameValue)
        OPTIONAL MATCH (s_end)-[:HAS_SELECTED_ENDPOINT]->(end_val:EndpointValue)<--(end_roo:EndpointRoot)
        OPTIONAL MATCH (s_end)-[:HAS_UNIT]->(:UnitDefinitionRoot)-[:LATEST]->(uni_value:UnitDefinitionValue)-[:HAS_CT_UNIT]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(uni_ctt_roo:CTTermRoot)
        OPTIONAL MATCH (s_end)-[:HAS_SELECTED_TIMEFRAME]->(tim_fra_val:TimeframeValue)<--(tim_fra_roo:TimeframeRoot)
        // fetch any Activities instantiated in ObjectiveTemplate or EndpointTemplate
        OPTIONAL MATCH (study_end_obj)-[:HAS_SELECTED_ENDPOINT|HAS_SELECTED_OBJECTIVE|HAS_SELECTED_TIMEFRAME]->(:SyntaxInstanceValue)-[:USES_VALUE]->(activity_tem_par_root)<-[:HAS_PARAMETER_TERM]-(t:TemplateParameter)
            WHERE t.name IN ["Activity"] AND (study_end_obj = s_obj OR study_end_obj = s_end)
        OPTIONAL MATCH (study_end_obj2)-[:HAS_SELECTED_ENDPOINT|HAS_SELECTED_OBJECTIVE|HAS_SELECTED_TIMEFRAME]->(:SyntaxInstanceValue)-[:USES_VALUE]->(activity_subgroup_tem_par_root)<-[:HAS_PARAMETER_TERM]-(t2:TemplateParameter)
            WHERE t2.name IN ['ActivitySubGroup'] AND (study_end_obj2 = s_obj OR study_end_obj2 = s_end)
        OPTIONAL MATCH (study_end_obj3)-[:HAS_SELECTED_ENDPOINT|HAS_SELECTED_OBJECTIVE|HAS_SELECTED_TIMEFRAME]->(:SyntaxInstanceValue)-[:USES_VALUE]->(activity_group_tem_par_root)<-[:HAS_PARAMETER_TERM]-(t3:TemplateParameter)
            WHERE t3.name IN [ "ActivityGroup"] AND (study_end_obj3 = s_obj OR study_end_obj3 = s_end)
        OPTIONAL MATCH (study_end_obj4)-[:HAS_SELECTED_ENDPOINT|HAS_SELECTED_OBJECTIVE|HAS_SELECTED_TIMEFRAME]->(:SyntaxInstanceValue)-[:USES_VALUE]->(activity_instance_tem_par_root)<-[:HAS_PARAMETER_TERM]-(t4:TemplateParameter)
            WHERE t4.name IN ['ActivityInstance'] AND (study_end_obj4 = s_obj OR study_end_obj4 = s_end)
        OPTIONAL MATCH (activity_tem_par_root)-[:LATEST]->(activity_tem_par_value)
        OPTIONAL MATCH (activity_subgroup_tem_par_root)-[:LATEST]->(activity_subgroup_tem_par_value)
        OPTIONAL MATCH (activity_group_tem_par_root)-[:LATEST]->(activity_group_tem_par_value)
        OPTIONAL MATCH (activity_instance_tem_par_root)-[:LATEST]->(activity_instance_tem_par_value)
        WITH 
            s_r, 
            s_v, 
            s_obj, 
            obj_lev,
            obj_val,
            obj_roo,
            s_end,
            end_lev,
            end_sublev,
            end_val,
            end_roo,
            uni_value,
            uni_ctt_roo,
            tim_fra_val,
            tim_fra_roo,
            COLLECT(DISTINCT activity_tem_par_value.name) as activity_tem_par_root_uid_collected,
            COLLECT(DISTINCT activity_subgroup_tem_par_value.name) as activity_subgroup_tem_par_root_uid_collected,
            COLLECT(DISTINCT activity_group_tem_par_value.name) as activity_group_tem_par_root_uid_collected,
            COLLECT(DISTINCT activity_instance_tem_par_value.name) as activity_instance_tem_par_root_uid_collected
        return 
            DISTINCT s_r.uid as STUDYID_OBJ, 
            obj_lev.name AS OBJTVLVL,
            obj_val.name AS OBJTV,
            obj_val.name_plain AS OBJTVPT,
            end_lev.name AS ENDPNTLVL,
            end_sublev.name AS ENDPNTSL,
            end_val.name AS  ENDPNT, 
            end_val.name_plain AS ENDPNTPT, 
            uni_value.definition AS UNITDEF,
            uni_ctt_roo.uid AS UNIT,
            tim_fra_val.name AS TMFRM,
            tim_fra_val.name_plain AS TMFRMPT,
            activity_tem_par_root_uid_collected AS RACT,
            activity_subgroup_tem_par_root_uid_collected AS RACTSGRP,
            activity_group_tem_par_root_uid_collected AS RACTGRP,
            activity_instance_tem_par_root_uid_collected AS RACTINST
        ORDER BY STUDYID_OBJ, OBJTV, ENDPNT, TMFRM
        """
        result_array = db.cypher_query(
            query=query,
            params={
                "study_uid": str(study_uid),
                "study_value_version": str(study_value_version),
            },
        )

        return utils.db_result_to_list(result_array)

    def get_ta(
        self,
        study_uid,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_value_version:
            query = MATCH_SPECIFIC_STUDY_VERSION
        else:
            query = MATCH_LATEST_STUDY
        query = query + """
        MATCH (sv)-[:HAS_STUDY_ELEMENT]->(se:StudyElement)
        CALL 
            {
            WITH sv, se
            MATCH (se)-[:STUDY_ELEMENT_HAS_DESIGN_CELL]-(sd:StudyDesignCell)-[:HAS_STUDY_DESIGN_CELL]-(sv),
            (sd)-[:STUDY_EPOCH_HAS_DESIGN_CELL]-(sep:StudyEpoch)-[:HAS_STUDY_EPOCH]-(sv),
            (sv) -[:HAS_STUDY_ARM] -(sar:StudyArm)-[:STUDY_ARM_HAS_DESIGN_CELL]-(sd)
            OPTIONAL MATCH (sv) -[:HAS_STUDY_BRANCH_ARM]-(sba:StudyBranchArm)-[:STUDY_BRANCH_ARM_HAS_DESIGN_CELL] -(sd)
            OPTIONAL MATCH (sep) - [:HAS_EPOCH] - (:CTTermContext) - [:HAS_SELECTED_TERM] - (:CTTermRoot) - [:HAS_NAME_ROOT] - (:CTTermNameRoot) -[:LATEST]- (sep_term:CTTermNameValue)
            RETURN toUpper(sv.study_id_prefix + '-' + sv.study_number) AS STUDYID,
                'TA' AS DOMAIN,
                se.name AS ELEMENT,
                se.order AS ETCD,
                sep.order as TAETORD,
                sd.transition_rule AS TATRANS,
                sep_term.name AS EPOCH,
                sar.name AS ARM,
                CASE  
                    WHEN sba.branch_arm_code IS NULL THEN sar.arm_code  
                    ELSE sar.arm_code+'-'+ sba.branch_arm_code 
                END AS ARMCD,
                sba.name AS TABRANCH
                ORDER BY sar.order, sep.order
            union all
            WITH sv, se
            MATCH (se)-[:STUDY_ELEMENT_HAS_DESIGN_CELL]-(sd:StudyDesignCell)-[:HAS_STUDY_DESIGN_CELL]-(sv),
            (sd)-[:STUDY_EPOCH_HAS_DESIGN_CELL]-(sep:StudyEpoch)-[:HAS_STUDY_EPOCH]-(sv),
            (sv) -[:HAS_STUDY_BRANCH_ARM]-(sba:StudyBranchArm)-[:STUDY_BRANCH_ARM_HAS_DESIGN_CELL] -(sd),
            (sba)-[:STUDY_ARM_HAS_BRANCH_ARM]-(sar:StudyArm)-[:HAS_STUDY_ARM]-(sv)
            OPTIONAL MATCH (sep) - [:HAS_EPOCH] - (:CTTermContext) - [:HAS_SELECTED_TERM] - (:CTTermRoot) - [:HAS_NAME_ROOT] - (:CTTermNameRoot) -[:LATEST]- (sep_term:CTTermNameValue)
            RETURN toUpper(sv.study_id_prefix + '-' + sv.study_number) AS STUDYID,
                'TA' AS DOMAIN,
                se.name AS ELEMENT,
                se.order AS ETCD,
                sep.order as TAETORD,
                sd.transition_rule AS TATRANS,
                sep_term.name AS EPOCH,
                sar.name AS ARM,
                CASE 
                    WHEN sba.branch_arm_code IS NULL THEN sar.arm_code  
                    ELSE sar.arm_code+'-'+ sba.branch_arm_code 
                END AS ARMCD,
                sba.name AS TABRANCH
        }
        RETURN 
            STUDYID,
            DOMAIN,
            ELEMENT,
            ETCD,
            TAETORD,
            TATRANS,
            EPOCH,
            ARM, 
            ARMCD,
            TABRANCH
        ORDER BY ARMCD, TAETORD
            


        """
        result_array = db.cypher_query(
            query=query,
            params={
                "study_uid": str(study_uid),
                "study_value_version": str(study_value_version),
            },
        )

        return utils.db_result_to_list(result_array)

    def get_ti(
        self,
        study_uid,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_value_version:
            query = MATCH_SPECIFIC_STUDY_VERSION
        else:
            query = MATCH_LATEST_STUDY
        query = query + """
        MATCH (sv)-->(sc:StudyCriteria)
        MATCH (sc)-->(cv:CriteriaValue)<-[:LATEST]-(cr:CriteriaRoot)<--(ctr:CriteriaTemplateRoot)-[:HAS_TYPE]->(ctx:CTTermContext)-[:HAS_SELECTED_TERM]->(tr:CTTermRoot)-->(atr:CTTermAttributesRoot)-[:LATEST]->(atv:CTTermAttributesValue)
        WHERE atv.concept_id = 'C25532' or atv.concept_id = 'C25370'
        MATCH (ctx)-[:HAS_SELECTED_CODELIST]->(clr:CTCodelistRoot)-[ht:HAS_TERM]-(clterm:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr)
        RETURN  toUpper(sv.study_id_prefix) + '-' + toUpper(sv.study_number) AS STUDYID,
                'TI' AS DOMAIN,
                TOUPPER(substring(clterm.submission_value,0,1)) + toInteger(sc.order) AS IETESTCD,
                cv.name_plain AS IETEST,
                clterm.submission_value AS IECAT,
                '' AS IESCAT,
                '' AS TIRL,
                '' AS TIVERS
        ORDER BY IETESTCD;
        """
        result_array = db.cypher_query(
            query=query,
            params={
                "study_uid": str(study_uid),
                "study_value_version": str(study_value_version),
            },
        )

        return utils.db_result_to_list(result_array)

    def get_ts(
        self,
        study_uid,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_value_version:
            query = MATCH_SPECIFIC_STUDY_VERSION
        else:
            query = MATCH_LATEST_STUDY

        reg_field_names, reg_case_lines = _build_registry_identifier_cypher_fragment()

        query = query + f"""
        WITH sr, sv
        CALL (sr, sv) {{
        // --- Field-based TS parameters (driven by CTTermNameValue → MetaStudyField graph) ---
        MATCH (ts_term:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST_FINAL]->(tsp:CTTermNameValue)
        MATCH (tsp)-[:RELATED_STUDY_FIELD_SELECTION]->(msf:MetaStudyField)
        MATCH (:CTCodelistRoot {{uid:'{settings.ts_parmcd_codelist_uid}'}})-[:HAS_TERM]->(cclt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(ts_term)
        MATCH (:CTCodelistRoot {{uid:'{settings.ts_parm_codelist_uid}'}})-[:HAS_TERM]->(nclt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(ts_term)
        // Resolve the actual StudyField value for this study.
        // Regular fields match by msf.osb_field_name; Other Study Attributes
        // (which share one MetaStudyField per data type) match by tsp.name.
        OPTIONAL MATCH (sv)-->(sf:StudyField)
            WHERE sf.field_name = msf.osb_field_name
               OR (msf.osb_page_reference = '{settings.study_other_attributes_page_reference}'
                   AND sf.field_name = tsp.name
                   AND (sf)-[:HAS_META_STUDY_FIELD]->(msf))
        OPTIONAL MATCH (sf)-->(:CTTermContext)-[:HAS_SELECTED_TERM]->(ctr:CTTermRoot)-->
            (ctar:CTTermAttributesRoot)-[:LATEST_FINAL]->(ctav:CTTermAttributesValue)
        OPTIONAL MATCH (ctr)-->(ctnr:CTTermNameRoot)-[:LATEST_FINAL]->(ctnv:CTTermNameValue)
        OPTIONAL MATCH (sf)-->(dtr:DictionaryTermRoot)-->(dtv:DictionaryTermValue)
        OPTIONAL MATCH (sf)-[:HAS_REASON_FOR_NULL_VALUE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(ct_null:CTTermRoot{{uid:'{settings.ct_uid_na_value}'}})
        OPTIONAL MATCH (sf)-[:HAS_REASON_FOR_NULL_VALUE]->(pinf_ctx:CTTermContext)-[:HAS_SELECTED_TERM]->(ct_pinf:CTTermRoot)
        WHERE (pinf_ctx)-[:HAS_SELECTED_CODELIST]->(:CTCodelistRoot)-[:HAS_TERM]->
            (:CTCodelistTerm {{submission_value:'{settings.ct_submval_positive_infinity}'}})-[:HAS_TERM_ROOT]->(ctr)
        RETURN DISTINCT
            sv.study_id_prefix+'-'+sv.study_number AS STUDYID,
            'TS' AS DOMAIN,
            cclt.submission_value AS TSPARMCD,
            nclt.submission_value AS TSPARM,
            CASE
                WHEN tsp.reference IS NOT NULL THEN tsp.reference
                WHEN sf:StudyTimeField THEN 'Not Controlled TimeField'
                WHEN sf:StudyIntField THEN 'Not Controlled IntField'
                WHEN ctr IS NOT NULL THEN 'CDISC'
                WHEN dtr IS NOT NULL THEN 'Dictionary'
                ELSE 'Not Controlled'
            END AS controlled_by,
            CASE
                WHEN ctnv IS NOT NULL THEN ctnv.name
                WHEN ctr IS NOT NULL AND ct_null IS NULL THEN ctav.concept_id
                WHEN dtr IS NOT NULL THEN dtv.name
                WHEN sf IS NOT NULL AND sf.value = [] THEN NULL
                WHEN sf IS NOT NULL THEN sf.value
                ELSE NULL
            END AS TSVAL,
            CASE
                WHEN ct_null IS NOT NULL THEN 'NA'
                WHEN sf:StudyTimeField AND ct_pinf IS NOT NULL THEN 'PINF'
                ELSE ''
            END AS TSVALNF,
            CASE
                WHEN ctr IS NOT NULL AND ct_null IS NULL THEN ctav.concept_id
                WHEN dtr IS NOT NULL THEN dtv.dictionary_id
                ELSE ''
            END AS TSVALCD,
            CASE
                WHEN tsp.reference IS NOT NULL THEN tsp.reference
                WHEN sf:StudyTimeField THEN 'ISO8601'
                WHEN ctr IS NOT NULL AND ct_null IS NULL THEN 'CDISC'
                WHEN dtr IS NOT NULL THEN head([(library:Library)-[:CONTAINS_DICTIONARY_TERM]->(dtr) | library.name])
                ELSE ''
            END AS TSVCDREF,
            '' AS TSVCDVER

        UNION
        // --- Registry Identifiers ---
        // Registry identifier fields (StudyTextField) all share the REGID TS parameter code.
        // Each filled registry field produces its own row; field names and TSVCDREF
        // are driven by FieldConfiguration.registry_identifier_vcdref_map().
        WITH sr, sv
        MATCH (:CTCodelistRoot {{uid:'{settings.ts_parmcd_codelist_uid}'}})-[:HAS_TERM]->(regid_cclt:CTCodelistTerm {{submission_value:'{TS_REGID_SUBMVAL}'}})-[:HAS_TERM_ROOT]->(regid_term:CTTermRoot)
        MATCH (:CTCodelistRoot {{uid:'{settings.ts_parm_codelist_uid}'}})-[:HAS_TERM]->(regid_nclt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(regid_term)
        MATCH (sv)-->(sf:StudyTextField)
        WHERE sf.field_name IN [{reg_field_names}] AND sf.value IS NOT NULL AND sf.value <> ''
        RETURN DISTINCT
            sv.study_id_prefix+'-'+sv.study_number AS STUDYID,
            'TS' AS DOMAIN,
            regid_cclt.submission_value AS TSPARMCD,
            regid_nclt.submission_value AS TSPARM,
            CASE sf.field_name
                {reg_case_lines}
                ELSE ''
            END AS controlled_by,
            sf.value AS TSVAL,
            '' AS TSVALNF,
            '' AS TSVALCD,
            CASE sf.field_name
                {reg_case_lines}
                ELSE ''
            END AS TSVCDREF,
            '' AS TSVCDVER

        UNION
        // --- Study Objectives ---
        WITH sr, sv
        MATCH (sv)-[:HAS_STUDY_OBJECTIVE]->(so:StudyObjective)-[:HAS_OBJECTIVE_LEVEL]->(ctx:CTTermContext)-[:HAS_SELECTED_TERM]->(objlv)-->(octar:CTTermAttributesRoot)-[:LATEST_FINAL]->(octav:CTTermAttributesValue)
        MATCH (ctx)-[:HAS_SELECTED_CODELIST]->(clr:CTCodelistRoot)-[:HAS_TERM]-(cclt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(objlv)
        MATCH (objlv)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST_FINAL]->(objav:CTTermAttributesValue)
        MATCH (so)-[:HAS_SELECTED_OBJECTIVE]->(obj)
        RETURN
        sv.study_id_prefix+'-'+sv.study_number AS STUDYID,
        'TS' AS DOMAIN,
        cclt.submission_value AS TSPARMCD,
        objav.preferred_term AS TSPARM,
        '' AS controlled_by,
        obj.name_plain AS TSVAL,
        '' AS TSVALNF,
        '' AS TSVALCD,
        '' AS TSVCDREF,
        '' AS TSVCDVER

        UNION
        // --- Study Endpoints ---
        WITH sr, sv
        MATCH (sv)-[:HAS_STUDY_ENDPOINT]->(send)-[:HAS_ENDPOINT_LEVEL]->(ctx:CTTermContext)-[:HAS_SELECTED_TERM]->(endplv)-->(ectar:CTTermAttributesRoot)-[:LATEST_FINAL]->(ectav:CTTermAttributesValue)
        MATCH (ctx)-[:HAS_SELECTED_CODELIST]->(clr:CTCodelistRoot)-[:HAS_TERM]-(cclt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(endplv)
        MATCH (endplv)-[:HAS_ATTRIBUTES_ROOT]->(:CTTermAttributesRoot)-[:LATEST_FINAL]->(ebjav:CTTermAttributesValue)
        MATCH (send)-[:HAS_SELECTED_TIMEFRAME]->(tf:TimeframeValue)
        MATCH (send)-[:HAS_SELECTED_ENDPOINT]->(endp:EndpointValue)
        OPTIONAL MATCH (send)-[:HAS_ENDPOINT_SUB_LEVEL]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(end_sublev:CTTermNameValue)
        OPTIONAL MATCH (send)-[:HAS_SELECTED_ENDPOINT]->(end_val:EndpointValue)<--(end_roo:EndpointRoot)
        OPTIONAL MATCH (send)-[:HAS_UNIT]->(:UnitDefinitionRoot)-[:LATEST]->(uni_value:UnitDefinitionValue)-[:HAS_CT_UNIT]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(uni_ctt_roo:CTTermRoot)
        OPTIONAL MATCH (send)-[:HAS_SELECTED_TIMEFRAME]->(tim_fra_val:TimeframeValue)<--(tim_fra_roo:TimeframeRoot)
        CALL (send) {{
                OPTIONAL MATCH (send)-[:HAS_UNIT]->(:UnitDefinitionRoot)-[:LATEST]->(uni_value:UnitDefinitionValue)-[:HAS_CT_UNIT]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(uni_ctt_roo:CTTermRoot)
                OPTIONAL MATCH (send)-[:HAS_CONJUNCTION]->(con:Conjunction)
                WITH distinct send,collect(distinct uni_value.name) as units,
                CASE
                        WHEN con IS NULL THEN ", "
                        ELSE " "+con.string +" "
                end as con_string,
                CASE
                        WHEN uni_value IS NULL THEN ["",""]
                        ELSE [" (",")."]
                end as units_space
                RETURN send as send_uax, units_space[0]+ apoc.text.join([i IN units | toString(i)], con_string) + units_space[1] as unit_str
        }}
        RETURN
        DISTINCT sv.study_id_prefix+'-'+sv.study_number AS STUDYID,
        'TS' AS DOMAIN,
        cclt.submission_value AS TSPARMCD,
        ebjav.preferred_term AS TSPARM,
        '' AS controlled_by,
        endp.name_plain + unit_str +' Time frame: ' + tf.name_plain + '.'AS TSVAL,
        '' AS TSVALNF,
        '' AS TSVALCD,
        '' AS TSVCDREF,
        '' AS TSVCDVER

        UNION
        // --- Cohort count ---
        WITH sr, sv
        MATCH (sv)-[:HAS_STUDY_COHORT]->(sch:StudyCohort)
        MATCH (tr:CTTermRoot {{uid:'{TS_COHORT_COUNT_TERM_UID}'}})-->(tar:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav:CTTermAttributesValue)
        MATCH (:CTCodelistRoot {{uid:'{settings.ts_parmcd_codelist_uid}'}})-[:HAS_TERM]->(cclt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr)
        MATCH (:CTCodelistRoot {{uid:'{settings.ts_parm_codelist_uid}'}})-[:HAS_TERM]->(nclt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr)
        RETURN
            sv.study_id_prefix+'-'+sv.study_number AS STUDYID,
            'TS' AS DOMAIN,
            cclt.submission_value AS TSPARMCD,
            nclt.submission_value AS TSPARM,
            '' AS controlled_by,
            count(sch) AS TSVAL,
            '' AS TSVALNF,
            '' AS TSVALCD,
            '' AS TSVCDREF,
            '' AS TSVCDVER

        UNION
        // --- Arm count (from design cells) ---
        WITH sr, sv
        CALL
            {{
            WITH sr, sv
            WITH sr as inner_sr, sv as innver_sv
            MATCH (innver_sv)-[:HAS_STUDY_ELEMENT]->(se:StudyElement),
            (se)-[:STUDY_ELEMENT_HAS_DESIGN_CELL]-(sd:StudyDesignCell)-[:HAS_STUDY_DESIGN_CELL]-(innver_sv),
            (sd)-[:STUDY_EPOCH_HAS_DESIGN_CELL]-(sep:StudyEpoch)-[:HAS_STUDY_EPOCH]-(innver_sv),
            (innver_sv) -[:HAS_STUDY_ARM] -(sar:StudyArm)-[:STUDY_ARM_HAS_DESIGN_CELL]-(sd)
            OPTIONAL MATCH (innver_sv) -[:HAS_STUDY_BRANCH_ARM]-(sba:StudyBranchArm)-[:STUDY_BRANCH_ARM_HAS_DESIGN_CELL] -(sd)
            OPTIONAL MATCH (sep)-[:HAS_EPOCH]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]-(:CTTermNameRoot)-[:LATEST]->(sep_term:CTTermNameValue)
            MATCH (tr:CTTermRoot {{uid:'{TS_ARM_COUNT_TERM_UID}'}})-->(tar:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav:CTTermAttributesValue)
            MATCH (:CTCodelistRoot {{uid:'{settings.ts_parmcd_codelist_uid}'}})-[:HAS_TERM]->(cclt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr)
            MATCH (:CTCodelistRoot {{uid:'{settings.ts_parm_codelist_uid}'}})-[:HAS_TERM]->(nclt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr)
            RETURN distinct inner_sr,innver_sv, sar,sba, tav, cclt, nclt
            union all
            WITH sr, sv
            WITH sr as inner_sr, sv as innver_sv
            MATCH (innver_sv)-[:HAS_STUDY_ELEMENT]->(se:StudyElement),
            (se)-[:STUDY_ELEMENT_HAS_DESIGN_CELL]-(sd:StudyDesignCell)-[:HAS_STUDY_DESIGN_CELL]-(innver_sv),
            (sd)-[:STUDY_EPOCH_HAS_DESIGN_CELL]-(sep:StudyEpoch)-[:HAS_STUDY_EPOCH]-(innver_sv),
            (innver_sv) -[:HAS_STUDY_BRANCH_ARM]-(sba:StudyBranchArm)-[:STUDY_BRANCH_ARM_HAS_DESIGN_CELL] -(sd),
            (sba)-[:STUDY_ARM_HAS_BRANCH_ARM]-(sar:StudyArm)-[:HAS_STUDY_ARM]-(innver_sv)
            OPTIONAL MATCH (sep)-[:HAS_EPOCH]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]-(:CTTermNameRoot)-[:LATEST]-(sep_term:CTTermNameValue)
            MATCH (tr:CTTermRoot {{uid:'{TS_ARM_COUNT_TERM_UID}'}})-->(tar:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav:CTTermAttributesValue)
            MATCH (:CTCodelistRoot {{uid:'{settings.ts_parmcd_codelist_uid}'}})-[:HAS_TERM]->(cclt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr)
            MATCH (:CTCodelistRoot {{uid:'{settings.ts_parm_codelist_uid}'}})-[:HAS_TERM]->(nclt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr)
            RETURN distinct inner_sr,innver_sv, sar,sba, tav, cclt, nclt
            }}
        with   tav, inner_sr, innver_sv, count(*) as counter, cclt, nclt
        return
            innver_sv.study_id_prefix+'-'+innver_sv.study_number AS STUDYID,
            'TS' AS DOMAIN,
            cclt.submission_value AS TSPARMCD,
            nclt.submission_value AS TSPARM,
            '' AS controlled_by,
            counter AS TSVAL,
            '' AS TSVALNF,
            '' AS TSVALCD,
            '' AS TSVCDREF,
            '' AS TSVCDVER

        UNION
        // --- Compound (type of treatment → UNII) ---
            WITH sr, sv
            MATCH (sv)-[:HAS_STUDY_COMPOUND]->(sc:StudyCompound)-[:HAS_TYPE_OF_TREATMENT]->(ctx:CTTermContext)-[:HAS_SELECTED_TERM]->(cttr:CTTermRoot)
            -[:HAS_ATTRIBUTES_ROOT]->(ctar:CTTermAttributesRoot)-[:LATEST_FINAL]->(ctav:CTTermAttributesValue)
            MATCH (ctx)-[:HAS_SELECTED_CODELIST]->(clr:CTCodelistRoot)-[:HAS_TERM]-(cclt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(endplv)
            OPTIONAL MATCH (clr)<-[:PAIRED_CODE_CODELIST]-(nclr:CTCodelistRoot)-[:HAS_TERM]->(nclt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(endplv)
            MATCH (sc)-[:HAS_SELECTED_COMPOUND]->(cav:CompoundAliasValue)-[:IS_COMPOUND]->(cr:CompoundRoot)-[:LATEST_FINAL]->(cv:CompoundValue)
            -[:HAS_UNII_VALUE]->(uniir:UNIITermRoot)-[:LATEST_FINAL]->(uniiv:UNIITermValue)
            MATCH (uniir)<-[:CONTAINS_DICTIONARY_TERM]-(lib:Library)
            with sv,uniiv,lib,ctav, cclt, nclt
            RETURN
                sv.study_id_prefix+'-'+sv.study_number as STUDYID,
                'TS' as DOMAIN,
                cclt.submission_value as TSPARMCD,
                nclt.submission_value as TSPARM,
                '' AS controlled_by,
                uniiv.name as TSVAL,
                '' AS TSVALNF,
                uniiv.dictionary_id as TSVALCD,
                lib.name as TSVCDREF,
                '' AS TSVCDVER

        UNION
        // --- Pharmacological class (from investigational products) ---
            WITH sr, sv
            match (sv)-[:HAS_STUDY_COMPOUND]->(sc:StudyCompound)-[:HAS_TYPE_OF_TREATMENT]->(ctx:CTTermContext)-[:HAS_SELECTED_TERM]->(cttr:CTTermRoot)
            WHERE (ctx)-[:HAS_SELECTED_CODELIST]->(:CTCodelistRoot)-[:HAS_TERM]-(:CTCodelistTerm {{submission_value:'INVESTIGATIONAL PRODUCT TYPE OF TREATMENT'}})-[:HAS_TERM_ROOT]->(cttr)
            WITH sr, sc, sv
            match (sc)-[:HAS_SELECTED_COMPOUND]->(cav:CompoundAliasValue)
            match (cav)-[:IS_COMPOUND]->(cr:CompoundRoot)-[:LATEST_FINAL]->(cv:CompoundValue)-[:HAS_UNII_VALUE]->
              (uniir:UNIITermRoot)-[:LATEST_FINAL]->(uniiv:UNIITermValue)-[:HAS_PCLASS]->(pclass_root:DictionaryTermRoot)-[:LATEST_FINAL]->(medrt:DictionaryTermValue)
            match (pclass_root)<-[:CONTAINS_DICTIONARY_TERM]-(lib:Library)
            match (tr:CTTermRoot {{uid:'{TS_PHARMA_CLASS_TERM_UID}'}})-->(tar:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav:CTTermAttributesValue)
            MATCH (:CTCodelistRoot {{uid:'{settings.ts_parmcd_codelist_uid}'}})-[:HAS_TERM]->(cclt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr)
            MATCH (:CTCodelistRoot {{uid:'{settings.ts_parm_codelist_uid}'}})-[:HAS_TERM]->(nclt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr)
            RETURN sv.study_id_prefix+'-'+sv.study_number as STUDYID,
                'TS' as DOMAIN,
                cclt.submission_value as TSPARMCD,
                nclt.submission_value as TSPARM,
                '' AS controlled_by,
                medrt.name as TSVAL,
                '' AS TSVALNF,
                medrt.dictionary_id as TSVALCD,
                lib.name as TSVCDREF,
                '' AS TSVCDVER

        UNION
        // --- Randomization quotient ---
            WITH sr, sv
            match (:CTTermRoot{{uid : 'C49488'}})<-[:HAS_SELECTED_TERM]-(:CTTermContext)<-[:HAS_TYPE]-(sf:StudyField {{ field_name : 'is_trial_randomised'}}),
            (sf)-[:HAS_BOOLEAN_FIELD]-(sv)
            match (init_arms:StudyArm)-[:HAS_STUDY_ARM]-(sv)
            with distinct init_arms, sv
            with count( init_arms) as counter_arms,  sum( init_arms.number_of_subjects) as all_num_sub, sv
            where counter_arms>1
            with all_num_sub, sv
            call{{
                with sv
                match (inv_arms:StudyArm)-[:HAS_STUDY_ARM]-(sv)
                match (inv_arms)-[:HAS_ARM_TYPE]->(st:CTTermContext)-[:HAS_SELECTED_TERM]->
                  (:CTTermRoot)-[:HAS_NAME_ROOT]-(:CTTermNameRoot)-[:LATEST_FINAL]-(:CTTermNameValue{{name:"Investigational Arm"}})
                with collect(distinct inv_arms) as collected_inv_arms
                unwind collected_inv_arms as unwind_inv_arms
                with sum( unwind_inv_arms.number_of_subjects) as inv_num_sub
                return inv_num_sub
            }}
            with all_num_sub, inv_num_sub, sv
            with
            case all_num_sub
                when 0 then 'NA'
                else round(toFloat(inv_num_sub)/all_num_sub,4)
            end as rand_quotient, sv
            match (tr:CTTermRoot {{uid:'{TS_RANDOMIZATION_QUOTIENT_TERM_UID}'}})-->(tar:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav:CTTermAttributesValue)
            MATCH (:CTCodelistRoot {{uid:'{settings.ts_parmcd_codelist_uid}'}})-[:HAS_TERM]->(cclt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr)
            MATCH (:CTCodelistRoot {{uid:'{settings.ts_parm_codelist_uid}'}})-[:HAS_TERM]->(nclt:CTCodelistTerm)-[:HAS_TERM_ROOT]->(tr)
            with tav, rand_quotient, sv, cclt, nclt
            RETURN
                sv.study_id_prefix+'-'+sv.study_number as STUDYID,
                'TS' as DOMAIN,
                cclt.submission_value as TSPARMCD,
                nclt.submission_value as TSPARM,
                '' AS controlled_by,
                rand_quotient as TSVAL,
                '' AS TSVALNF,
                '' as TSVALCD,
                '' as TSVCDREF,
                '' AS TSVCDVER

        }}
        WITH *
        WHERE TSVAL IS NOT NULL
        RETURN *
        ORDER BY TSPARMCD
        """
        result_array = db.cypher_query(
            query=query,
            params={
                "study_uid": str(study_uid),
                "study_value_version": str(study_value_version),
            },
        )

        return utils.db_result_to_list(result_array)

    def get_te(
        self,
        study_uid,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_value_version:
            query = MATCH_SPECIFIC_STUDY_VERSION
        else:
            query = MATCH_LATEST_STUDY
        query = query + """
        MATCH (sv)-[:HAS_STUDY_ELEMENT]->(se:StudyElement)
        RETURN 
            toUpper(sv.study_id_prefix + '-' + sv.study_number) AS STUDYID,
            'TE' AS DOMAIN,
            se.uid,
            se.order AS ETCD,
            se.name AS ELEMENT,
            se.start_rule AS TESTRL,
            se.end_rule AS TEENRL,
            se.planned_duration AS TEDUR
            ORDER BY se.order
        """
        result_array = db.cypher_query(
            query=query,
            params={
                "study_uid": str(study_uid),
                "study_value_version": str(study_value_version),
            },
        )
        return utils.db_result_to_list(result_array)

    def get_tdm(
        self,
        study_uid,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_value_version:
            query = MATCH_SPECIFIC_STUDY_VERSION
        else:
            query = MATCH_LATEST_STUDY
        query = query + """
        MATCH (sv)-[:HAS_STUDY_DISEASE_MILESTONE]->(sdm:StudyDiseaseMilestone)
        MATCH (sdm)-[:HAS_DISEASE_MILESTONE_TYPE]-(:CTTermContext)-[:HAS_SELECTED_TERM]->(tr:CTTermRoot)-[:HAS_NAME_ROOT]-(:CTTermNameRoot)-[:LATEST]-(sdm_term:CTTermNameValue)
        MATCH (tr)-[HAS_ATTRIBUTES_ROOT]->(CTTermAttributesRoot)-[LATEST]->(ctav:CTTermAttributesValue)
        RETURN DISTINCT toUpper(sv.study_id_prefix + '-' + sv.study_number) AS STUDYID,
            'TM' AS DOMAIN,
            sdm_term.name AS MIDSTYPE ,
            ctav.definition AS TMDEF,
            case sdm.repetition_indicator
                when true then 'Y'
                when false then 'N'
            END AS TMRPT
        """
        result_array = db.cypher_query(
            query=query,
            params={
                "study_uid": str(study_uid),
                "study_value_version": str(study_value_version),
            },
        )
        return utils.db_result_to_list(result_array)
