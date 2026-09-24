# Components and UI

## Component Structure

```
src/
├── api/             # Axios repository + one module per resource (see architecture-core.md)
├── components/      # Shared/reusable components
│   ├── library/     # Library-specific components
│   ├── studies/     # Study-specific components
│   ├── tools/       # Cross-cutting widgets: dialogs, charts, form fields,
│   │                #   table helpers, comment threads. FLAT — no subdirs.
│   ├── layout/      # AppBar, Drawer, PassThrough
│   ├── ui/          # Low-level field wrappers + notification/
│   └── preferences/ # PreferenceField.vue
├── views/           # Page-level components (routed)
│   ├── library/
│   ├── studies/
│   ├── administration/
│   ├── user/        # UserPreferences.vue
│   └── *.vue        # HomePage, LoginPage, LogoutPage, AuthCallback
├── stores/          # Pinia stores
├── composables/     # Vue 3 composition API reusable logic (see below)
├── plugins/         # Vue plugins (auth, i18n, vuetify, formRules, notificationHub, eventBus)
├── locales/         # i18n — a directory per language (see below)
├── styles/          # SCSS, incl. settings.scss consumed by the vuetify() plugin
├── utils/           # Utility functions
├── constants/       # Static constants and enums
├── assets/          # Static assets
├── demo/            # Demo mode: mock backend, auth stub, fixtures (see architecture-core.md)
└── extensions/      # Extensibility system (custom modules)
```

`library/` and `studies/` are by far the largest subtrees; the rest are small.

**Search `components/tools/` before building a new shared widget.** It is a large flat directory —
`ConfirmDialog`, `ActionsMenu`, `DataTableExportButton`, `DurationField`, chart wrappers, comment
threads — and the most common source of accidental duplication, because it is not named for
anything and does not appear in most mental models of the tree.

## Composables

Everything in `src/composables/`. All are plain `useX()` factories returning an object — none are
singletons, so each call site gets its own state. Check this list before writing a new one.

| Composable | Returns | Notes |
|-----------|---------|-------|
| `useAccessGuard()` | `{ userInfo, checkPermission }` | `checkPermission(role)` returns **`true` unconditionally** unless both `OAUTH_ENABLED` and `OAUTH_RBAC_ENABLED` are set — so permission checks are inert in a default local setup. Fails closed on a null `userInfo`. |
| `useErrorHandler(error)` | — (side effect) | Takes an Axios error, resolves a message from `api.errors.*` / `api.fields.*`, and raises a sticky error toast. **Already called by the repository interceptor** — see the double-toast warning in `patterns.md`. |
| `useInfiniteScroll(fetchFn, opts)` | `{ items, loading, currentPage, hasMore, searchQuery, loadMore, reset, search }` | `fetchFn(page, searchQuery)`; `opts.pageSize` default 50, `opts.initialPage` default 1. |
| `useTabKeys()` | `{ tabKeys, updateTabKey }` | Increments a per-tab counter used as a `:key` to force remount of a tab's contents. |
| `useShake(duration = 1000)` | `{ isShaking, activateShake }` | Sets a flag for ~1s to drive a shake animation. `activateShake(false)` is a no-op. |
| `useNumericValues()` | `{ createNumericValue, createNumericValues }` | POSTs numeric-value-with-unit concepts; returns uids. Skips items missing `value` or `unit_definition_uid`. |
| `useActivities()` | `{ displayActivityGroups, displayActivitySubgroups }` | Builds bullet-joined **HTML strings** from `activity_groupings`, escaped via `@/utils/sanitize`. Intended for `v-html`; keep the escaping if you touch it. |
| `usePharmaceuticalProducts()` | `{ getIngredientName, displayIngredients, displayDosageForms, displayRoutesOfAdministration }` | Display-formatting helpers for pharmaceutical product records. |

## Extensions System
- Located in `src/extensions/`
- Each extension is a self-contained module with optional:
  - `router/index.js` - Adds routes via `addExtensionRoutes(routes)` function
  - Components, views, stores specific to the extension
- Extensions are auto-discovered and loaded at build time

## Internationalization (i18n)
- Plugin: `src/plugins/i18n.js`
- Locale files: `src/locales/<lang>/` — a **directory** per language, not a single file. Currently only `en/`:
  - `src/locales/en/app.json` — UI strings. New translation keys go here.
  - `src/locales/en/api.json` — generated API field labels (see below); do not hand-edit.
  - `src/locales/en/index.js` — merges and exports the above.
  - There is no `src/locales/en.json`.
- Use `$t()` function in templates and `t()` in script
- API field translations can be generated with `node scripts/getApiFields.js`
- Frontend extensions ship their own `locales/en/` rather than adding keys to the core `app.json`

## Styling
- Vuetify 4 Material Design components
- SCSS configuration: `src/styles/settings.scss` (wired via the `vuetify()` plugin in `vite.config.mjs`)
- Custom styles: `src/styles/`
- Themes live one-file-per-palette in `src/plugins/themes/*.js` (each default-exports
  `{ title, dark, colors }`); `src/plugins/vuetify.js` derives `APP_THEMES`/`THEME_NAMES` from them
  via `import.meta.glob`. Adding a theme is just adding a file — no other file needs editing. Use
  named theme colors (`primary`, `nnBaseBlue`, `nnSeaBlue200`, …) rather than hex literals.

### Global component defaults — read before adding form fields
`src/plugins/vuetify.js` also sets a `defaults` block, and the codebase relies on it completely —
**no `v-text-field` call site in the app passes `variant`.**

- `VTextField`, `VTextarea`, `VSelect`, `VAutocomplete`, `VCombobox`, `VFileInput`, `VNumberInput`
  → `variant: 'outlined'`, `density: 'compact'`, `rounded: 'lg'`
- `VBtn` → `class: 'text-uppercase'`
- `VCheckbox`, `VCheckboxBtn`, `VRadio`, `VRadioGroup`, `VSwitch` → `density: 'compact'`,
  `color: 'primary'`

Do not restate these props on individual components — it is redundant and inconsistent with every
existing call site. Only pass them to deliberately *override* a default. If a button renders
uppercase or a field comes out outlined and you did not ask for it, this block is why.
