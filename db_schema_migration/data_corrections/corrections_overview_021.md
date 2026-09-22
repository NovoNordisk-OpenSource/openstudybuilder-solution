## Data corrections: overview of data_corrections.correction_021

PRD Data Corrections: Replace XML entities in node definition text


## 1. Correction: replace_xml_entities_in_definitions

#### Problem description
Some nodes store XML-encoded text in `definition`, such as `&#8729;` and `&#8722;`,
instead of plain characters.
#### Change description
- Replace `&#8729;` with `·` in `definition`
- Replace `&#8722;` with `-` in `definition`
- Apply the replacement only to nodes where `definition` contains `&#8729;`
#### Nodes and relationships affected
- Any node with a `definition` property containing XML entities
#### Expected changes: XML entities removed from affected `definition` values
