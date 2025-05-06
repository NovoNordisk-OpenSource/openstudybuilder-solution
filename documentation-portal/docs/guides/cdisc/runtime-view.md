# Runtime View

[![Runtime View Scope](~@source/images/cdisc/runtime_view/runtime-view-scope.svg)](../../images/cdisc/runtime_view/runtime-view-scope.svg)


## Import CDISC CT into CDISC CT DB

[![Image: Import CDISC CT into CDISC CT DB](~@source/images/cdisc/runtime_view/import-cdisc-ct-into-cdisc-ct-db-level-1.svg)](../../images/cdisc/runtime_view/import-cdisc-ct-into-cdisc-ct-db-level-1.svg)


### Download JSON data from CDISC API

[![Image: Download JSON data from CDISC API](~@source/images/cdisc/runtime_view/import-cdisc-ct-into-cdisc-ct-db-level-2-download.svg)](../../images/cdisc/runtime_view/import-cdisc-ct-into-cdisc-ct-db-level-2-download.svg)


### Import JSON data into CDISC CT DB

**Output of this step:**

One `Import` node that holds all the information of the CDISC
data for the specified effective date.

So, all JSON package files have been combined under that node.
All detected and automatically resolved inconsistencies are also linked to that node.

[![Image: Import JSON data into CDISC CT DB](~@source/images/cdisc/runtime_view/import-cdisc-ct-into-cdisc-ct-db-level-2-import.svg)](../../images/cdisc/runtime_view/import-cdisc-ct-into-cdisc-ct-db-level-2-import.svg)


#### Process all JSON package files

This step reads the JSON package files and loads them into memory.

Once this step is done, the JSON files are no longer needed for further processing.

[![Image: Process all package files.](~@source/images/cdisc/runtime_view/import-cdisc-ct-into-cdisc-ct-db-level-3-package-files.svg)](../../images/cdisc/runtime_view/import-cdisc-ct-into-cdisc-ct-db-level-3-package-files.svg)


#### Load package data

[![Image: Load package data](~@source/images/cdisc/runtime_view/import-cdisc-ct-into-cdisc-ct-db-level-4-load-package-data.svg)](../../images/cdisc/runtime_view/import-cdisc-ct-into-cdisc-ct-db-level-4-load-package-data.svg)


#### Differentiate between code/name submission value for terms

This step
- sets the `code_submission_value` and `name_submission_value` properties of the `Term` nodes,
- renames the `uid` property of those `Term` nodes where only one code submission value exists and
- duplicates those `Term` nodes and renames the `uid` properties accordingly where two or more code submission values exist.

[![Image: Differentiate between code/name submission value for terms (1)](~@source/images/cdisc/runtime_view/import-cdisc-ct-into-cdisc-ct-db-level-4-code-name-sv-1.svg)](../../images/cdisc/runtime_view/import-cdisc-ct-into-cdisc-ct-db-level-4-code-name-sv-1.svg)

[![Image: Differentiate between code/name submission value for terms (2)](~@source/images/cdisc/runtime_view/import-cdisc-ct-into-cdisc-ct-db-level-4-code-name-sv-2.svg)](../../images/cdisc/runtime_view/import-cdisc-ct-into-cdisc-ct-db-level-4-code-name-sv-2.svg)

#### Detect inconsistencies

[![Image: Detect inconsistencies and store them in the DB](~@source/images/cdisc/runtime_view/import-cdisc-ct-into-cdisc-ct-db-level-3-inconsistencies.svg)](../../images/cdisc/runtime_view/import-cdisc-ct-into-cdisc-ct-db-level-3-inconsistencies.svg)



### Resolve inconsistencies automatically

[![Image: Automatic Resolution of Inconsistencies](~@source/images/cdisc/runtime_view/import-cdisc-ct-into-cdisc-ct-db-level-3-automatic-resolution.svg)](../../images/cdisc/runtime_view/import-cdisc-ct-into-cdisc-ct-db-level-3-automatic-resolution.svg)


## Manual Review & Resolution through an Admin UI

TODO: design, document and implement the Admin UI

### Manual Data Validation

