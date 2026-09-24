DEFINITION_XML_CODES = """
UNWIND [
    {uid: 1, properties: {name: "node_1", definition: "Alpha &#8729; beta &#8722; gamma"}},
    {uid: 2, properties: {name: "node_2", definition: "One more &#8729; sample"}},
    {uid: 3, properties: {name: "node_3", definition: "No xml entities here"}}
] AS row
MERGE (n:XmlDefinitionCleanupNode {uid: row.uid}) SET n += row.properties;
"""

TEST_DATA = DEFINITION_XML_CODES
