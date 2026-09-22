import logging
from dataclasses import asdict, dataclass

from neo4j.exceptions import ServiceUnavailable
from neomodel import db

log = logging.getLogger(__name__)


@dataclass
class ParameterConcept:
    name: str
    values: str

    def get_values(self):
        return asdict(self)


class ParameterConceptRepository:
    @staticmethod
    def get_parameter_concept_values(query):
        items, labels = db.cypher_query(query)
        return_values = []
        for row in items:
            return_item = {}
            for key, value in zip(labels, row):
                return_item[key] = value
            return_values.append(return_item)
        return return_values


def parameter_concept_create_factory(name, query):
    values = ParameterConceptRepository.get_parameter_concept_values(query)
    return ParameterConcept(name, values)


class ComplexTemplateParameterRepository:
    def __init__(self):
        try:
            self._fetch_concepts()
        except ServiceUnavailable:
            log.error(
                "The neo4j database is unavailable. API functionality will be severely limited."
            )
            self.concepts = None

    def _fetch_concepts(self):
        time_unit = parameter_concept_create_factory(
            name="TimeUnit",
            query="""
            MATCH (n:UnitDefinitionRoot)-[:LATEST_FINAL]->(v:UnitDefinitionValue)-[:HAS_CT_DIMENSION]->(:CTTermContext)-[:HAS_SELECTED_TERM]->
            (term_root:CTTermRoot)-[:HAS_NAME_ROOT]->()-[:LATEST_FINAL]->(:CTTermNameValue {name: "TIME"}) 
            return n.uid as uid, v.name as name, 'TimeUnit' as type
            """,
        )
        acidity_unit = parameter_concept_create_factory(
            name="AcidityUnit",
            query="""
            MATCH (n:UnitDefinitionRoot)-[:LATEST_FINAL]->(v:UnitDefinitionValue)-[:HAS_CT_DIMENSION]->(:CTTermContext)-[:HAS_SELECTED_TERM]->
            (term_root:CTTermRoot)-[:HAS_NAME_ROOT]->()-[:LATEST_FINAL]->(:CTTermNameValue {name: "ACIDITY"}) 
            return n.uid as uid, v.name as name, 'AcidityUnit' as type
            """,
        )
        concentration_unit = parameter_concept_create_factory(
            name="ConcentrationUnit",
            query="""
            MATCH (n:UnitDefinitionRoot)-[:LATEST_FINAL]->(v:UnitDefinitionValue)-[:HAS_CT_DIMENSION]->(:CTTermContext)-[:HAS_SELECTED_TERM]->
            (term_root:CTTermRoot)-[:HAS_NAME_ROOT]->()-[:LATEST_FINAL]->(:CTTermNameValue {name: "CONCENTRATION"}) 
            return n.uid as uid, v.name as name, 'ConcentrationUnit' as type
            """,
        )
        self.concepts = [time_unit, acidity_unit, concentration_unit]

    def find_extended(self):
        values = self.find_all_with_samples()
        if self.concepts is None:
            self._fetch_concepts()
        for concept in self.concepts:
            values.append(concept.get_values())
        values.sort(key=lambda s: s["name"])
        return values

    def find_all_with_samples(self):
        items, _ = db.cypher_query("""
            MATCH (pt:TemplateParameter)
            CALL (pt) {
                MATCH (pt)<-[:HAS_PARENT_PARAMETER*0..]-(pt_parents)-[:HAS_PARAMETER_TERM]->(pr)-[:LATEST_FINAL]->(pv)
                // Filter out items from the Requested library.
                WHERE NOT (pr)<-[:CONTAINS_CONCEPT]-(:Library {name: "Requested"})    
                WITH  pr, pv,  pt_parents
                ORDER BY pv.name ASC
                LIMIT 3
                RETURN collect({uid: pr.uid, name: pv.name, type: pt_parents.name}) AS terms
            }
            RETURN
                pt.name AS name,
                terms
            ORDER BY name
        """)
        return_value = [{"name": item[0], "terms": item[1]} for item in items]
        return return_value

    def find_values(self, template_parameter_name: str):
        items, _ = db.cypher_query(
            """
            MATCH (pt:TemplateParameter {name: $name})
            CALL (pt) {
                MATCH (pt)<-[:HAS_PARENT_PARAMETER*0..]-(pt_parents)-[:HAS_PARAMETER_TERM]->(pr)-[:LATEST_FINAL]->(pv)
                // Filter out the child template parameter values if theirs parent contains the same value.
                // This ensures that the terms response will contain unique values.
                // Also filter out items from the Requested library.
                WHERE (pt=pt_parents OR NOT ((pt_parents)-[:HAS_PARAMETER_TERM]->(pr) AND (pt)-[:HAS_PARAMETER_TERM]->(pr))) AND NOT (pr)<-[:CONTAINS_CONCEPT]-(:Library {name: "Requested"})
                WITH  pr, pv,  pt_parents
                ORDER BY pv.name ASC
                RETURN collect({uid: pr.uid, name: pv.name, type: pt_parents.name}) AS terms
            }
            RETURN
                pt.name AS name,
                terms
            ORDER BY name
        """,
            {"name": template_parameter_name},
        )
        if len(items) > 0:
            return items[0][1]
        return []

    def get_parameter_including_terms(self, parameter_name: str):
        for item in self.find_extended():
            if item["name"] == parameter_name:
                return item
        return None
