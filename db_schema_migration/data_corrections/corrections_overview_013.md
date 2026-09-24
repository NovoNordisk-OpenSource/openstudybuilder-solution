# Data Corrections: Applied to PRD after release 1.16.0

## 1. Properly store author information for some nodes/relations
### Problem description
- Some nodes and relationships in the database have an `author_id` field value that does not correspond to any existing `User` node.
- Some of them are storing author information in the `user_initials` field instead of `author_id`.
- Some nodes and relationships have the `author_id` set to 'unknown-user' or 'sb-import', which should be replaced with a specific SB app registration ID.

The `author_id` field is expected to be set for all relevant nodes and relationships, and it should match the `user_id` value of an existing `User` node.

### Change description
- Move `user_initials` values to `author_id` field for all relevant nodes and relationships.
- Convert 'unknown-user' and 'sb-import' values for `author_id` field to a specific SB app registration ID.
- Create `User` nodes for all existing `author_id` values that do not have a corresponding `User` node.
- Ensure that all relevant nodes and relationships have the `author_id` field set, and that it matches an existing `User` node's `user_id`.

### Nodes and relationships affected
- `CTPackage|StudyAction|Edit|Create|Delete` nodes
- `HAS_VERSION|HAS_TERM|HAD_TERM|LATEST_LOCKED|LATEST_RELEASED` relationships