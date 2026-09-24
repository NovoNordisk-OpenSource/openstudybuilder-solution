# Data Corrections: Applied to PRD after release 1.12.0

## 1. Remove Duplicate Activity Instance Classes
### Problem description
There are duplicate root-value pairs of Activity Instance Classes for the following:
`TextualFindings`, `NumericFindings`, `GeneralObservation` and `CategoricFindings`.


### Change description
- Move the `ACTIVITY_INSTANCE_CLASS` relationship between redundant Activity Instance Class nodes to
the corresponding usable Activity Instance Class nodes.
- Remove the redundant Activity Instance Class root-value pairs.

### Nodes and relationships affected
- `ActivityInstanceClassValue` nodes
- `ACTIVITY_INSTANCE_CLASS` relationships