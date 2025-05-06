# Solution Strategy

The CDISC CT data is imported into the _intermediate_ CDISC CT
<a href="https://neo4j.com" target="_blank">Neo4j</a> Graph DB.

During that first import phase, most of the CDISC CT structure is taken over and directly transformed into
the graph structure.
However, it is important to note that the CDISC CT term structure is transformed/adjusted so that it
reflects the differentiation between code and name submission value for the terms.

Inconsistencies are automatically detected and - if possible - automatically resolved.
The (remaining) inconsistencies and the resolved inconsistencies are stored in the CDISC CT Neo4j Graph DB
so that they can be displayed in an Admin UI for manual review, approval and/or further resolutions.

The user then manually accepts the adjusted CDISC CT Graph structure and triggers the import into the
MDR DB.


## CDISC CT DB Schema (the _intermediate_ Neo4j DB)

This section explains the Neo4j schema used for the _intermediate_ database.

- Per effective date, there will be one `Import` node pointing to the imported data at this date.
- The nodes marked in <span style="background-color: #b7c9e3;">blue</span> are referring to the core concepts of the CDISC CT.
- The nodes marked in <span style="background-color: #eada00;">yellow</span> are referring to inconsistencies. These enrich the original CDISC CT data for easy investigation and resolution.
- The nodes marked in <span style="background-color: #99cc00;">green</span> define the resolution rules that tell how to deal with potential inconsistencies.

[![CDISC CT DB Schema](~@source/images/cdisc/cdisc-ct-schema.svg)](../../images/cdisc/cdisc-ct-schema.svg)
<small>Figure 1: <a href="https://neo4j.com" target="_blank">Neo4j</a> - CDISC CT DB Schema</small>

### Node Labels

#### Import [+ Running]

The high-level entry point to one specific import of an effective date.

- The label `Running` is added if the import is currently ongoing. It will be removed once the import is done.

- Properties:
    - `effective_date: Date` - The CDISC effective date. 
    - `import_date_time: DateTime` - The date and time when the import was executed.
    - `author_id: String` - The ID of the user that triggered the import.
    - `automatic_resolution_done: Boolean` - Denotes whether or not the automatic resolution of inconsistencies was run for that import.


#### Package (<span style="background-color: #b7c9e3;">core concept</span>)

Represents a CDISC CT catalogue **at a specific effective date**.

NODE KEY:
- `name`

- Relationships:
    - `CONTAINS (Outgoing, 0..*)`: A package contains an arbitrary number of codelists.
      - Properties:
        - `inconsistent_term_concept_ids: Array<String>` - This property does only exist if there is an inconsistency. In that case, it includes the concept ids (strings) of those terms that are contained in the codelist (end node).

#### Codelist (<span style="background-color: #b7c9e3;">core concept</span>)

Represents a CDISC CT codelist **at a specific effective date**.

NODE KEY:
- `effective_date`
- `concept_id`

#### Term (<span style="background-color: #b7c9e3;">core concept</span>)

Represents a CDISC CT term **at a specific effective date**.

NODE KEY:
- `effective_date`
- `concept_id`
- `code_submission_value`

**Note:**
The `<term code submission value>` is part of the unique identifier of a `Term` node.


#### Inconsistency | ResolvedInconsistency (<span style="background-color: #eada00;">inconsistency concept</span>)

The two labels `Inconsistency` and `ResolvedInconsistency` are mutual exclusive.
`Inconsistency` is used to denote a detected inconsistency in the data. Once that inconsistency has been resolved (either by automatic resolution or by manual review and resolution) the `Inconsistency` label is removed and the `ResolvedInconsistency` label is added. The properties and relationships remain the same.

