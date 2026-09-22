import datetime
from dataclasses import dataclass
from textwrap import dedent
from typing import Any, Iterable, Mapping

from cachetools import TTLCache
from neomodel import RelationshipDefinition, RelationshipManager, StructuredNode, db

from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    VersionRelationship,
    VersionRoot,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
    StudyAction,
)
from clinical_mdr_api.repositories._utils import sb_clear_cache
from common.config import settings
from common.exceptions import ValidationException
from common.telemetry import trace_calls


class EntityNotFoundError(LookupError):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


@dataclass(frozen=True)
class RepositoryClosureData:
    not_for_update: bool
    repository: Any
    additional_closure: Any


class RepositoryImpl:
    """
    A repository is responsible for reading/writing data to/from the database.
    Results from a repository should be used to build aggregate root (AR) objects.
    """

    cache_store_item_by_uid = TTLCache(
        maxsize=settings.cache_max_size, ttl=settings.cache_ttl
    )

    value_class: type
    root_class: type

    @property
    def author_id(self) -> str | None:
        return self._author_id

    def __init__(self, user: str | None = None):
        self._author_id = user

    def _get_version_relation_keys(self, root_node: VersionRoot) -> tuple[
        RelationshipDefinition,
        RelationshipDefinition,
        RelationshipDefinition,
        RelationshipDefinition,
        RelationshipDefinition,
    ]:
        """
        Returns the keys used in the neomodel definition for the relationship definition.
        By default, all library objects use "has_version", "has_draft", etc...
        But some objects use an override, like SponsorModel with "has_sponsor_model_version"

        Args:
            root_node (VersionRoot): Root node for which to return the relationship manager

        Returns:
            The relationships managers for the various versioning relationships.
        """
        return (
            root_node.has_version,
            root_node.has_latest_value,
            root_node.latest_draft,
            root_node.latest_final,
            root_node.latest_retired,
        )

    @trace_calls
    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _db_create_and_link_nodes(
        self,
        root: ClinicalMdrNode,
        value: ClinicalMdrNode,
        rel_properties: Mapping[str, Any],
        save_root: bool = True,
    ):
        """
        Creates versioned root and versioned object nodes.
        # TODO - Generation of uids should be removed (additional service?)
        """
        if save_root:
            self._db_save_node(root)
        self._db_save_node(value)

        latest_draft: RelationshipDefinition | None
        latest_final: RelationshipDefinition | None
        (
            has_version,
            has_latest_value,
            latest_draft,
            latest_final,
            _,
        ) = self._get_version_relation_keys(root)
        latest_value = self._db_create_relationship(has_latest_value, value)
        self._db_create_relationship(has_version, value, rel_properties)

        if rel_properties["status"] != "Final":
            latest_draft = self._db_create_relationship(latest_draft, value)
            latest_final = None
        else:
            # if we create an object that is immediately in a final state, we create a LATEST_FINAL relationship.
            latest_draft = None
            latest_final = self._db_create_relationship(latest_final, value)
        return root, value, latest_value, latest_draft, latest_final

    @trace_calls
    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _db_save_node(self, node: ClinicalMdrNode) -> ClinicalMdrNode:
        """
        Saves a Neomodel node object in the graph.
        TODO: optionally accept multiple nodes and handle in same DB transaction.
        """
        if node is not None:
            node.save()
        return node

    @trace_calls
    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _db_create_relationship(
        self,
        origin: RelationshipManager,
        destination: ClinicalMdrNode,
        parameters: Mapping[str, Any] | None = None,
    ) -> VersionRelationship:
        """
        Creates a relationship of an origin type (e.g.VersionRoot.has_latest) to a destination (VersionValue).
        Parameters of a VersionRelationship must be included.
        """
        if parameters is None:
            parameters = {}

        if parameters:
            return origin.connect(destination, parameters)
        return origin.connect(destination)

    @trace_calls
    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _db_remove_relationship(
        self, relationship: RelationshipManager, value: ClinicalMdrNode | None = None
    ):
        """
        Removes a relationship.
        Example input: {relationship: compound_root.latest_draft,
                        value: compound_value}
        """
        if value is None:
            relationship.disconnect_all()
        else:
            relationship.disconnect(value)

    def generate_uid_callback(self):
        return self.root_class.get_next_free_uid_and_increment_counter()


