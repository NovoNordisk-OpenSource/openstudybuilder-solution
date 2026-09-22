# Data Corrections: Applied to PRD after release 2.0.1

## 1. Remove orphan ActivityInstance nodes

### Problem description
- There are orphan ActivityInstance nodes in the database that need to be removed.
- These nodes were created because of a bug where we would create Root and Value nodes, then the operation would be aborted because of a business rule violation, and it was happening outside of a transaction, hence the nodes were not deleted.

### Change description
- Delete orphan ActivityInstance nodes - Root and Value.
- Execute two specific Cypher queries to identify and remove these orphan nodes.

### Nodes and relationships affected
- `ActivityInstanceRoot` nodes
- `ActivityInstanceValue` nodes

## 2. Remove orphan ActivityInstanceClass nodes

### Problem description
- There are orphan ActivityInstanceClassValue nodes in the database that need to be removed.
- The source bug has not been identified yet, but it seems probably related to some bad migrations in the past.

### Change description
- Delete orphan ActivityInstanceClassValue nodes.
- Execute one specific Cypher query to identify and remove these orphan nodes.

### Nodes and relationships affected
- `ActivityInstanceClassValue` nodes


## 3. Remove orphan StudyField nodes

### Problem description
- There are orphan StudyField nodes in the database that need to be removed.
- The source bug has not been identified yet, but it seems probably related to some bad migrations in the past.

### Change description
- Delete orphan StudyField nodes.

### Nodes and relationships affected
- `StudyField` nodes


## 4. Fix ActivityInstances connected to multiple Activity nodes

### Problem description
- There are ActivityInstanceValue nodes that are connected to multiple ActivityValue nodes through ActivityGrouping.
- This is not allowed and needs to be fixed.

### Change description
- Delete offending, extra relationships between ActivityInstanceValue and ActivityGrouping nodes.

### Nodes and relationships affected
- `HAS_ACTIVITY` relationships

## 5. Remove unwanted studies

### Problem description
Some studies have been created by mistake in the production environment.
These occupy some Study IDs and cause confusion.
There are also unused template studies that are outdated and should be removed
to avoid confusion.

### Change description
Delete all nodes and relationships related to the following studies:
- 80_35_DELETE
- 85_09_DELETE
- 85_62_DELETE
- 82_66_DELETE
- 80_34_DELETE
- 79_10_DELETE
- 79_11_DELETE
- 0030
- 0050

### Nodes and relationships affected
- All study nodes for the studies where the study number has a _DELETE:
- Expected changes: ~500 nodes deleted, ~1000 relationships deleted


## 6. Remove three unwanted sponsor terms.

### Problem description
The database contains a few sponsor terms that were added by mistake.
The UIDs of the unwanted terms are:
- CTTerm_001775
- CTTerm_001776
- CTTerm_001777

### Change Description
The three unwanted terms need to be removed from the database,
including all nodes and relationships related to these terms.

### Nodes and relationships affected
- All nodes and relationships related to the unwanted terms are deleted:
  - Term root: `CTTermRoot`,
  - Term names: `CTTermNameRoot`, `CTTermNameValue`, `HAS_NAME_ROOT`, `HAS_VERSION`
  - Term attributes: `CTTermAttributesRoot`, `CTTermAttributesValue`, `HAS_ATTRIBUTES_ROOT`, `HAS_VERSION`
  - Term-codelist linking: `CTCodelistTerm`, `HAS_TERM`, `HAS_TERM_ROOT`
  - Expected changes: 26 nodes deleted, 44 relationships deleted


## 7. Remove dummy definitions for concept values

### Problem description
In earlier versions of StudyBuilder, the `definition` field
for concepts was set as mandatory. This led to many concepts created with dummy
values for the definition such as "x", ".." or "TBD".
The field is now optional, and these dummy values should be removed.

### Change dscription
The dummy definitions are removed from the concept value nodes.

### Nodes and relationships affected
- The `definition` field of
  - `ActivityValue`, `ActivityGroupValue`, `ActivitySubGroupValue`, `ActivityInstanceValue`
  - `UnitDefinitionValue`
- Expected changes: approximately 3000 properties removed


## 8. Correct Baseline 2 Visit Type term

### Problem description
The Baseline 2 term is linked twice to the VisitType codelist, due to a bug in the data migration
for the new CT model in release 2.0.
This needs to be corrected by setting an end date for the unwanted link.

### Change desciption
- Look up the change date by getting the start date for version 1.3 of the term attributes.
- Set an end date for the `HAS_TERM` relationship for the "BASELINE 2" submission value
- Adjust the start date of the `HAS_TERM` relationship for the "BASELINE 2 VISIT TYPE" submission value.
- Expected changes: 1 relationship property added, 1 modified


## 9. Study Selection Not mantained relationships

### Problem description
In the current database schema, certain relationships between `StudySelection` nodes may be inadvertently dropped
when `StudyAction` nodes are created or deleted. This can lead to loss of important connections that define
the timeline of changes (Audit trail) of study selections.
Specifically, relationships such as `STUDY_EPOCH_HAS_STUDY_VISIT`, `STUDY_VISIT_HAS_SCHEDULE`,
and others may not be properly maintained during these operations.
### Change description
- Identify and restore any dropped relationships between `StudySelection` nodes
  that should be maintained based on the temporal context provided by `StudyAction` nodes.
- Ensure that the relationships are only restored when they are temporally relevant, i.e.,
  when the `StudySelection` nodes are active during the same time period as defined by the `StudyAction` nodes.
- Use temporal logic to determine the validity of relationships based on the dates associated with the `StudyAction` nodes.

### Nodes and relationships affected
- `StudySelection` nodes
- Relationships: `STUDY_EPOCH_HAS_STUDY_VISIT`, `STUDY_VISIT_HAS_SCHEDULE`, `STUDY_EPOCH_HAS_DESIGN_CELL`,
  `STUDY_ACTIVITY_HAS_SCHEDULE`, `STUDY_ACTIVITY_HAS_INSTRUCTION`, `STUDY_ELEMENT_HAS_DESIGN_CELL`, `STUDY_ARM_HAS_BRANCH_ARM`


## 10. Correct author id for CDISC data

### Problem description
The new CDISC import script has imported the data using the old "user_intitals" property
instead of the new "author_id" on `HAS_VERSION` relationships.
On `HAS_TERM` relationships the field is missing completely.
The author id for these should always be the "sb-import" user.

### Change description
- Find the author id for the "sb-import" user
- Add the id for this user in the `author_id` property on all `HAS_TERM` and `HAS_VERSION` relationships
  and `CTPackage` nodes where it is missing.
- Remove all `user_initials` properties.

### Expected changes
- approx. 200 000 properties updated


## 11. Correct selected term for null flavor reason

### Problem description
The migration script for the new CT model mistakenly created a second `CTTermContext`
node linked to a `StudyTextField` via a `HAS_REASON_FOR_NULL_VALUE` relationship.
This links to a null value term in the wrong codelist, and should be removed.

### Change description
- Find `StudyTextField` nodes with more than one `HAS_REASON_FOR_NULL_VALUE` relationships.
- Remove the unwanted `HAS_REASON_FOR_NULL_VALUE` relationship and the corresponding `CTTermContext` node.
- Expected changes: 1 node deleted, 3 relationships deleted.
