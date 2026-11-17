"""Sponsor-defined content seeded in the test MDR database.

The assessment reads MDR for what the sponsor has already built, and nothing in this app
ever writes it — coining a codelist or a term is the main API's job. So these tests seed
it directly, in the shape that API produces: the root belongs to a library other than
`CDISC`, the name lives on the name half, the definition on the attributes half, and the
submission value belongs to the membership rather than to the term.

`CREATE` rather than `MERGE` for the version relationships and the membership, because a
`MERGE` carrying a `start_date` would never match an existing one anyway and hiding that
behind a keyword only makes the fixture harder to read.
"""

from typing import Any

from neomodel import db

SPONSOR_LIBRARY = "Sponsor"

# How a consumer stands in the version history of the thing it belongs to. Only a *live*
# consumer — one with an open `HAS_VERSION` — counts as using a term. `end_date: NULL`
# stores no property at all, which is how the main API leaves a version open, so "live"
# is also the missing-property case the usage queries once failed to match.
_VERSION_OF_CONSUMER = (
    "CREATE (owner)-[:HAS_VERSION {{version: '{version}', status: 'Final', "
    "start_date: datetime(), end_date: {end_date}}}]->(consumer)"
)
CONSUMER_VERSIONS = {
    "live": "CREATE (owner:ConsumerRoot)\n"
    + _VERSION_OF_CONSUMER.format(version="1.0", end_date="NULL"),
    "closed": "CREATE (owner:ConsumerRoot)\n"
    + _VERSION_OF_CONSUMER.format(version="1.0", end_date="datetime()"),
    "reopened": "\n".join(
        (
            "CREATE (owner:ConsumerRoot)",
            _VERSION_OF_CONSUMER.format(version="1.0", end_date="datetime()"),
            _VERSION_OF_CONSUMER.format(version="2.0", end_date="NULL"),
        )
    ),
    "unversioned": "",
}


def _write(cypher: str, **params: Any) -> None:
    db.cypher_query(cypher, params)


def add_sponsor_codelist(
    uid: str,
    name: str,
    submission_value: str,
    definition: str = "A sponsor codelist.",
) -> None:
    """A codelist the sponsor coined, in a library of their own."""

    _write(
        """
        MERGE (lib:Library {name: $library}) ON CREATE SET lib.is_editable = true
        MERGE (root:CTCodelistRoot {uid: $uid})
        MERGE (lib)-[:CONTAINS_CODELIST]->(root)
        MERGE (root)-[:HAS_ATTRIBUTES_ROOT]->(ar:CTCodelistAttributesRoot)
        CREATE (ar)-[:HAS_VERSION {
            version: '1.0', status: 'Final', start_date: datetime(), end_date: NULL
        }]->(value:CTCodelistAttributesValue {
            name: $name, submission_value: $submission_value, definition: $definition
        })
        MERGE (ar)-[:LATEST]->(value)
        MERGE (ar)-[:LATEST_FINAL]->(value)
        """,
        library=SPONSOR_LIBRARY,
        uid=uid,
        name=name,
        submission_value=submission_value,
        definition=definition,
    )


def add_sponsor_term(
    codelist_uid: str,
    uid: str,
    name: str,
    submission_value: str,
    definition: str = "A sponsor term.",
    status: str = "Final",
) -> None:
    """A term the sponsor coined, sitting inside an existing codelist.

    `codelist_uid` is normally a **CDISC** codelist: a sponsor term extending one of those
    is the collision the assessment exists to catch, and the term's library and the
    codelist's are independent in this model.

    `status` is on the *name* half deliberately. That is the one the main API's uniqueness
    rule reads, and `Retired` is the state in which a term stops colliding.
    """

    _write(
        """
        MERGE (lib:Library {name: $library}) ON CREATE SET lib.is_editable = true
        MERGE (root:CTTermRoot {uid: $uid})
        MERGE (lib)-[:CONTAINS_TERM]->(root)
        MERGE (root)-[:HAS_NAME_ROOT]->(nr:CTTermNameRoot)
        MERGE (root)-[:HAS_ATTRIBUTES_ROOT]->(ar:CTTermAttributesRoot)
        CREATE (nr)-[:HAS_VERSION {
            version: '1.0', status: $status, start_date: datetime(), end_date: NULL
        }]->(name_value:CTTermNameValue {
            name: $name, name_sentence_case: toLower($name)
        })
        MERGE (nr)-[:LATEST]->(name_value)
        MERGE (nr)-[:LATEST_FINAL]->(name_value)
        CREATE (ar)-[:HAS_VERSION {
            version: '1.0', status: 'Final', start_date: datetime(), end_date: NULL
        }]->(attributes:CTTermAttributesValue {definition: $definition})
        MERGE (ar)-[:LATEST]->(attributes)
        WITH root
        MATCH (codelist:CTCodelistRoot {uid: $codelist_uid})
        MERGE (root)<-[:HAS_TERM_ROOT]-(ct:CTCodelistTerm {
            submission_value: $submission_value
        })
        CREATE (codelist)-[:HAS_TERM {start_date: datetime(), end_date: NULL}]->(ct)
        """,
        library=SPONSOR_LIBRARY,
        codelist_uid=codelist_uid,
        uid=uid,
        name=name,
        submission_value=submission_value,
        definition=definition,
        status=status,
    )


