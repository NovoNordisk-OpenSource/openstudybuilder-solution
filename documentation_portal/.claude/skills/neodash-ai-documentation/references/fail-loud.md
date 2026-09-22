# Fail loud — never substitute, never approximate

A documentation agent has a higher accuracy bar than a testing agent: a test
that clicks the wrong control fails visibly; a guide that documents the wrong
control ships and gets read. "Substituting the closest analogue" is the natural
failure mode of a helpful agent. These rules exist to override that instinct.
Do not soften them.

## The pattern (before every click)

1. **Literal-label check.** Confirm the exact tab/label from the source guide is
   present in the current `browser_snapshot`. If it is absent, **STOP**. Do not
   click a "near match", "closest analogue", or "functionally equivalent" control.
2. **Name the gate.** A missing control usually means a prerequisite isn't met.
   For NeoDash that is almost always **data / connection**: the dashboard is
   connected to the wrong Neo4j database, the report isn't loaded into this
   NeoDash instance, or the underlying data is empty. Say which in the failure
   message.
3. **Duplicate-screenshot tripwire.** If two consecutive screenshots are
   byte-identical, the previous click was a no-op. Stop and report — don't
   continue, the rendered guide would mislead.

## NeoDash-specific stop conditions

- **Report not in the navigation panel** → the report (dashboard) isn't loaded
  in this NeoDash instance, or you're connected to the wrong database. Stop.
- **Expected tab not on the page tab bar** → do not document a different tab.
  Stop and report which tab is missing.
- **A card shows "Query returned no data"** → the query found nothing (wrong
  database, empty data, or a selection/filter not yet made). Capture it, flag it
  as low-confidence, and do NOT invent a result in the prose.
- **Editor-only controls visible** (rename pencil, card drag handle, add-page
  `+`) → you are NOT in reader mode. End-user guides must be captured in reader
  mode; switch before capturing.

## Failure message shape

> Expected tab/label "<name>" not found in <report> on <url> at step <n>.
> Most likely cause: <gate — e.g. report not loaded in this NeoDash instance, or
> connected to the wrong Neo4j database>. Stopping. Partial screenshots saved to
> ./neodash-docs/<report>/assets/.

On any failure, also write `./neodash-docs/<report>-FAILED.md` capturing what was
tried and where it stopped, so the next run has context.

## Why non-negotiable

Substitution looks helpful in the moment and produces confidently wrong
documentation. Halting early — before a redundant or wrong click — is the rule
working preventively, which is the desired behaviour.
