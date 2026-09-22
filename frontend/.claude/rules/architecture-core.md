# Core Architecture

## Application Bootstrap
- **Entry point**: `src/main.js`
- Loads runtime configuration from `/config.json` (not bundled, environment-specific)
- Initializes plugins: auth, i18n, vuetify, Pinia, router, event bus, etc.
- Configuration values are injected via `$config` and used throughout the app

## Configuration System
- Runtime config: `public/config.json` - **DO NOT modify environment files** (`.env.dev`, `.env.staging`) unless you understand the build pipeline
- Config includes API URLs, OAuth settings, feature flags, and Application Insights
- Boolean config values are parsed from strings (e.g., '1', 'true', 'yes' → true)

## Demo Mode
A second, self-contained way the app can run, living in `src/demo/`. Decided **once at build
time** by `VITE_ENABLE_DEMO_BACKEND` (set in `.env.demo`, used by `npm run dev:demo`,
`build:demo`, `preview:demo`, and `test:smoke`). It swaps out three things:

| Normal | Demo |
|--------|------|
| `fetch('/config.json')` | inline `DEMO_CONFIG` object in `src/main.js` |
| Axios talks to a real API | in-browser mock adapter, `src/demo/mockBackend.js` |
| OIDC via `src/plugins/auth.js` | localStorage auth stub, `src/demo/demoAuth.js` |

- `src/demo/isDemoMode.js` exports the `DEMO_MODE` constant and is the normal way to read the
  flag — `plugins/auth.js`, `router/index.js`, and `demoAuth.js` all import it. **Two files must
  not**; see the constant-folding gotcha in `conventions-gotchas.md`.
- `mockBackend.js` synthesizes responses from the API's OpenAPI spec rather than fixtures. The
  spec is injected as the `@openapi-spec` virtual module by a plugin in `vite.config.mjs`. The
  plugin is registered in *every* build — outside demo mode it resolves to an empty stub, which is
  what keeps Vite's dependency scan clean. Hand-tuned overrides live in `src/demo/fixtures/*.js`.
- The spec defaults to `../api/openapi.json` — the in-repo one. This is a real cross-component
  dependency: an `api/openapi.json` change alters the demo build and the smoke tests, which is why
  CI re-runs the frontend job when that file changes.

## State Management (Pinia)
- All stores are in `src/stores/`
- Key stores:
  - `app.js` - Application state (breadcrumbs, menu, section navigation)
  - `auth.js` - Authentication and user info
  - `studies-general.js` - Selected study context
  - `feature-flags.js` - Feature flag management
- Store composition pattern: stores import and use other stores as needed

## API Layer
- Base repository: `src/api/repository.js` (Axios instance with interceptors)
- API modules in `src/api/` follow resource-based pattern (e.g., `study.js`, `activities.js`)
- Each module exports methods that call the repository with specific endpoints
- API responses use standard REST conventions (GET, POST, PATCH, DELETE)