```cypher
// Per tagline: get x (adjust the LIMIT) random inconsistencies for graph view
USE `cdisc-ct`
MATCH (import:Import)-[:HAS]->(log)
WHERE import.effective_date=date('2021-09-24')
// AND log.tagline = 'inconsistent term submission values'
WITH DISTINCT import, log.tagline AS tagline

CALL {
    WITH import, tagline
    MATCH path=(import)-[:HAS]->(log{tagline: tagline})-->()
    RETURN path LIMIT 1
}
RETURN import, path
```

```cypher
// Per tagline: get 3 random inconsistencies for table view
USE `cdisc-ct`
MATCH (import:Import)-[:HAS]->(log)
WHERE import.effective_date=date('2021-09-24')
WITH DISTINCT import, log.tagline AS tagline

CALL{
    WITH import, tagline
    MATCH (import)-[:HAS]->(log{tagline: tagline})-->(affected_concept)
    RETURN log, affected_concept LIMIT 3
}
RETURN
    import.effective_date AS effective_date,
        labels(affected_concept)[0] + ': '
        + coalesce(affected_concept.concept_id, affected_concept.catalogue_name)
        AS affected_concept,
    log.tagline AS tagline,
    log.message AS message
ORDER BY tagline
```

```cypher
// Per import: list the taglines including the number of occurrences
USE `cdisc-ct`
MATCH (import:Import)
// WHERE import.effective_date=date('2021-09-24')
WITH import
ORDER BY import.effective_date DESC
CALL { WITH import
    MATCH (import)-[:HAS]->(log:Inconsistency)
    RETURN log.tagline AS tagline, count(*) AS num
    ORDER BY num DESC
}
RETURN import.effective_date AS effective_date, tagline, num
```

```cypher
// return x examples for specific taglines
USE `cdisc-ct`
MATCH (log:Inconsistency)
WHERE log.tagline IN ['inconsistent term submission values', '..']
WITH log LIMIT 10
MATCH path=(:Import)-[:HAS]->(log)-->()
RETURN path
```


## Import from CDISC CT DB into MDR DB

[![Image: Import from CDISC CT DB into MDR DB](~@source/images/cdisc/runtime_view/import-into-mdr-level-1.svg)](../../images/cdisc/runtime_view/import-into-mdr-level-1.svg)


### Retire Codelists

[![Image: Retire Codelists](~@source/images/cdisc/runtime_view/import-into-mdr-level-2-retire-codelists.svg)](../../images/cdisc/runtime_view/import-into-mdr-level-2-retire-codelists.svg)


### Merge Structure Nodes

[![Image: Merge Structure Nodes](~@source/images/cdisc/runtime_view/import-into-mdr-level-2-merge-structure-nodes.svg)](../../images/cdisc/runtime_view/import-into-mdr-level-2-merge-structure-nodes.svg)


### Update HAS_TERM and HAD_TERM

[![Image: Update HAS_TERM and HAD_TERM](~@source/images/cdisc/runtime_view/import-into-mdr-level-2-update-has-and-had-term.svg)](../../images/cdisc/runtime_view/import-into-mdr-level-2-update-has-and-had-term.svg)


### Update attributes

[![Image: Update codelist & term attributes](~@source/images/cdisc/runtime_view/import-into-mdr-level-2-update-attributes.svg)](../../images/cdisc/runtime_view/import-into-mdr-level-2-update-attributes.svg)


#### Initialization of the sponsor-specific names

**For newly added codelists:**

Create `CTCodelistNameValue` nodes and set the
- `name` property to the value of the `name` property of the corresponding `CTCodelistAttributesValue` node.

**For newly added terms:**

Create `CTTermNameValue` nodes and set the
- `name` property to the value of the `preferred_term` property
of the corresponding `CTTermAttributesValue` node and the
- `name_sentence_case` property to the value of the `preferred_term` property transformed to the sentence case.


### Validating the MDR Import

```cypher
// list term concept ids with their code submission values (identified by the uid property)
MATCH (term:CTTermRoot)
WITH split(term.uid, '_') AS uid_splits
WITH uid_splits[0] AS concept_id, uid_splits[1] AS code_submission_value
WITH concept_id, collect(code_submission_value) AS code_submission_values
RETURN concept_id, code_submission_values
ORDER BY size(code_submission_values) DESC
LIMIT 100
```