def use_term_in_a_study(
    codelist_uid: str, term_uid: str, version: str = "live"
) -> None:
    """Makes something depend on a term, the way everything in OSB depends on one.

    Through a `CTTermContext`, which is how activity items, unit definitions, ODM items
    and study selections all reach a term — the node carries the codelist as well, so a
    reference is always to a term *in* a codelist.

    `version` is a key of `CONSUMER_VERSIONS`: whether the consumer is still live.
    """

    _write(
        f"""
        MATCH (root:CTTermRoot {{uid: $uid}})
        MATCH (codelist:CTCodelistRoot {{uid: $codelist_uid}})
        CREATE (context:CTTermContext)
        CREATE (context)-[:HAS_SELECTED_TERM]->(root)
        CREATE (context)-[:HAS_SELECTED_CODELIST]->(codelist)
        CREATE (consumer:StudyVisit:StudySelection)-[:HAS_VISIT_TYPE]->(context)
        {CONSUMER_VERSIONS[version]}
        """,
        uid=term_uid,
        codelist_uid=codelist_uid,
    )


def stop_using_term(codelist_uid: str, term_uid: str) -> None:
    """Undoes `use_term_in_a_study`, so a test can drive usage back down to zero.

    Deletes the same `CTTermContext`/`StudySelection` pair that call created, matched
    on the term and codelist it names — leaving the term root and codelist root alone.
    """

    _write(
        """
        MATCH (root:CTTermRoot {uid: $uid})<-[:HAS_SELECTED_TERM]-(context:CTTermContext)
              -[:HAS_SELECTED_CODELIST]->(:CTCodelistRoot {uid: $codelist_uid})
        OPTIONAL MATCH (consumer)-[:HAS_VISIT_TYPE]->(context)
        DETACH DELETE context, consumer
        """,
        uid=term_uid,
        codelist_uid=codelist_uid,
    )


def offer_term_as_template_parameter(codelist_uid: str, term_uid: str) -> None:
    """Wires a term up as a template parameter of its codelist, as `add_term` does.

    This one reaches the term through its *name* root, so it is invisible to any query
    that walks `CTTermRoot` — which is exactly why it is worth a fixture of its own.
    """

    _write(
        """
        MATCH (codelist:CTCodelistRoot {uid: $codelist_uid})-[:HAS_NAME_ROOT]->(cnr)
              -[:LATEST]->(codelist_name)
        MATCH (:CTTermRoot {uid: $uid})-[:HAS_NAME_ROOT]->(nr)
        SET codelist_name:TemplateParameter, nr:TemplateParameterTermRoot
        MERGE (codelist_name)-[:HAS_PARAMETER_TERM]->(nr)
        """,
        codelist_uid=codelist_uid,
        uid=term_uid,
    )


def use_term_in_a_syntax_instance(term_uid: str, version: str = "live") -> None:
    """Makes a syntax instance depend on a term through its name root.

    Unlike `HAS_PARAMETER_TERM`, which only offers the term as a parameter, this one is
    something already built on it — and it reaches the name half, so a check that walked
    `CTTermRoot` would not see it at all.
    """

    _write(
        f"""
        MATCH (:CTTermRoot {{uid: $uid}})-[:HAS_NAME_ROOT]->(nr)
        SET nr:TemplateParameterTermRoot
        CREATE (consumer:CriteriaValue:SyntaxInstanceValue)-[:USES_VALUE {{position: 1}}]->(nr)
        {CONSUMER_VERSIONS[version]}
        """,
        uid=term_uid,
    )


def use_term_name_value_in_a_syntax_instance(
    term_uid: str, version: str = "live"
) -> None:
    """Like `use_term_in_a_syntax_instance`, but reaching the name *value* node."""

    _write(
        f"""
        MATCH (:CTTermRoot {{uid: $uid}})-[:HAS_NAME_ROOT]->(:CTTermNameRoot)
              -[:HAS_VERSION]->(name_value)
        CREATE (consumer:CriteriaValue:SyntaxInstanceValue)
              -[:USES_VALUE {{position: 1}}]->(name_value)
        {CONSUMER_VERSIONS[version]}
        """,
        uid=term_uid,
    )
