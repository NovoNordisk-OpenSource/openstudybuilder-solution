import unittest

from neomodel import db

from clinical_mdr_api.domain_repositories.models.syntax import (
    EndpointRoot,
    ObjectiveRoot,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db


class TestUIDAssignment(unittest.TestCase):
    dbname = "uidassignmenttest"

    def setUp(self):
        inject_and_clear_db(self.dbname)

    @db.transaction
    def get_all_nodes_by_label(self, label):
        return db.cypher_query(f"""
        MATCH (n:{label})
        RETURN n.uid
        """)

    @db.transaction
    def create_some_nodes_with_neomodel(self):
        EndpointRoot().save()
        EndpointRoot().save()
        ObjectiveRoot().save()

    @db.transaction
    def create_some_more_nodes_with_neomodel(self):
        EndpointRoot().save()
        EndpointRoot().save()
        ObjectiveRoot().save()

    @db.transaction
    def create_some_custom_uid_nodes_with_neomodel(self):
        EndpointRoot(uid="MIKE_UID").save()
        EndpointRoot(uid="MARY_UID").save()
        ObjectiveRoot(uid="MARY_UID").save()

    @db.transaction
    def create_some_custom_uid_nodes_with_cypher(self):
        db.cypher_query("CREATE (n:EndpointRoot {uid: 'ERIC_UID'})")
        db.cypher_query("CREATE (n2:EndpointRoot {uid: 'KYLE_UID'})")
        db.cypher_query("CREATE (n3:ObjectiveRoot {uid: 'KYLE_UID'})")
        EndpointRoot.generate_node_uids_if_not_present()
        ObjectiveRoot.generate_node_uids_if_not_present()

    @db.transaction
    def create_some_nodes_with_cypher(self):
        db.cypher_query("CREATE (n:EndpointRoot)")
        db.cypher_query("CREATE (n2:EndpointRoot)")
        db.cypher_query("CREATE (n3:ObjectiveRoot)")
        EndpointRoot.generate_node_uids_if_not_present()
        ObjectiveRoot.generate_node_uids_if_not_present()

    @db.transaction
    def create_some_more_nodes_with_cypher(self):
        db.cypher_query("CREATE (n:EndpointRoot)")
        db.cypher_query("CREATE (n2:EndpointRoot)")
        db.cypher_query("CREATE (n3:ObjectiveRoot)")
        EndpointRoot.generate_node_uids_if_not_present()
        ObjectiveRoot.generate_node_uids_if_not_present()

    def test__assign_multiple_uids_in_single_transaction_neomodel(self):
        self.create_some_nodes_with_neomodel()
        self.create_some_more_nodes_with_neomodel()

        self.assertEqual(
            self.get_all_nodes_by_label("ObjectiveRoot")[0],
            [["Objective_000001"], ["Objective_000002"]],
        )
        self.assertEqual(
            self.get_all_nodes_by_label("EndpointRoot")[0],
            [
                ["Endpoint_000001"],
                ["Endpoint_000002"],
                ["Endpoint_000003"],
                ["Endpoint_000004"],
            ],
        )

    def test__assign_multiple_uids_in_single_transaction_cypher(self):
        self.create_some_nodes_with_cypher()
        self.create_some_more_nodes_with_cypher()

        self.assertEqual(
            self.get_all_nodes_by_label("ObjectiveRoot")[0],
            [["Objective_000001"], ["Objective_000002"]],
        )
        self.assertEqual(
            self.get_all_nodes_by_label("EndpointRoot")[0],
            [
                ["Endpoint_000001"],
                ["Endpoint_000002"],
                ["Endpoint_000003"],
                ["Endpoint_000004"],
            ],
        )

    def test__automatic_uid_generation_does_not_override_manual_uid_neomodel(self):
        self.create_some_custom_uid_nodes_with_neomodel()

        self.assertEqual(
            self.get_all_nodes_by_label("ObjectiveRoot")[0], [["MARY_UID"]]
        )
        self.assertEqual(
            self.get_all_nodes_by_label("EndpointRoot")[0], [["MIKE_UID"], ["MARY_UID"]]
        )

    def test__automatic_uid_generation_does_not_override_manual_uid_cypher(self):
        self.create_some_custom_uid_nodes_with_cypher()

        self.assertEqual(
            self.get_all_nodes_by_label("ObjectiveRoot")[0], [["KYLE_UID"]]
        )
        self.assertEqual(
            self.get_all_nodes_by_label("EndpointRoot")[0], [["ERIC_UID"], ["KYLE_UID"]]
        )
