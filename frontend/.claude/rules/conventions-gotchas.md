# Conventions and Common Gotchas

## File Naming Conventions

- Vue components: PascalCase (e.g., `StudyTitle.vue`, `ActivityOverview.vue`)
- JavaScript files: camelCase (e.g., `study.js`, `formRules.js`)
- Stores: kebab-case or descriptive names (e.g., `app.js`, `studies-general.js`)
- Constants: camelCase files, UPPER_CASE exports when appropriate

## Common Gotchas

1. **Routes with dots**: Version numbers in routes (e.g., `/overview/4.1`) need special handling in Vite config (see `spa-fallback-for-dots` plugin)

2. **Config.json vs .env files**:
   - `public/config.json` is for runtime configuration
   - `.env.*` files are only used during build time
   - Don't confuse the two - config.json is loaded at app startup

3. **Study context**: Many operations require a study to be selected. Always check `studiesGeneralStore.selectedStudy` before study-specific operations.

4. **Feature flags**: New features should be gated by feature flags. Check existing patterns in router and components.

5. **Authentication state**: OAuth tokens can expire. API layer handles 401s and triggers re-authentication.

6. **Async initialization**: The app waits for config.json to load before mounting. Don't try to access `$config` in module-level code.

7. **Path aliases**: Use `@/` to import from `src/` directory (configured in `vite.config.mjs`)

8. **Demo-mode checks in `main.js` and `api/repository.js` must stay inline**: Both files guard a
   dynamic `import()` of demo-only code, and both declare the flag as a local literal:

   ```javascript
   const DEMO_MODE = import.meta.env.VITE_ENABLE_DEMO_BACKEND === 'true'
   ```

   This looks like duplication of `@/demo/isDemoMode` and it is tempting to "clean up" — do not.
   Vite/Rolldown only constant-folds the check, and therefore only tree-shakes the demo branch,
   when the boolean is a literal in that module's own scope. Importing the constant defeats the
   cross-module propagation and the demo branch — `import('@openapi-spec')` in `main.js`,
   `import('@/demo/mockBackend')` in `repository.js` — survives into the normal `npm run build`.

   **The build does not fail — it silently bloats.** Measured against a 5,032,837-byte / 217-chunk
   baseline by swapping in the import and running `npm run build`:

   | Swapped | Exit | JS bytes | Chunks | Effect |
   |---------|------|----------|--------|--------|
   | `main.js` | 0 | +30 | +1 | dead dynamic import of a 30-byte stub |
   | `repository.js` | 0 | **+24,365** | +1 | **`mockBackend-*.js` shipped to production** |

   `repository.js` is the one that matters. Nothing in the build output flags it; the only signal
   is a `mockBackend-*.js` chunk appearing in `dist/`.

   The OpenAPI spec itself is *not* embedded, because `vite.config.mjs`'s `load()` returns
   `export default {}` when the spec path is null. That stub exists for Vite's dependency scanner
   (which crawls `mockBackend.js`'s static import even in non-demo builds) — it is not a safety net
   that makes the inline check optional, and it does nothing about the demo *code* being bundled.

   Everywhere else, importing `DEMO_MODE` from `@/demo/isDemoMode` is correct and preferred —
   `plugins/auth.js`, `router/index.js`, and `demo/demoAuth.js` all do it. The rule is narrow: it
   applies only to the two modules that gate a dynamic import.
