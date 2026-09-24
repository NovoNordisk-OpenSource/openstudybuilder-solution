# Development Commands

## Start Development Server
```bash
npm run dev
```
Starts the Vite dev server with hot-reload at http://localhost:5173 (default).

## Build for Production
```bash
npm run build              # Standard build
npm run build:dev          # Build with dev mode
npm run build:staging      # Build with staging mode
```

## Testing
```bash
npm run test:smoke         # Playwright end-to-end smoke tests
npm run test:smoke:headed  # ...with a visible browser
npm run test:smoke:ui      # ...in Playwright's interactive UI mode
npm run test:fixtures      # node --test over tests/fixtures/*.test.mjs
```
- Tests live in `tests/`: `tests/smoke/` (Playwright specs + helpers) and `tests/fixtures/`
- Playwright config: `tests/smoke/playwright.config.js`
- Run a single smoke test: `npx playwright test --config tests/smoke/playwright.config.js -g "test name"`
- `test:smoke` runs `build:demo` first, so it is slow — it builds the demo bundle before the browser starts

**There is no unit test runner.** Jest is not installed and there is no `test:unit` script; `frontend/jest.config.js` is an unremoved leftover from a previous setup (it references an uninstalled `@vue/cli-plugin-unit-jest` preset and a `tests/unit/` directory that does not exist). Do not write Jest tests and do not add `npm run test:unit` back to this file. Component-level coverage currently happens through the smoke suite.

## Code Quality
```bash
npm run lint               # Run ESLint with auto-fix
npm run lint:staged        # Lint only staged files (used by pre-commit hooks)
npm run format             # Run Prettier on all files
npm run format:staged      # Format only staged files
```

## Other Utilities
```bash
node scripts/getApiFields.js    # Extract API field translations from OpenAPI spec
npm run build-sbom              # Generate software bill of materials
```
