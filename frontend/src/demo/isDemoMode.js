/**
 * Single source of truth for the demo-mode toggle.
 *
 * Demo mode swaps the axios adapter for an in-browser mock backend
 * (src/demo/mockBackend.js), bypasses /config.json (src/main.js), and uses
 * a localStorage-backed auth stub (src/demo/demoAuth.js) instead of OIDC.
 * Whether the app is in demo mode is decided once, at build time, by the
 * VITE_ENABLE_DEMO_BACKEND env var — Vite inlines import.meta.env reads at
 * build time, so this constant compiles to a literal in each call site.
 */
export const DEMO_MODE = import.meta.env.VITE_ENABLE_DEMO_BACKEND === 'true'