- Properties:
    - `date_time: Datetime` - The date and time when this message was written into the DB.
    - `tagline: String` - A short summary of the inconsistency.
  It can be seen as a category of the message. See the section [Inconsistencies](#inconsistencies) for details.
    - `message: String` - The log message itself with an explanation of why we think
  there is an unexpected value or even an inconsistency. See the section [Inconsistencies](#inconsistencies) for details.
    - `comment: String` - Either the standard message from the automatic resolution step or a user comment provided e.g. via the Admin UI.
    - `author_id: String` - The standard user ID from the automatic resolution step or the ID of the user that resolved the inconsistency.
- Relationships:
    - `HAS (Incoming, 1)`: An `Inconsistency` node is always connected to the corresponding `Import` node **and** one of the following nodes (depending on which level the inconsistency was introduced): `Package` node **or** `Codelist` node **or** `Term` node.
    Although an inconsistency may affect multiple levels (e.g. a codelist and multiple packages), the connection to the higher concept is not explicitly stored on the `Inconsistency` nodes.


#### InconsistentAttributes (<span style="background-color: #eada00;">inconsistency concept</span>)

An `InconsistentAttributes` node will only exist if there are differences (inconsistencies)
within the attributes of one specific term (or codelist). If it exists, there will be always at least one
other `InconsistentAttributes` node with different attributes for the same term (or codelist).
If no `InconsistentAttributes` node exist, the `Term` (or `Codelist`) node contains consistent attributes.

- Properties: a subset of the properties of the `Term` or `Codelist` node.


#### InconsistentTermSubmissionValue (<span style="background-color: #eada00;">inconsistency concept</span>)

An `InconsistentTermSubmissionValue` node will only exist if there are inconsistencies within the submission values.


#### CataloguePriority (<span style="background-color: #99cc00;">resolution configuration</span>)

This is part of the resolution configuration.

It is expected to only have **one node** with that label in the database that defines the catalogue priorities!

- Properties:
    - `catalogue_names: String[]`: An ordered list (higher priorities come first in the list) of cataluge names. The names need to match those names defined by CDISC. Valid names include e.g.: 'SDTM CT', 'ADaM CT', ..


#### Resolution (<span style="background-color: #99cc00;">resolution configuration</span>)

This is part of the resolution configuration.

- Properties:
    - `order: Integer`: Specifies the order in which the existing resolutions will be applied. Lower numbers will be applied first.
    - `action: String`: Specified the resolution path. Valid actions are defined in TODO: add reference.
    - `valid_for_taglines: String[] (Optional)`: If specified, the resolution is only applied to inconsistencies tagged with one of these taglines.
    - `valid_for_concept_ids: String[] (Optional)`: If specified, the resolution is only applied to those concept ids specified here. If omitted, the resolution is valid for all concept ids (except `invalid_for_concept_ids` contains exclusions). `valid_for_concept_ids` overrules `invalid_for_concept_ids`.
    The values of the array refer either to the values of the `concept_id` property of `Term` or `Codelist` nodes or the `catalogue_name` property of `Package` nodes.
    - `invalid_for_concept_ids: String[] (Optional)`: If specified, the resolution is applied to all concept ids except for the ones specified here. Mutual exclusive with `valid_for_concept_ids` (see description there).
    The values of the array refer either to the values of the `concept_id` property of `Term` or `Codelist` nodes or the `catalogue_name` property of `Package` nodes.

## Inconsistent Data

The CDISC CT data might contain inconsistencies. The known inconsistencies are categorized as follows:

### Categorization

| Tagline                                           | Message Template |
| :------------------------------------------------ | :----------------|
| no codelists in package                           | The package with the name='{name}' does not have any codelists; href='{href}'. |
| inconsistent codelist attributes                  | The codelist with the conceptId='{codelist_concept_id}' has inconsistent attributes across different packages; packages={package_names}. |
| inconsistent term attributes                      | The term with the conceptId='{term_concept_id}' has inconsistent attributes across different codelists; codelists={codelist_concept_ids}; packages={package_names}. |
| inconsistent terms                                | The codelist with the conceptId='{codelist_concept_id}' has an inconsistent set of terms defined across different packages; packages={package_names}. |
| unexpected codelist name                          | The name='{name}' of the codelist with the conceptId='{codelist_concept_id}' indicates that there is a second codelist with the expectedName='{expected_other_name}'. However, we could not find such a second codelist. |
| inconsistent term submission values | The term with the conceptId='{term_concept_id}' has an inconsistent set of submission value defined; codelist='{codelist_concept_id}', packages={package_names}. |


### Resolution

The resolution of inconsistencies is split into the following steps:
- [Automatic Resolution](/guides/cdisc/building-blocks.html#automatic-resolution-of-inconsistencies) and
- [Manual Review & Resolution](/guides/cdisc/building-blocks.html#manual-review-resolution-through-an-admin-ui)


#### Actions

The following actions are defined and can be specified for the automatic and the manual resolution:

| Action | Description | Valid for taglines |
| :----- | :---------- | :----------------- |
| `catalogue-priority`     | Applies the catalogue priority according to the `CataloguePriority` node and marks the inconsistency as resolved. | `inconsistent codelist attributes`, `inconsistent term attributes`, `inconsistent term submission values` |
| `merge-terms` | Takes over both terms, keeps the package structure and marks the inconsistency as resolved. | `inconsistent terms` |
| `ignore` | Ignores the inconsistency and marks it as resolved. | *all* |


