# Data Corrections: Applied to PRD after release 1.11.2

## 1. Remove duplicated ACTIVITY_INSTANCE_CLASS relationships

### Problem description
A few `ActivityInstanceValue` nodes have multiple `ACTIVITY_INSTANCE_CLASS` relationships to the same `ActivityClassRoot` node.
This makes a few api endpoints fail.

### Change description
- The duplicated relationships are removed, keeping only one.

### Nodes and relationships affected
- `ACTIVITY_INSTANCE_CLASS` relationships between `ActivityInstanceValue` and `ActivityClassRoot` nodes.
- Expected changes: 21 relationships removed.

## 2. Add relationship to an Activity for Activity Instance where it's missing

### Problem description
A few old `ActivityInstanceValue` nodes are missing a `HAS_ACTIVITY` relationship to an `ActivityGrouping` node.
This makes a few api endpoints fail.

### Change description
- The `HAS_ACTIVITY` relationship is created for the affected nodes,
  linking to the same `ActivityGrouping` node as the next version of the activity instance.

### Nodes and relationships affected
- `HAS_ACTIVITY` relationships between `ActivityInstanceValue` and `ActivityGrouping` nodes.
- Expected changes: 3 relationships created.
