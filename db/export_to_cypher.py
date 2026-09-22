from neo4j import GraphDatabase
from os import environ

DATABASE = environ.get("NEO4J_MDR_DATABASE")
HOST = environ.get("NEO4J_MDR_HOST")
PORT = environ.get("NEO4J_MDR_BOLT_PORT")
USER = environ.get("NEO4J_MDR_AUTH_USER")
PASS =  environ.get("NEO4J_MDR_AUTH_PASSWORD")

uri = "neo4j://{}:{}".format(HOST, PORT)
driver = GraphDatabase.driver(uri, auth=(USER, PASS))

print("Dumping database contents as cypher statements")
def get_data(tx):
    result = tx.run("CALL apoc.export.cypher.all(null, {streamStatements: true, batchSize: 1000, format: 'cypher-shell', saveIndexNames: true, saveConstraintNames: true, multipleRelationshipsWithType: true})")
    return result.data()

with driver.session(database=DATABASE) as session:
    print(f"Connecting to database '{DATABASE}' on host: {HOST}")
    nbr_nodes = session.read_transaction(lambda tx: tx.run("MATCH (n) RETURN count(n) as nbr_nodes").single().get("nbr_nodes"))
    nbr_rels = session.read_transaction(lambda tx: tx.run("MATCH ()-[r]-() RETURN count(r) as nbr_rels").single().get("nbr_rels"))
    print(f"Database contains {nbr_nodes} nodes and {nbr_rels} relationships")
    print("Requesting data")
    data = session.read_transaction(get_data)
    print(f"Saving data to 'dump-{DATABASE}.cypher'")
    with open(f"dump-{DATABASE}.cypher", "w") as f:
        for chunk in data:
            f.write(chunk['cypherStatements'])

driver.close()
print("Done!")
