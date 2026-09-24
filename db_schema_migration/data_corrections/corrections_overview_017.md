## Data corrections: overview of data_corrections.correction_017

PRD Data Corrections: Before Release 2.5



## 1. Correction: fix_duplicated_unique_visit_numbers_and_incorrect_visit_number_visit_name_and_short_name

#### Problem description
There exists an issue that some different StudyVisits share the same unique visit number.
It should not be the case as unique visit number should be a unique value across all StudyVisits within a Study.
The issue existed only for groups of subvisits when the anchor visit timing was edited and it was not properly updated.
#### Change description
- Update unique visit number and other properties (visit_name, short_visit_label, visit_number) for StudyVisits having wrong values
- Correct values are taken from API that calculates them based on the StudyVisit full schedule.
#### Nodes and relationships affected
- `StudyVisit` node
#### Expected changes: 2 StudyVisits (StudyVisit_004596, StudyVisit_009676) updated by correcting (visit_number, unique_visit_number, short_visit_label) properties and relationship to dependent visit_name node


## 2. Correction: remove_duplicated_non_visit_and_unscheduled_visits

#### Problem description
There should only exist one Non-visit and Unscheduled-visit in a given Study.
There was an API issue that when both Non-visit and Unscheduled-visit existed in given Study and we were editing
Non-visit to be Unscheduled-visit or vice versa, the API allowed to created duplicated Non or Unscheduled visit by edition.
#### Change description
- Delete duplicated Non-visit or Unscheduled-visit in the Study.
#### Nodes and relationships affected
- `StudyVisit` node
#### Expected changes: 1 call for DELETE /study-visits/{StudyVisit_000196} to delete duplicated non-visit.


## 3. Correction: rebuild_missing_protocol_soa_snapshots

### Problem description
Some (RELEASED) Study versions do not have a Protocol SoA snapshot created due to a (fixed) bug.
### Change description
- Rebuild missing/failing Protocol SoA snapshots for RELEASED Study versions, using contemporary StudySelections but latest ordering.
### Relationships affected
- (StudyValue)-[:HAS_PROTOCOL_SOA_CELL]->(StudySelection)
- (StudyValue)-[:HAS_PROTOCOL_SOA_FOOTNOTE]->(StudySelection)
### Expected changes
- Old relationships removed
- New relationships created



## 4. Correction: remove_study_action_with_broken_after

#### Problem description
Some StudyAction nodes exist without AFTER relationships. These are leftover from migrated study selections
where the StudySelection nodes were deleted but the StudyAction nodes remained. Every StudyAction (except
UpdateSoASnapshot) must have an AFTER relationship.
#### Change description
- Delete StudyAction nodes that don't have AFTER relationships (excluding UpdateSoASnapshot nodes).
#### Nodes and relationships affected
- `StudyAction` nodes



## 5. Correction: remove_soa_cell_relationships_without_released_study

#### Problem description
Some StudyValue nodes have HAS_PROTOCOL_SOA_CELL or HAS_PROTOCOL_SOA_FOOTNOTE relationships
when the StudyRoot doesn't have a RELEASED or LOCKED version. These relationships were created
as a result of bad cloning and should not exist without a released or locked version.
#### Change description
- Delete HAS_PROTOCOL_SOA_CELL and HAS_PROTOCOL_SOA_FOOTNOTE relationships from StudyValue nodes
  where the StudyRoot doesn't have a RELEASED or LOCKED version
#### Nodes and relationships affected
- `HAS_PROTOCOL_SOA_CELL` relationships
- `HAS_PROTOCOL_SOA_FOOTNOTE` relationships
