import abc
import re
from typing import Any, Generic, TypeVar

from neomodel import db

from clinical_mdr_api.domain_repositories.generic_repository import EntityNotFoundError
from clinical_mdr_api.domain_repositories.generic_syntax_repository import (
    GenericSyntaxRepository,
)
from clinical_mdr_api.domain_repositories.models.generic import VersionRoot
from clinical_mdr_api.domain_repositories.models.syntax import SyntaxTemplateValue
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameter,
)
from clinical_mdr_api.domains.syntax_templates.template import TemplateVO
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.utils import strip_html
from common.config import settings

_AggregateRootType = TypeVar("_AggregateRootType")


class GenericSyntaxTemplateRepository(
    GenericSyntaxRepository, Generic[_AggregateRootType], abc.ABC
):
    def next_available_sequence_id(
        self,
        uid: str,
        prefix: str | None = None,
        type_uid: str | None = None,
        library: LibraryVO | None = None,
    ) -> str | None:
        query = f"""MATCH (r:{self.root_class.__name__})<-[:CONTAINS_SYNTAX_TEMPLATE]-(l:Library {{name: "{library.name}"}})"""

        if type_uid:
            query += f"""MATCH (r)-[:HAS_TYPE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot {{uid: "{type_uid}"}})"""

        query += "RETURN r.sequence_id"

        rs = db.cypher_query(query)

        name = uid.replace("Template", "")
        prefix = (
            prefix if prefix else "".join([char for char in name if char.isupper()])
        )
        if library.name == "User Defined":
            prefix = "U-" + prefix

        if rs[0]:
            rs[0].sort(key=lambda x, p=prefix: int(x[0].split(p)[1]), reverse=True)

            number = re.search("(\\d*)$", rs[0][0][0]).group()
            return prefix + str(int(number) + 1)

        return prefix + "1"

    def _get_template(self, value: SyntaxTemplateValue) -> TemplateVO:
        return TemplateVO(
            name=value.name,
            name_plain=value.name_plain,
            guidance_text=value.guidance_text,
        )

    def _get_or_create_value(
        self,
        root: VersionRoot,
        ar: _AggregateRootType,
        force_new_value_node: bool = False,
    ) -> SyntaxTemplateValue:
        if not force_new_value_node:
            for itm in root.has_version.filter(
                name=ar.name, guidance_text=ar.guidance_text
            ):
                return itm

            latest_draft = root.latest_draft.get_or_none()
            if latest_draft and not self._has_data_changed(ar, latest_draft):
                return latest_draft
            latest_final = root.latest_final.get_or_none()
            if latest_final and not self._has_data_changed(ar, latest_final):
                return latest_final
            latest_retired = root.latest_retired.get_or_none()
            if latest_retired and not self._has_data_changed(ar, latest_retired):
                return latest_retired

        new_value = self.value_class(
            name=ar.name, guidance_text=ar.guidance_text, name_plain=strip_html(ar.name)
        )
        self._db_save_node(new_value)
        return new_value

    def _has_data_changed(
        self, ar: _AggregateRootType, value: SyntaxTemplateValue
    ) -> bool:
        base_comparison = (
            ar.name != value.name or ar.guidance_text != value.guidance_text
        )
        return base_comparison

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: VersionRoot,
        value: SyntaxTemplateValue,
    ) -> None:
        root.has_parameters.disconnect_all()
        for index, parameter_name in enumerate(
            versioned_object.template_value.parameter_names
        ):
            parameter = TemplateParameter.nodes.get_or_none(name=parameter_name)
            if parameter is not None:
                # root.has_parameters.connect(parameter, {"position": index + 1})
                cypher_query = f"""
                    MATCH (tr:{self.root_class.__label__}) WHERE elementId(tr)=$element_id
                    WITH tr
                    MATCH (tp:TemplateParameter {{name: $parameter_name}})
                    WITH tr, tp
                    CREATE (tr)-[uses_parameter:{self.root_class.PARAMETERS_LABEL}]->(tp)
                    SET uses_parameter.position=$position
                    """
                db.cypher_query(
                    cypher_query,
                    {
                        "element_id": root.element_id,
                        "parameter_name": parameter_name,
                        "position": index + 1,
                    },
                )
            else:
                raise EntityNotFoundError(
                    f"Cannot find parameter named {parameter_name}"
                )

    def _add_value_parameter_relation(
        self,
        value: SyntaxTemplateValue,
        parameter_uid: str,
        position: int,
        index: int,
        set_number: int | None,
    ):
        set_number_subclause = (
            "set_number: $set_number, " if set_number is not None else ""
        )
        cypher_query = f"""
            MATCH (tv:SyntaxTemplateValue), (pt:TemplateParameterTermRoot {{uid: $parameter_uid}})
            WHERE elementId(tv) = $value_id
            CREATE (tv)-[r:{value.PARAMETERS_LABEL} {{{set_number_subclause}position: $position, index: $index}}]->(pt)
            """
        db.cypher_query(
            cypher_query,
            {
                "parameter_uid": parameter_uid,
                "set_number": set_number,
                "position": position,
                "index": index,
                "value_id": value.element_id,
            },
        )

    def get_parameters_including_terms(
        self,
        template_uid: str,
        study_uid: str | None = None,
        include_study_endpoints: bool = False,
        parameter_term_uids_to_fetch: list[str] | None = None,
    ):
        parameter_term_uids_to_fetch_query = (
            " AND pr.uid IN $parameter_term_uids_to_fetch"
            if parameter_term_uids_to_fetch and len(parameter_term_uids_to_fetch) > 0
            else ""
        )
        cypher_query = f"""
            MATCH (otr:{self.root_class.__label__} {{uid: $uid}})-[uses_parameter:{self.root_class.PARAMETERS_LABEL}]->(pt)
            WHERE NOT pt.name=$name
            WITH uses_parameter, pt
            ORDER BY
                uses_parameter.position ASC
            CALL (pt) {{
                    CALL(pt) {{
                            OPTIONAL MATCH (pt)<-[:HAS_PARENT_PARAMETER*0..]-(pt_parents)-[:HAS_PARAMETER_TERM]->(pr)-[:LATEST_FINAL]->(pv)
                                WHERE pt.name <> "{settings.operator_parameter_name}"
                                // Filter out the child template parameter values if theirs parent contains the same value.
                                // This ensures that the terms response will contain unique values.
                                // Also filter out the values that are part of the Requested library.
                                AND (pt=pt_parents OR NOT ((pt_parents)-[:HAS_PARAMETER_TERM]->(pr) AND (pt)-[:HAS_PARAMETER_TERM]->(pr)))
                                AND NOT (pr)<-[:CONTAINS_CONCEPT]-(:Library {{name: "Requested"}})
                                {parameter_term_uids_to_fetch_query}
                            CALL apoc.case(
                            [
                                pv.name_sentence_case IS NOT NULL, 'RETURN pv.name_sentence_case AS name',
                                pv.name_sentence_case IS NULL, 'RETURN pv.name AS name'
                            ],
                            '',
                            {{ pv:pv}})
                            yield value
                            WITH pt, pr, pt_parents, value.name as value
                            // If a TemplateParameterTermValue is NumericValue type we sort template parameter values
                            // by value property not name property
                            ORDER BY 
                                CASE 
                                    WHEN "NumericValue" IN labels(pv) THEN pv.value 
                                ELSE value END ASC
                            WITH pr ,value,pt_parents
                            RETURN pr.uid as uid, value, pt_parents.name as data_type, labels(pr) as labels
                        union
                            WITH pt
                            OPTIONAL MATCH (pt)-[:HAS_PARAMETER_TERM]->(pr_op)-[:LATEST_FINAL]->(pv_op)
                                WHERE pt.name = "{settings.operator_parameter_name}"
                            MATCH (pr_op)<-[:HAS_NAME_ROOT]-(:CTTermRoot)
                            WITH pt, pv_op.name as value, pr_op, pv_op
                            ORDER BY value ASC
                            WITH  pr_op , value, pt
                            RETURN pr_op.uid as uid, value, pt.name as data_type, labels(pr_op) as labels
                    }}
                    WITH labels,uid,value,data_type
                        WHERE uid IS NOT NULL
                    RETURN collect({{uid: uid, name: value, type: data_type, labels: labels}}) AS terms
            }}
            RETURN
                pt.name AS name,
                terms,
                uses_parameter.position
            """
        dataset, _ = db.cypher_query(
            cypher_query,
            {
                "uid": template_uid,
                "name": settings.study_endpoint_tp_name,
                "parameter_term_uids_to_fetch": parameter_term_uids_to_fetch,
            },
        )
        data = [
            {
                "name": item[0],
                "terms": item[1],
                "position": item[2],
            }
            for item in dataset
        ]

        if study_uid:
            data = self.subset_parameters_to_specific_study(
                data=data, study_uid=study_uid
            )

        # StudyEndpoint parameters need to be treated separately
        if include_study_endpoints is True:
            cypher_query = f"""
                MATCH (:{self.root_class.__label__} {{uid: $uid}})-[uses_parameter:{self.root_class.PARAMETERS_LABEL}]->(pt)
                WHERE pt.name=$pt_name
                WITH uses_parameter, pt
                ORDER BY
                    uses_parameter.position ASC
                CALL (pt) {{
                    MATCH (pt)-[:HAS_PARAMETER_TERM]->(pr)<-[:HAS_STUDY_ENDPOINT]-(:StudyValue)<-[:LATEST]-(sr:StudyRoot)
                    WHERE sr.uid=$study_uid
                    MATCH (pr)-[:HAS_SELECTED_ENDPOINT]->(ev:EndpointValue)
                    OPTIONAL MATCH (pr)-[:HAS_SELECTED_TIMEFRAME]->(tv)
                    CALL
                    {{
                        WITH pr
                        OPTIONAL MATCH (pr)-[rel:HAS_UNIT]->(un:UnitDefinitionRoot)-[:LATEST_FINAL]->(udv:UnitDefinitionValue)
                        WITH rel, udv, pr ORDER BY rel.index
                        WITH collect(udv.name) as unit_names, pr
                        OPTIONAL MATCH (pr)-[:HAS_CONJUNCTION]->(co:Conjunction)
                        WITH unit_names, co
                        RETURN apoc.text.join(unit_names, " " + coalesce(co.string, "") + " ") AS unit
                    }}
                    WITH pr.uid AS puid, ev.name + coalesce(" " + unit, "") + coalesce(" " + tv.name, "") AS pname, labels(pr) as labels
                    ORDER BY pname ASC
                    RETURN collect({{uid: puid, name: pname, type: $pt_name, labels: labels}}) AS terms
                }}

                RETURN
                    pt.name AS name,
                    terms,
                    uses_parameter.position
                """
            dataset, _ = db.cypher_query(
                cypher_query,
                {
                    "uid": template_uid,
                    "study_uid": study_uid,
                    "pt_name": settings.study_endpoint_tp_name,
                },
            )
            data += [
                {
                    "name": item[0],
                    "terms": item[1],
                    "position": item[2],
                }
                for item in dataset
            ]
        return sorted(data, key=lambda item: item["position"])

    def simple_concept_template(self, rel_type: str):
        query_to_subset = f"""
            MATCH (:StudyRoot {{uid:$uid}})-[:LATEST]->(:StudyValue)
            -[:HAS_STUDY_VISIT]->(:StudyVisit)-[:{rel_type}]->(:SimpleConceptRoot)
            -[:LATEST_FINAL]->(simple_concept_value:SimpleConceptValue)
            return simple_concept_value.name
            """
        return query_to_subset

    def ct_term_template(self, rel_type: str):
        query_to_subset = f"""
        MATCH (:StudyRoot {{uid:$uid}})-[:LATEST]->(:StudyValue)
        -[:HAS_STUDY_VISIT]->(:StudyVisit)-[:{rel_type}]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)
        -[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST_FINAL]->(term_name_value:CTTermNameValue)
        return term_name_value.name
        """
        return query_to_subset

    def subset_time_point_reference(self):
        query_to_subset = """
            MATCH (:StudyRoot {uid:$uid})-[:LATEST]->(:StudyValue)
            -[:HAS_STUDY_VISIT]->(:StudyVisit)-[:HAS_TIMEPOINT]->(:SimpleConceptRoot)
            -[:LATEST_FINAL]->(simple_concept_value:SimpleConceptValue)-[:HAS_TIME_REFERENCE]->(:CTTermContext)-[:HAS_SELECTED_TERM]->(:CTTermRoot)
            -[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST_FINAL]->(term_name_value:CTTermNameValue)
            return term_name_value.name
            """
        return query_to_subset

    def subset_parameters_to_specific_study(self, data: list[Any], study_uid: str):
        for parameter in data:
            query_to_subset = None
            param_name = parameter["name"]
            if parameter["name"] == settings.study_visit_type_name:
                query_to_subset = self.ct_term_template(rel_type="HAS_VISIT_TYPE")
            elif parameter["name"] == settings.study_visit_timeref_name:
                query_to_subset = self.subset_time_point_reference()
            elif parameter["name"] == settings.study_visit_name:
                query_to_subset = self.simple_concept_template(
                    rel_type="HAS_VISIT_NAME"
                )
            elif parameter["name"] == settings.study_day_name:
                query_to_subset = self.simple_concept_template(rel_type="HAS_STUDY_DAY")
            elif parameter["name"] == settings.study_duration_days_name:
                query_to_subset = self.simple_concept_template(
                    rel_type="HAS_STUDY_DURATION_DAYS"
                )
            elif parameter["name"] == settings.study_week_name:
                query_to_subset = self.simple_concept_template(
                    rel_type="HAS_STUDY_WEEK"
                )
            elif parameter["name"] == settings.study_duration_weeks_name:
                query_to_subset = self.simple_concept_template(
                    rel_type="HAS_STUDY_DURATION_WEEKS"
                )
            elif parameter["name"] == settings.week_in_study_name:
                query_to_subset = self.simple_concept_template(
                    rel_type="HAS_WEEK_IN_STUDY"
                )
            elif parameter["name"] == settings.study_timepoint_name:
                query_to_subset = self.simple_concept_template(rel_type="HAS_TIMEPOINT")
            if query_to_subset:
                template_parameters_subset, _ = db.cypher_query(
                    query_to_subset, {"uid": study_uid}
                )
                flat_template_parameters = self.flatten_neomodel_output(
                    output=template_parameters_subset
                )
                self.subset_value_list_for_given_tp(
                    data=data,
                    param_name=param_name,
                    subset_list=flat_template_parameters,
                )
        return data

    def flatten_neomodel_output(self, output: list[Any]):
        flatted_output = []
        if len(output) > 0:
            for value in output:
                flatted_output.append(value[0].lower())
        return flatted_output

    def subset_value_list_for_given_tp(
        self, data: list[Any], param_name: str, subset_list: list[Any]
    ):
        for template_param_value in data:
            if template_param_value["name"] == param_name:
                template_param_value["terms"] = [
                    item
                    for item in template_param_value["terms"]
                    if item["name"].lower() in subset_list
                ]

    def check_usage_count(self, uid: str) -> int:
        itm: VersionRoot = self.root_class.nodes.get(uid=uid)
        return len(itm.has_template.all())

    def check_exists_by_name_in_library(
        self, name: str, library: str, type_uid: str | None = None
    ) -> bool:
        result = self._query_by_name_in_library(name, library, type_uid)

        return len(result) > 0 and len(result[0]) > 0

    def _query_by_name_in_library(self, name, library, type_uid):
        query = f"""
MATCH (:Library {{name: $library}})-[:{self.root_class.LIBRARY_REL_LABEL}]->(root:{self.root_class.__label__})
-[:LATEST_FINAL|LATEST_DRAFT|LATEST_RETIRED|LATEST]->(:{self.value_class.__label__} {{name: $name}})
WITH DISTINCT root
"""
        if type_uid:
            query += "MATCH (type:CTTermRoot {uid: $typeUid})<-[:HAS_SELECTED_TERM]-(:CTTermContext)<-[:HAS_TYPE]-(root)"
        query += "RETURN root.uid"

        result, _ = db.cypher_query(
            query, {"name": name, "library": library, "typeUid": type_uid}
        )

        return result
