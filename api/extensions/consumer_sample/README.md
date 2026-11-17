# Consumer sample extension (`consumer_sample`)

A small, working example of a read-only extension that serves library content to external
systems. It covers Controlled Terminology (CT) terms:

| Content | Endpoint (Extensions API) |
|---|---|
| CT terms of a codelist | `GET /consumer-sample/ct-terms?codelist_submission_value=<value>` |

The extension reads Neo4j itself. It does not call another API.

## Files

| File | What it shows |
|---|---|
| `consumer_sample_main.py` | The endpoint (`router`), protected by role `Library.Read` |
| `db.py` | The Cypher queries (one page of rows, one count), with the submission value and the page passed as parameters |
| `models.py` | `CTTerm` response model and the sort enums (the page itself is `PaginatedResponse` from `extensions/common.py`) |
| `tests/test_unit.py` | The endpoint without a database (database function replaced) |
| `tests/test_extension.py` | The endpoint against the Neo4j test database |

## Authentication

The extension uses the authentication of the Extensions API, like every extension.

- `OAUTH_ENABLED=true`: every request needs a valid access token in the
  `Authorization: Bearer <token>` header, issued for this API (`OAUTH_API_APP_ID`).
  Without a valid token the API answers `401`.
- The endpoint needs the role **`Library.Read`** (`rbac.LIBRARY_READ`). Without it the API answers
  `403`. The role is checked only when `OAUTH_RBAC_ENABLED` is on.
- `OAUTH_ENABLED=false` is for local work only: every request is accepted as a dummy user that has
  all roles. Never expose the API like this.

Each authenticated request also records the calling user in Neo4j, so the Extensions API needs a
working database connection even for read-only endpoints.

## Response

One page of CT terms, with the total number of terms in the codelist:

```json
{
  "self": "/consumer-sample/ct-terms?codelist_submission_value=TIMELB&page_size=100&page_number=1",
  "prev": "/consumer-sample/ct-terms?codelist_submission_value=TIMELB&sort_by=term_uid&sort_order=asc&page_size=100&page_number=1",
  "next": "/consumer-sample/ct-terms?codelist_submission_value=TIMELB&page_size=100&page_number=2",
  "items": [ ... ]
}
```

- `sort_by` (`term_uid` by default, `submission_value`, `sponsor_preferred_name`,
  `nci_preferred_name` or `concept_id`) and `sort_order` (`asc` by default, or `desc`) order the
  terms before they are paged. Ties are broken by term uid, so pages never overlap.
- `page_size` (1 to the maximum page size) and `page_number` (from 1) select the page. Follow
  `next` until `items` is empty to read everything.
- `total` is the number of Final terms of the codelist, the same on every page.
- Each item has `codelist_uid`, `term_uid`, `order`, `ordinal`, `submission_value`,
  `sponsor_preferred_name`, `concept_id`, `nci_preferred_name`, `library_name`, `name_status`,
  `name_version`, `attributes_status` and `attributes_version`.
- Only terms whose name and attributes are currently Final are returned. A term that is being
  revised (a new Draft version) or is retired is not returned until it is approved again, and the
  status of the codelist itself is not checked. An unknown submission value gives an empty page.
- Invalid parameters (missing submission value, unknown `sort_by`/`sort_order`, page outside the limits) give `400`.

## Running the sample locally

From `api/`, with Neo4j running and `.env` set (`NEO4J_DSN`, `OAUTH_ENABLED=false` for local work).
The Extensions API reads `NEO4J_DSN` from the environment, so start it through poe, which exports
`.env`:

```bash
uv run poe extensions-api-dev    # Extensions API on http://localhost:8009

curl "http://localhost:8009/consumer-sample/ct-terms?codelist_submission_value=TIMELB"
```

Tests:

```bash
uv run poe extensions-test                                   # all extension tests
uv run poe test -- extensions/consumer_sample/tests/         # this extension only
```
