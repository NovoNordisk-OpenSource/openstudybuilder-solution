## Data corrections: overview of data_corrections.correction_019

PRD Data Corrections: Remove Veeva-imported codelists and terms



## 1. Correction: remove_veeva_codelists

#### Problem description
The initial import of ODM data from Veeva created 301 codelists in the library.
When the ODM data was wiped, these codelists were left behind and need to be removed.
Some Veeva codelists contain non-Veeva terms that must be unlinked before deletion.
Runs after term deletion so codelists with remaining protected terms are preserved.
#### Change description
- Phase A: Unlink non-Veeva terms from Veeva codelists (remove CTCodelistTerm junctions)
- Phase B: Delete Veeva codelists that have no remaining terms
#### Nodes and relationships affected
- `CTCodelistRoot`, `CTCodelistNameRoot`, `CTCodelistNameValue`
- `CTCodelistAttributesRoot`, `CTCodelistAttributesValue`
- `CTCodelistTerm` (junction nodes)
#### Expected changes: Veeva codelists with no remaining terms deleted


## 2. Correction: remove_veeva_terms

#### Problem description
The initial import of ODM data from Veeva created 652 terms in the library.
When the ODM data was wiped, these terms were left behind and need to be removed.
6 terms have active CTTermContext references (UnitDefinitionValue/ActivityItem) and must
be preserved.
#### Change description
- Step 1: Identify protected terms (those referenced by CTTermContext nodes that
  themselves have incoming relationships, i.e. are actually used by studies/concepts)
- Step 2: Delete all unprotected Veeva terms (CTTermRoot + name/attributes sub-trees
  + CTCodelistTerm junctions + orphaned CTTermContext nodes)
#### Nodes and relationships affected
- `CTTermRoot`, `CTTermNameRoot`, `CTTermNameValue`
- `CTTermAttributesRoot`, `CTTermAttributesValue`
- `CTCodelistTerm` (junction nodes linking terms to non-Veeva codelists)
- `CTTermContext` (orphaned nodes with no incoming relationships)
#### Expected changes: 646 terms deleted, 6 terms preserved