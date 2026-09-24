## Data corrections: overview of data_corrections.correction_020

PRD Data Corrections: Fix Non and Unscheduled visit labels and visibility, restore CTCodelistTerm nodes



## 1. Correction: fix_non_and_unscheduled_visit_label_and_visibility

#### Problem description
Non-visit and Unscheduled-visit StudyVisit nodes have `short_visit_label` values
that are not prefixed with "V", and their `show_visit` property is not set to `false`.
#### Change description
- Prefix `short_visit_label` with "V" for all current Non and Unscheduled visits
  whose label does not already start with "V".
- Set `show_visit` to `false` for all current Non and Unscheduled visits.
#### Nodes and relationships affected
- `StudyVisit` node properties: `short_visit_label`, `show_visit`
#### Expected changes: Non and Unscheduled visits updated with "V" prefix and show_visit=false


## 2. Correction: restore_codelist_term_nodes

#### Problem description
Correction 019 Phase A (unlink non-Veeva terms from Veeva codelists) used
`DETACH DELETE clt` on CTCodelistTerm nodes. Because these nodes are shared
across multiple codelists (HAS_TERM from both Veeva and CDISC codelists),
deleting the node severed terms from ALL codelists, not just the
Veeva ones. This left 84 CDISC terms fully orphaned and destroyed 5,670
CONTAINS_SUBMISSION_VALUE relationships from CTPackageTerm nodes.
#### Change description
- Read the correction 019 change log to identify deleted CTCodelistTerm nodes
  and their original relationships (skipping 13 whose codelists were all deleted)
- Recreate each CTCodelistTerm node with its submission_value
- Restore HAS_TERM_ROOT relationships to CTTermRoot
- Restore HAS_TERM relationships to CTCodelistRoot nodes that still exist
- Restore CONTAINS_SUBMISSION_VALUE relationships from CTPackageTerm nodes
#### Nodes and relationships affected
- `CTCodelistTerm` (recreated via MERGE)
- `HAS_TERM_ROOT` (CTCodelistTerm -> CTTermRoot)
- `HAS_TERM` (CTCodelistRoot -> CTCodelistTerm, with author_id/start_date/order/end_date)
- `CONTAINS_SUBMISSION_VALUE` (CTPackageTerm -> CTCodelistTerm)
#### Expected changes: up to 95 CTCodelistTerm nodes restored with all relationships
