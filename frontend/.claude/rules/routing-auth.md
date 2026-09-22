# Routing and Authentication

## Routing
- Router: `src/router/index.js`
- **Three** main sections: `/library`, `/studies`, and `/administration`. Plus the unsectioned
  top-level routes `/`, `/login`, `/logout`, and `/oauth-callback`.

### Route metadata

These are the keys actually in use, roughly most to least common:

| Key | Meaning |
|-----|---------|
| `authRequired` | Requires authentication |
| `studyRequired` | Requires a selected study (persisted in localStorage) |
| `featureFlag` | Gates the route behind a feature flag |
| `resetBreadcrumbs` | Resets breadcrumb navigation on entry |
| `requiredPermission` | Requires a specific role (see `src/constants/roles.js`) |
| `documentation` | `{ page, anchor? }` — builds `appStore.helpPath` for the in-app help link |
| `section` | `'Library'` / `'Studies'` / `'Administration'` |
| `layoutTemplate` | `'empty'` or `'error'`; defaults to `'2cols'` |

Two behaviours that are easy to get wrong:

- **`section` is only read when `resetBreadcrumbs` is true.** The guard sets it inside the
  `resetBreadcrumbs` branch, falling back to `to.name` when `section` is absent. Setting `section`
  without `resetBreadcrumbs` does nothing.
- **`layoutTemplate` is consumed in `App.vue`, not the router** — `route.meta.layoutTemplate ||
  '2cols'`. Only `'empty'` and `'error'` have branches; any other value silently falls through to
  the standard two-column chrome.

`documentation` is inherited: the guard uses `to.matched.some(...)`, so a parent route's value
applies to children that do not set their own.

- **Dynamic extension routes**: Extensions in `src/extensions/*/router/index.js` are auto-loaded
  via `import.meta.glob(..., { eager: true })`. The `eager` flag there is a glob option, **not**
  route metadata — do not copy it into a `meta` block.

## Authentication Flow
- OAuth/OIDC via `oidc-client-ts` library
- Auth plugin: `src/plugins/auth.js`
- Token stored in browser and validated on navigation
- Router guards check `authRequired` and `requiredPermission` metadata
- Login redirect stores intended route in sessionStorage
- Access token is automatically included in API requests via Axios interceptor
