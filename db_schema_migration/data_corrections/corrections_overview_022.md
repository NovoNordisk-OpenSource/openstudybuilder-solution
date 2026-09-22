## Data corrections: overview of data_corrections.correction_022

PRD Data Corrections: Remove unused Neodash dashboard node


## 1. Correction: remove_lonely_external_data_file_spec_dashboard

#### Problem description
A single `_Neodash_Dashboard` node for "External Data File Specifications" (uuid
`6b288611-7f89-482c-a850-b34b19cf6ebb`, user `devops_adm`, date `2025-10-05 13:20:42 +0000`)
is not used anymore and should be removed.

#### Change description
- Delete that node only when all four identifying properties match **and** the node has
  no graph relationships (`NOT (d)--()`), which is used as a safety guard.

#### Nodes and relationships affected
- `_Neodash_Dashboard`: one node (properties including `uuid`, `title`, `user`, `date`,
  `content`, `version`).

#### Expected changes
Unused dashboard removed; safe to re-run (no further updates once deleted).