@trace_calls
def get_connected_node_by_rel_name_and_study_value(
    node: Any,
    connected_rel_name: str,
    study_value: Any = None,
    multiple_returned_nodes: bool = False,
    at_least_one_returned: bool = True,
) -> Any:
    """
    Having a StudySelection node created on the database, get the connected StudySelection(s)
    """
    connected_node_with_study_value = []
    # get all nodes connected with connected_rel_name
    connected_nodes = getattr(node, connected_rel_name).all()
    if connected_nodes:
        relationships = [
            (_[0], _[1].definition["node_class"])
            for _ in connected_nodes[0].__all_relationships__
        ]
        connected_study_value_rel_name, _ = [
            i_rel for i_rel in relationships if i_rel[1] == type(study_value)
        ][0]
    for connected_node in connected_nodes:
        # get all study_values connected to the connected node

        # pylint: disable=possibly-used-before-assignment
        study_values = getattr(connected_node, connected_study_value_rel_name).all()
        for iter_study_value in study_values:
            # if the connected study_value is the same as the study_value of node
            if iter_study_value == study_value:
                # then take it as connected node
                connected_node_with_study_value.append(connected_node)
    if multiple_returned_nodes:
        return connected_node_with_study_value

    ValidationException.raise_if(
        len(connected_node_with_study_value) > 1,
        msg=f"Returned multiple connected '{connected_rel_name}' nodes and was expecting to match just one.",
    )

    if at_least_one_returned:
        ValidationException.raise_if(
            len(connected_node_with_study_value) == 0,
            msg=f"No connected '{connected_rel_name}' node was found and it was set as mandatory.",
        )
        return connected_node_with_study_value[0]
    return (
        connected_node_with_study_value[0] if connected_node_with_study_value else None
    )


