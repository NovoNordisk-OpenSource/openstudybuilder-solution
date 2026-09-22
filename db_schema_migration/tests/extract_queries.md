# Queries for extracting test data

This is a collection of queries that can be used to extract test data.
Use them as they are, or modify as needed.
New queries of a generic enough nature that they might be useful again in the future
can be added here.


## Controlled terminology
Extract a codelist with some terms.
```
MATCH (clr:CTCodelistRoot {uid: 'CTCodelist_000001'})-[:HAS_NAME_ROOT]->(clnr:CTCodelistNameRoot)-[:LATEST]-(clnv)
MATCH (cl_lib:Library)-[:CONTAINS_CODELIST]->(clr)
MATCH (clr)-[:HAS_ATTRIBUTES_ROOT]->(clar:CTCodelistAttributesRoot)-[:LATEST]-(clav)
MATCH (clr)-[:HAS_TERM]-(clt:CTCodelistTerm)-[:HAS_TERM_ROOT]-(tr)
MATCH (tav:CTTermAttributesValue)-[:LATEST]-(tar:CTTermAttributesRoot)--(tr)--(tnr:CTTermNameRoot)-[:LATEST]-(tnv:CTTermNameValue)
MATCH (t_lib:Library)-[:CONTAINS_TERM]->(tr)
RETURN * LIMIT 3
```

Extract a codelist with some terms.
Similar to the previous but only includes terms that have duplicated submission values.
```
MATCH (clr:CTCodelistRoot {uid: 'C71620'})-[:HAS_NAME_ROOT]->(clnr:CTCodelistNameRoot)-[:LATEST]-(clnv)
MATCH (cl_lib:Library)-[:CONTAINS_CODELIST]->(clr)
MATCH (clr)-[:HAS_ATTRIBUTES_ROOT]->(clar:CTCodelistAttributesRoot)-[:LATEST]-(clav)
CALL {
    WITH clr
    MATCH (clr:CTCodelistRoot)-[ht:HAS_TERM]->(clt:CTCodelistTerm)
    WITH clr, collect(clt.submission_value) AS term_submvals
    WITH clr, apoc.coll.duplicates(term_submvals) AS duplicates
    WHERE size(duplicates) > 0
    RETURN duplicates
}
MATCH (clr)-[:HAS_TERM]-(clt:CTCodelistTerm)-[:HAS_TERM_ROOT]-(tr)
WHERE clt.submission_value IN duplicates
MATCH (tav:CTTermAttributesValue)-[:LATEST]-(tar:CTTermAttributesRoot)--(tr)--(tnr:CTTermNameRoot)-[:LATEST]-(tnv:CTTermNameValue)
MATCH (t_lib:Library)-[:CONTAINS_TERM]->(tr)
RETURN * LIMIT 30
```

## Data extraction queries

These are a few ways to extract test data. Pick one that fits the use case.


Generic query for extracting data as cypher statements.
Add a query that returns all the desired nodes.
All relationships between these nodes will then be added to the export automatically.
```
// Define the Cypher query to extract the relevant subgraph.
// The query needs to return all nodes to export, but not relationships.
WITH "
<< Insert query here >>
" AS cypherQuery

// Execute the query and collect nodes and relationships
CALL apoc.cypher.run(cypherQuery, {}) YIELD value
UNWIND value as row
WITH [key IN keys(row) WHERE apoc.meta.cypher.isType(row[key], "NODE") | row[key]] AS nodes_in_row
UNWIND nodes_in_row as node
WITH collect(DISTINCT node) AS all_nodes
WITH all_nodes, [node IN all_nodes | elementId(node)] AS node_ids
MATCH (n)-[rel]->(m)
WHERE elementId(n) IN node_ids
AND elementId(m) IN node_ids
WITH all_nodes, collect(DISTINCT rel) AS all_rels

// Export the nodes and relationships as cypher statements
CALL apoc.export.cypher.data(all_nodes, all_rels,
   NULL,
   { format: "plain", cypherFormat: "create", stream: true})
YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
RETURN cypherStatements
```


Example query that collects selected nodes and relationships,
and then queries for any missing nodes and relationships
in the set.
```
WITH "
CALL {
    OPTIONAL MATCH (:SyntaxInstanceRoot)-[rel1]->(:SyntaxInstanceValue)-[rel2:USES_VALUE]->(:TemplateParameterTermRoot)
    RETURN COLLECT(DISTINCT rel1) + COLLECT(DISTINCT rel2) AS col1
}
CALL {
    OPTIONAL MATCH (:SyntaxPreInstanceRoot)-[rel3]->(:SyntaxPreInstanceValue)-[rel4:USES_VALUE]->(:TemplateParameterTermValue)<-[rel5]-(:TemplateParameterTermRoot)
    RETURN COLLECT(DISTINCT rel3) + COLLECT(DISTINCT rel4) + COLLECT(DISTINCT rel5) AS col2
}
UNWIND col1 + col2 as edges_total
match (n)-[edges_total]-(m)
with collect(n)+collect(m) as all_nodes_collected
UNWIND all_nodes_collected AS all_nodes
WITH DISTINCT all_nodes
WITH collect(all_nodes) as all_nodes_collected, collect(ID(all_nodes)) AS all_nodes_id_collected
CALL{
  with all_nodes_collected,all_nodes_id_collected
  unwind all_nodes_collected as x
  match(x)-[r]-(c)
  where ID(c) in all_nodes_id_collected
  return x,r,c
  }
return x,r,c" AS query
CALL apoc.export.cypher.query(query, null, {stream: true, format: "plain",  cypherFormat: "create",ifNotExists: true})
YIELD cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize
RETURN cypherStatements, file, batches, source, format, nodes, relationships, time, rows, batchSize;
```