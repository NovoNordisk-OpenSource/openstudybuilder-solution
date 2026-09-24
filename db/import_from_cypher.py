from neo4j import GraphDatabase
from os import environ
import os
import sys

DATABASE = environ.get("NEO4J_MDR_DATABASE")
HOST = environ.get("NEO4J_MDR_HOST")
PORT = environ.get("NEO4J_MDR_BOLT_PORT")
USER = environ.get("NEO4J_MDR_AUTH_USER")
PASS =  environ.get("NEO4J_MDR_AUTH_PASSWORD")

uri = "neo4j://{}:{}".format(HOST, PORT)
driver = GraphDatabase.driver(uri, auth=(USER, PASS))

def run_queries(tx, queries):
    for q in queries:
        tx.run(q)

def build_query_until_semicolon(file, firstline=None):
    if firstline is None:
        query = file.readline()
    else:
        query = firstline
    if not query:
        return
    while not query.endswith(";\n"):
        line = file.readline()
        if line.startswith(":"):
            raise ValueError(f"Unexpected control code {line} in query")
        query = query + line
    query = query.rstrip(";\n")
    return query

def build_transaction_until_commit(file):
    queries = []
    while True:
        line = file.readline()
        if line.startswith(":commit"):
            return queries
        query = build_query_until_semicolon(file, line)
        if query is None:
            print("Warning, the file ended without closing a transaction")
            return queries
        queries.append(query)

def next_transaction(file):
    line = file.readline()
    if line.startswith(":begin"):
        queries = build_transaction_until_commit(file)
    else:
        query = build_query_until_semicolon(file, firstline=line)
        if query is None:
            return []
        queries = [query]
    return queries


if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        print("Error: no filename given!")
        sys.exit(1)
    file_stats = os.stat(filename)
    file_size = file_stats.st_size
    print(f"Importing from file '{filename}', size: {file_size/1024/1024:.1f} MB")
    with driver.session(database="system") as session:
        print(f"Creating database '{DATABASE}'")
        querystring = "CREATE DATABASE `{}` IF NOT EXISTS".format(DATABASE)
        session.write_transaction(run_queries, [querystring])
    with driver.session(database=DATABASE) as session:

        with open(filename, 'r') as file:
            nbr_tx = 0
            while True:
                queries = next_transaction(file)
                if len(queries) == 0:
                    break
                session.write_transaction(run_queries, queries)
                nbr_tx += 1
                print(f"Progress: {file.tell()/file_size:.1%}, transactions executed: {nbr_tx}", end="\r")
    driver.close()
    print("\nDone!")