@trace_calls
def _manage_versioning_with_relations(
    study_root: StudyRoot | str,
    action_type: type[StudyAction],
    before: StructuredNode | None = None,
    after: StructuredNode | None = None,
    exclude_relationships: Iterable[
        type[StructuredNode] | RelationshipDefinition | str
    ] = tuple(),
    **properties,
) -> StudyAction:
    """
    Manages versioning of StudySelection nodes: Creates StudyAction, and copies relationships from `before` to `after`.

    Relationship from StudyValue to `after` node should be connected outside of this method.
    Otherwise, this method is meant to replace `manage_previous_connected_study_selection_relationships`
    with better performance due to batching multiple statements into less Cypher queries.

    Args:
        study_root (StudyRoot | str): The StudyRoot node or its uid.
        action_type (type[StudyAction]): The StudyAction node type to create (Create, Edit, Delete).
        before (StructuredNode | None): The 'before' node (for Edit, Delete).
        after (StructuredNode | None): The 'after' node (for Edit, Create).
        exclude_relationships (Iterable[type[StructuredNode] | type[RelationshipDefinition] | str ]):
            Node-types and relationships to exclude when copying relationships from `before` to `after` node.
            Relationships from StudyAction and StudyValue nodes are always excluded, never copied.
        **properties: Additional properties for the StudyAction node.
            `date` will be set to current UTC time if not provided.
    Returns:
        StudyAction: The created StudyAction node.
    Raises:
        RuntimeError: If action_type is not StudyAction or required nodes are missing.
    """

    if not (isinstance(action_type, type) and issubclass(action_type, StudyAction)):
        raise RuntimeError("Action type must be StudyAction.")

    if before is None and action_type in {Edit, Delete}:
        raise RuntimeError(f"{action_type.__name__} action must have a 'before' node.")

    if after is None and action_type in {Edit, Create}:
        raise RuntimeError(f"{action_type.__name__} action must have an 'after' node.")

    # Match StudyRoot node
    if isinstance(study_root, StructuredNode):
        query = [
            "MATCH (study_root:StudyRoot)-[:LATEST]->(study_value:StudyValue)",
            f"WHERE {db.get_id_method()}(study_root) = $_study_root",
        ]
        params = {"_study_root": study_root.element_id}
    else:
        query = [
            "MATCH (study_root:StudyRoot {uid: $_study_root})-[:LATEST]->(study_value:StudyValue)"
        ]
        params = {"_study_root": study_root}

    # Create StudyAction node
    if "date" not in properties:
        properties["date"] = datetime.datetime.now(datetime.timezone.utc)
    properties = action_type.deflate(properties, skip_empty=True)
    query.append(dedent(f"""
        CREATE (action:{':'.join(action_type.inherited_labels())}:StudyAction {{{', '.join(f'{k}: ${k}' for k in properties)}}})<-[:AUDIT_TRAIL]-(study_root)
        WITH *
    """).strip())

    # Match & link previous node
    if before:
        query.append(f"MATCH (before) WHERE {db.get_id_method()}(before) = $_before")
        params["_before"] = before.element_id
        query.append("CREATE (action)-[:BEFORE]->(before)")
        query.append("WITH *")

    # Match & link new node
    if after:
        query.append(f"MATCH (after) WHERE {db.get_id_method()}(after) = $_after")
        params["_after"] = after.element_id
        query.append("CREATE (action)-[:AFTER]->(after)")
        query.append("WITH *")

    # Copy relationships
    if before and after:
        _exclude_relationships: set[Any] = set()
        _exclude_labels = {
            StudyValue.__name__,  # exclude (HAS_...) relations from StudyValue node
            StudyAction.__name__,  # exclude (BEFORE/AFTER) relations from StudyAction node
        }
        for rel in exclude_relationships:
            if isinstance(rel, str):
                _exclude_relationships.add(rel)
            elif isinstance(rel, RelationshipDefinition):
                _exclude_relationships.add(rel.definition["relation_type"])
            elif issubclass(rel, StructuredNode):
                _exclude_labels.add(rel.__name__)
            else:
                raise RuntimeError(
                    "exclude_relationships must be an iterable of StructuredNode subclasses or relationship type strings."
                )

        query.append(dedent("""
            CALL (before, after) {
                MATCH (before)-[r]->(target)
                WHERE NOT (type(r) IN $_exclude_relationships OR any(label IN labels(target) WHERE label IN $_exclude_labels))
                CALL apoc.create.relationship(after, type(r), properties(r), target) YIELD rel
                RETURN count(rel) AS num_rels_out
            }
            CALL (before, after) {
                MATCH (before)<-[r]-(source)
                WHERE NOT (type(r) IN $_exclude_relationships OR any(label IN labels(source) WHERE label IN $_exclude_labels))
                CALL apoc.create.relationship(source, type(r), properties(r), after) YIELD rel
                RETURN count(rel) AS num_rels_in
            }
        """).strip())
        params["_exclude_relationships"] = tuple(_exclude_relationships)
        params["_exclude_labels"] = tuple(_exclude_labels)

    # Unlink previous relationship from latest StudyValue
    if before:
        query.append(dedent("""
            CALL (study_value, before) {
                MATCH (study_value)-[rel]->(before)
                DELETE rel
                RETURN count(rel) AS num_rels_del
            }
        """).strip())

    # Execute query
    query.append("RETURN action")

    query_str = "\n".join(query)
    params.update(properties)

    result, _ = db.cypher_query(query_str, params)

    # Return the inflated StudyAction-type node (Create, Edit, Delete)
    node = result[0][0]
    node = action_type.inflate(node)
    return node
