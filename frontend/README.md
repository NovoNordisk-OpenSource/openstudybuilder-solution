# OpenStudyBuilder Frontend

Node.js 20 and npm are prerequisites — see the
[root README](../README.md#prerequisites).

On Windows, use WSL/WSL2 or make sure your shell can run the npm scripts.

## Enable authentication

Edit the ``config.json`` file and update or define the following variables:
```
"OAUTH_ENABLED": "true",
"OAUTH_RBAC_ENABLED": "true",
"OAUTH_METADATA_URL": "<URL to the OpenID Connect Metadata document>",
"OAUTH_API_APP_ID": "<Application ID of the clinical-mdr-api>",
"OAUTH_UI_APP_ID": "<Application ID of OpenStudyBuilder UI>",
```

## Project setup
```
npm ci
```

### Compiles and hot-reloads for development
```
npm run dev
```

### Compiles and minifies for production
```
npm run build
```

### Run your integration tests
See [README.md of the system_tests directory.](../system_tests/README.md)

### Run smoke tests against the demo build
A small Playwright suite drives the demo build (in-browser mock backend) and asserts that key routes render without uncaught exceptions or unexpected console errors. The suite also runs in CI as the `smoke` job in `.github/workflows/frontend-build.yml`.

First-time setup (one-off):
```
npx playwright install chromium
```

Run the suite:
```
npm run test:smoke          # rebuilds the demo bundle, runs headless
npm run test:smoke:headed   # same, but with a visible browser
npm run test:smoke:ui       # Playwright UI for picking individual tests, no rebuild
```

Tests live in `tests/smoke/`. They cover home, studies and library summary pages, activities, CRF viewer, study-scoped routes, breadcrumb trails, validators, and a few navigation paths. Known-noise warnings from the mock backend (`[demo] no spec entry for …`, schema-walker depth limit, the `GroupOverview` `/details` fallback) are filtered — see `tests/smoke/helpers/consoleSpy.js` for the exact ignore list.

### Lints and fixes files
```
npm run lint
```

### Generate API field translation strings
To extract field paths and human-readable labels from an OpenAPI specification for use in translation files:
```
node scripts/updateApiFields.js
```

This script will:
1. Prompt you for the path to an OpenAPI JSON file. In this repository the API
   spec is at `../api/openapi.json`.
2. Parse the OpenAPI specification and extract field definitions
3. Generate human-readable translation strings for API field names
4. Output the results to `output.txt`

The generated strings can be used to create frontend translations for API field names.

### Customize configuration
See [Configuration Reference](https://cli.vuejs.org/config/).

## Demo mode (no backend required)

Demo mode runs the OpenStudyBuilder web application against an in-browser mock backend so it boots without a live [API](../api/README.md) or an authentication provider. Useful for screenshots, design exploration, and offline demos.

### Run it
```
npm run dev:demo      # dev server with hot-reload
npm run build:demo    # production build
```

### How it works
- Auth and `/config.json` are bypassed in `src/main.js` when `VITE_ENABLE_DEMO_BACKEND=true`.
- `src/api/repository.js` swaps the axios adapter for `src/demo/mockBackend.js`, which intercepts every API call.
- For each request, the mock backend looks up the URL in the OpenAPI spec, walks the success-response schema, and returns a synthetic body (enums → first value, types → shaped placeholders, paginated wrappers → `{items, total, page, size}`).
- Hand-tuned fixtures in `src/demo/fixtures/*.js` take precedence over generated responses, so a small slice (a few studies, activities, one CRF, a flowchart) feels coherent.
- Mutations (`POST` / `PATCH` / `DELETE`) update an in-memory state object backed by `localStorage` (`studybuilder.demo.state.v1`), so changes survive reloads. Clear that key to reset.

### OpenAPI spec source
The mock backend needs the API's `openapi.json` at build/dev time. By default it reads the in-repo spec at `../api/openapi.json` (the sibling `api/` project in this monorepo), so demo mode and CI stay in sync with the API automatically. To point at a different spec — e.g. a freshly regenerated one — set `VITE_OPENAPI_SPEC` in `.env.demo` or your shell:

```
VITE_OPENAPI_SPEC=../api/openapi.json npm run dev:demo
VITE_OPENAPI_SPEC=/absolute/path/to/openapi.json npm run dev:demo
```

The spec is compacted at build time (success responses + their referenced schemas only) so production demo bundles stay reasonable (~35 KB gzipped).

### Adding hand-tuned fixtures
When a generated response isn't realistic enough, add an entry to `src/demo/fixtures/studies.js` or `src/demo/fixtures/library.js`. Each handler is `{method, regex, respond}`; `respond` receives a context with `state`, `clone`, and request details.

### Resetting demo state
Mutations are persisted in `localStorage` under the key `studybuilder.demo.state.v1`. To start fresh, clear that key from your browser's devtools (Application → Local Storage), or run `localStorage.removeItem('studybuilder.demo.state.v1')` in the console. A full reload after that gives you a clean slate.

### Sign-in and access groups
Demo mode runs with `OAUTH_ENABLED=1` so the existing route guards and permission checks are exercised. On first load you'll see a Login button; the picker lets you choose a display name and any combination of access groups (Library/Study/Admin × Read/Write). Identity is stored in `localStorage` under `studybuilder.demo.auth.v1` and survives reloads. Logout clears it.

The mock backend enforces those access groups: `GET` calls require `<domain>.Read`, mutations require `<domain>.Write`. Domains are derived from the path (`/studies` and `/study-*` → Study; `/admin`, `/configurations`, `/user-preferences`, `/notifications`, `/data-completeness-tags` → Admin; everything else → Library). System routes and feature-flags are open so the app can boot before sign-in.

To skip the picker (E2E tests, fixed-identity development), set `VITE_DEMO_AUTH_ROLES` in `.env.demo` or your shell — comma-separated, or `*` for every role. Optionally set `VITE_DEMO_AUTH_NAME`. When set, the demo session is reapplied on every page load.

```
VITE_DEMO_AUTH_ROLES=Library.Read,Library.Write,Study.Read,Study.Write,Admin.Read npm run dev:demo
```

### Limitations
- Extensions API (`src/extensions/`) and consumer APIs are not mocked.
- Endpoints not in the spec return 404 with a console warning — that's the signal to add a hand-tuned handler.
- For paginated endpoints, `page_size=0` (the API's "give me everything" sentinel) is capped at 25 synthetic items. Lists requesting all rows will appear truncated.
- Mutations only persist round-trip if the relevant fixture handler explicitly merges from `state` on read. Generated (schema-walked) GET responses don't see prior PATCH/POST writes — when that matters, add a hand-tuned handler that reads from `state`.
- The OpenAPI spec must match the API version the UI expects. A stale spec will cause "no spec entry" 404s for newly added endpoints, or schema mismatches for changed ones.


## Environments
Environment files contained in main directory are used to build proper environments in NN cloud please do not modify them:

```
.env.staging, .env.dev
```

unless you know what you are doing.

