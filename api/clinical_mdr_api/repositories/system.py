from neomodel import db


def get_neo4j_version():
    get_neo4j_version_query = """
        CALL dbms.components()
        YIELD versions
        UNWIND versions as version
        RETURN version
        """
    result, _ = db.cypher_query(query=get_neo4j_version_query)
    return result[0][0]
