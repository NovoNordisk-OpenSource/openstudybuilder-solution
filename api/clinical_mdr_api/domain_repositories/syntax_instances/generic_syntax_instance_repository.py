import abc
import re
from datetime import datetime
from typing import Generic, Iterable, TypeVar

from neomodel import db

from clinical_mdr_api.domain_repositories._utils.helpers import (
    get_latest_version_properties,
)
from clinical_mdr_api.domain_repositories.generic_syntax_repository import (
    GenericSyntaxRepository,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Conjunction,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains.libraries.object import ParametrizedTemplateVO
from clinical_mdr_api.domains.libraries.parameter_term import SimpleParameterTermVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemStatus,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameAndAttributes,
    SimpleTermAttributes,
    SimpleTermName,
)
from common.exceptions import BusinessLogicException, NotFoundException

_AggregateRootType = TypeVar("_AggregateRootType", bound=LibraryItemAggregateRootBase)


class GenericSyntaxInstanceRepository(
    GenericSyntaxRepository[_AggregateRootType], Generic[_AggregateRootType], abc.ABC
):
    template_class: type

    def next_available_sequence_id(self, uid: str) -> str | None:
        rs = db.cypher_query(f"""
            MATCH (r:SyntaxTemplateRoot {{uid: "{uid}"}})
            OPTIONAL MATCH (pr:{self.root_class.__name__})-[:CREATED_FROM]->(r)
            RETURN pr.sequence_id, r.sequence_id
            """)

        if rs[0][0][0]:
            rs[0].sort(key=lambda x: int(x[0].split("P")[1]), reverse=True)

            prefix, number = re.search("(.*P)(\\d*)", rs[0][0][0]).groups()
            return prefix + str(int(number) + 1)

        return rs[0][0][1] + "P1"

    def find_instance_uids_by_template_uid(self, template_uid: str) -> Iterable[str]:
        template_root: VersionRoot = self.template_class.nodes.get_or_none(
            uid=template_uid
        )
        items = template_root.has_template.all()
        return [item.uid for item in items]

    def find_pre_instance_uids_by_template_uid(
        self, template_uid: str
    ) -> Iterable[str]:
        template_root: VersionRoot = self.template_class.nodes.get_or_none(
            uid=template_uid
        )
        items = template_root.has_pre_instance.all()
        return [item.uid for item in items]

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: VersionRoot,
        value: VersionValue,
    ) -> None:
        value.name = versioned_object.name
        value.save()
        value.has_parameters.disconnect_all()
        value.has_conjunction.disconnect_all()
        params = versioned_object.get_parameters()
        for position, parameter_config in enumerate(params):
            conjunction_string: str = parameter_config.conjunction
            if len(conjunction_string) != 0:
                result = Conjunction.nodes.get_or_none(string=conjunction_string)
                if result is None:
                    conjunction = Conjunction(string=conjunction_string)
                    conjunction.save()
                else:
                    conjunction = result
                value.has_conjunction.connect(conjunction, {"position": position + 1})
            for index, value_config in enumerate(parameter_config.parameters):
                self._add_value_parameter_relation(
                    value, value_config.uid, position + 1, index + 1
                )
        template = self.template_class.nodes.get(uid=versioned_object.template_uid)

        if self.is_pre_instance(root):
            root.created_from.connect(template)
        else:
            root.has_template.connect(template)

        # Double check that we actually performed a valid connection to the template that isn't retired.
        # this needs to be done after connecting, as there might be concurrent transactions retiring the template.
        latest_version = get_latest_version_properties(template)
        BusinessLogicException.raise_if(
            latest_version and latest_version.status == LibraryItemStatus.RETIRED.value,
            msg=root.uid
            + " cannot be added to "
            + template.uid
            + ", as it is retired.",
        )

    def _add_value_parameter_relation(
        self, value: VersionValue, parameter_uid: str, position: int, index: int
    ):
        if self.is_pre_instance(value):
            # TODO: This should be refactored when we change the relationship between
            # syntax instance root and TemplateParameterTermRoot to value to value.
            cypher_query = f"""
                MATCH (spiv:SyntaxPreInstanceValue), (tp:TemplateParameterTermRoot {{uid: $parameter_uid}})-[:LATEST]->(tpv:TemplateParameterTermValue)
                WHERE elementId(spiv) = $value_id
                CREATE (spiv)-[r:{value.PARAMETERS_LABEL} {{position: $position, index: $index}}]->(tpv)
                """
        else:
            cypher_query = f"""
                MATCH (siv:SyntaxInstanceValue), (tp:TemplateParameterTermRoot {{uid: $parameter_uid}})
                WHERE elementId(siv) = $value_id
                CREATE (siv)-[r:{value.PARAMETERS_LABEL} {{position: $position, index: $index}}]->(tp)
                """
        db.cypher_query(
            cypher_query,
            {
                "parameter_uid": parameter_uid,
                "position": position,
                "index": index,
                "value_id": value.element_id,
            },
        )

    def find_by(self, name: str) -> _AggregateRootType:
        values = self.value_class.nodes.filter(name=name)

        NotFoundException.raise_if(
            len(values) < 1, self.root_class.__name__, name, "Name"
        )

        root_uid = values[0].get_root_uid_by_latest()
        item: _AggregateRootType = self.find_by_uid(uid=root_uid)
        return item

    def _get_template_parameters(self, root, value):
        # TODO: This should be refactored when we change the relationship between
        # syntax instance root and TemplateParameterTermRoot to value to value.
        if self.is_pre_instance(root):
            cypher_query = f"""
        MATCH (param:TemplateParameter)<-[u:USES_PARAMETER]-(:SyntaxTemplateRoot)<-[:CREATED_FROM]-(pre_instance_root:{root.__label__})-[:LATEST]->(pre_instance_value:{value.__label__})
        WHERE pre_instance_root.uid=$root_uid AND pre_instance_value.name=$value_name
        WITH pre_instance_value, param.name as parameter, u.position as position
        OPTIONAL MATCH (pre_instance_value)-[rel:USES_VALUE]->(tptv:TemplateParameterTermValue)<-[:HAS_VERSION]-(tptr:TemplateParameterTermRoot)
        CALL apoc.when(tptr IS NOT NULL AND tptr:StudyEndpoint,
            "MATCH (:StudyValue)-->(tptr)-[:HAS_SELECTED_ENDPOINT]->(ev:EndpointValue)
            OPTIONAL MATCH (tptr)-[:HAS_SELECTED_TIMEFRAME]->(tv:TimeframeValue)
            CALL
            {{
                WITH tptr
                OPTIONAL MATCH (tptr)-[rel:HAS_UNIT]->(un:UnitDefinitionRoot)-[:LATEST_FINAL]->(udv:UnitDefinitionValue)
                WITH rel, udv, tptr ORDER BY rel.index
                WITH collect(udv.name) as unit_names, tptr
                OPTIONAL MATCH (tptr)-[:HAS_CONJUNCTION]->(co:Conjunction)
                WITH unit_names, co
                RETURN apoc.text.join(unit_names, ' ' + coalesce(co.string, '') + ' ') AS unit
            }}
            RETURN ev.name + coalesce(' ' + unit, '') + coalesce(' ' + tv.name, '') AS tptv_name",
            "CALL apoc.case(
                [
                    tptv.name_sentence_case IS NOT NULL, 'RETURN tptv.name_sentence_case AS name',
                    tptv.name_sentence_case IS NULL, 'RETURN tptv.name AS name'
                ],
                '',
                {{ tptv:tptv }})
                YIELD value
                RETURN value.name AS tptv_name
            ",
        {{tptr:tptr, tptv:tptv}})
        YIELD value
        WITH pre_instance_value,
            rel,
            position,
            parameter,
            tptr,
            value.tptv_name AS tptv_name
        OPTIONAL MATCH (ptv: ParameterTemplateValue)<-[:LATEST_FINAL]-(td: ParameterTemplateRoot)-[:HAS_COMPLEX_VALUE]->(tptr)
        WHERE tptv_name iS NOT NULL
        WITH pre_instance_value, position, parameter, collect(DISTINCT {{
            set_number: 0,
            position: rel.position,
            index: rel.index,
            parameter_name: parameter,
            parameter_term: tptv_name,
            parameter_uid: tptr.uid,
            definition: td.uid,
            template: ptv.template_string,
            labels: labels(tptr)
        }}) as data
        OPTIONAL MATCH (pre_instance_value)-[con_rel:HAS_CONJUNCTION]->(con:Conjunction)
        WHERE con_rel.position=position
        WITH position, parameter, data, coalesce(con.string, "") AS conjunction
        RETURN position, parameter, [row in data where row.position = position | row] as parameterterms, conjunction
        """
        else:
            cypher_query = f"""
        MATCH  (param:TemplateParameter)<-[u:USES_PARAMETER]-
              (:SyntaxTemplateRoot)-[:HAS_OBJECTIVE|HAS_ENDPOINT|HAS_TIMEFRAME|HAS_CRITERIA|HAS_FOOTNOTE|HAS_ACTIVITY_INSTRUCTION]->
              (vt:{root.__label__})-[:LATEST]->
              (vv:{value.__label__})
        WHERE vt.uid=$root_uid AND vv.name=$value_name
        WITH vv, param.name as parameter, u.position as position
        OPTIONAL MATCH (vv)-[rel:USES_VALUE]->(tptr:TemplateParameterTermRoot)
        CALL apoc.when(
            tptr IS NOT NULL AND tptr:StudyEndpoint,
            "MATCH (:StudyValue)-->(tptr)-[:HAS_SELECTED_ENDPOINT]->(ev:EndpointValue)
            OPTIONAL MATCH (tptr)-[:HAS_SELECTED_TIMEFRAME]->(tv:TimeframeValue)
            CALL
            {{
                WITH tptr
                OPTIONAL MATCH (tptr)-[rel:HAS_UNIT]->(un:UnitDefinitionRoot)-[:LATEST_FINAL]->(udv:UnitDefinitionValue)
                WITH rel, udv, tptr ORDER BY rel.index
                WITH collect(udv.name) as unit_names, tptr
                OPTIONAL MATCH (tptr)-[:HAS_CONJUNCTION]->(co:Conjunction)
                WITH unit_names, co
                RETURN apoc.text.join(unit_names, ' ' + coalesce(co.string, '') + ' ') AS unit
            }}
            RETURN ev.name + coalesce(' ' + unit, '') + coalesce(' ' + tv.name, '') AS tpv",
            "WITH head([(tptr)-[:LATEST_FINAL]->(tpv) | tpv]) AS tpv
            CALL apoc.case(
                [
                    tpv.name_sentence_case IS NOT NULL, 'RETURN tpv.name_sentence_case AS name',
                    tpv.name_sentence_case IS NULL, 'RETURN tpv.name AS name'
                ],
                '',
                {{ tpv:tpv }})
            YIELD value
            RETURN value.name AS tpv
            ",
            {{tptr:tptr}})
            YIELD value
            WITH vv,
                rel,
                position,
                parameter,
                tptr,
                value.tpv AS tpv
        OPTIONAL MATCH (tpvv: ParameterTemplateValue)<-[:LATEST_FINAL]-(td: ParameterTemplateRoot)-[:HAS_COMPLEX_VALUE]->(tptr)
        WHERE tpv iS NOT NULL
        WITH vv, position, parameter, collect(DISTINCT {{
            set_number: 0,
            position: rel.position,
            index: rel.index,
            parameter_name: parameter,
            parameter_term: tpv,
            parameter_uid: tptr.uid,
            definition: td.uid,
            template: tpvv.template_string,
            labels: labels(tptr)
        }}) as data
        OPTIONAL MATCH (vv)-[con_rel:HAS_CONJUNCTION]->(con:Conjunction)
        WHERE con_rel.position=position
        WITH position, parameter, data, coalesce(con.string, "") AS conjunction
        RETURN position, parameter, [row in data where row.position = position | row] as parameterterms, conjunction
        """

        results, _ = db.cypher_query(
            cypher_query, params={"root_uid": root.uid, "value_name": value.name}
        )

        parameter_terms = self._parse_parameter_terms(instance_parameters=results)
        return parameter_terms[0] if len(parameter_terms) > 0 else []

    def _from_repository_values(self, value):
        simple_parameter_term_vo = SimpleParameterTermVO.from_repository_values(
            uid=value["parameter_uid"], value=value["parameter_term"]
        )
        return simple_parameter_term_vo

    def get_template_vo(self, root, value, template):
        return ParametrizedTemplateVO(
            template_name=template["template_name"],
            template_uid=template["template_uid"],
            template_sequence_id=template["template_sequence_id"],
            guidance_text=template["template_guidance_text"],
            parameter_terms=self._get_template_parameters(root, value),
            library_name=template["template_library_name"],
            template_type=(
                SimpleCTTermNameAndAttributes(
                    term_uid=template["term_uid"],
                    name=SimpleTermName(
                        sponsor_preferred_name=template["name"],
                        sponsor_preferred_name_sentence_case=template[
                            "name_sentence_case"
                        ],
                    ),
                    attributes=SimpleTermAttributes(
                        nci_preferred_name=template["preferred_term"],
                    ),
                )
                if template["term_uid"]
                else None
            ),
        )

    def _get_template(
        self, root: VersionRoot, value: VersionValue, date_before: datetime
    ) -> ParametrizedTemplateVO:
        parameter_terms = self._get_template_parameters(root, value)

        template_object: VersionRoot
        if self.is_pre_instance(root):
            template_object = root.created_from.get()
        else:
            template_object = root.has_template.get()

        template_value_object: VersionValue
        if date_before:
            template_value_object = template_object.get_final_before(date_before)
            if template_value_object is None:
                template_value_object = template_object.get_retired_before(date_before)

        if template_value_object is None:
            template_value_object = template_object.latest_final.get()

        template = ParametrizedTemplateVO(
            template_name=template_value_object.name,
            template_uid=template_object.uid,
            template_sequence_id=template_object.sequence_id,
            parameter_terms=parameter_terms,
            guidance_text=template_value_object.guidance_text,
            library_name=template_object.has_library.get().name,
        )
        return template

    def check_usage_count(self, _: str) -> bool:
        return False

    def is_pre_instance(self, obj):
        return "PreInstance" in obj.__class__.__name__
