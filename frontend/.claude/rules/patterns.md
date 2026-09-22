# Important Patterns

## Study Selection
- Many routes require a selected study (`studyRequired: true` in route meta)
- Selected study is stored in localStorage and loaded into `studies-general` store
- Study UID is in route params as `:study_id`
- If study is not selected, user is redirected to study selection page

## Feature Flags
- Feature flags control visibility of routes and features
- Fetched from API at router navigation
- Route-level: `meta: { featureFlag: 'flag_name' }`
- Component-level: Check `featureFlagsStore.getFeatureFlag('flag_name')`

## Breadcrumb Navigation
- Managed by `app` store
- Routes with `resetBreadcrumbs: true` clear existing breadcrumbs
- Breadcrumbs auto-generated from menu structure based on current route
- Section is set based on route's top-level path (/library, /studies, /administration)

## API Request Patterns
When making API calls:
1. Import the relevant API module (e.g., `import study from '@/api/study'`)
2. Use async/await or promises
3. Handle errors with try/catch or `.catch()`
4. Common pattern: show loading state, call API, update store/component state, handle errors

## Event Bus
- Plugin: `src/plugins/eventBus.js`
- **There is no `eventBusOn`.** The bus is a `ref(new Map())`; emitting just writes the args into
  the map under the event name. Subscribers *watch* that entry — there is no listener registry:
  ```javascript
  import { eventBus, eventBusEmit } from '@/plugins/eventBus'

  eventBusEmit('userSignedIn')                        // producer
  watch(() => eventBus.value.get('userSignedIn'), () => { ... })   // consumer
  ```
  Provided for injection as `eventBus` (the ref) and `eventBusEmit`, and also exported by name.
- Consequence of the Map design: the last emitted value is retained forever and never cleared, so
  a watcher added with `{ immediate: true }` fires immediately on a *stale* past event. Watch
  without `immediate` (as `App.vue` does). There is also no unsubscribe — the entry outlives every
  subscriber. Repeated emits do each re-fire, since `emit(event, ...args)` stores a fresh array
  reference every call.
- The bus is almost unused: `userSignedIn` is the only event, emitted from `src/plugins/auth.js`
  and `src/demo/DemoLoginPage.vue`, with a single watcher in `src/App.vue`. Prefer a store or
  props for new cross-component communication.
- **Notifications do not go through the event bus** — see below.

## Notifications and API Errors
- Plugin: `src/plugins/notificationHub.js` — this is how user-facing toasts are raised.
- Obtain it with `const notificationHub = inject('notificationHub')` in components (the common
  case), or `import { notificationHub } from '@/plugins/notificationHub'` in plain modules.
- API: `add()`, `remove()`, `clear()`, `clearErrors()`, and the `queue` ref.
  ```javascript
  notificationHub.add({ msg: t('some.key'), type: 'success' })
  ```
  - `type` defaults to `'success'`; also `'warning'`, `'error'`, `'info'`.
  - `timeout` defaults to an estimated reading time (minimum 7s). Pass `timeout: 0` to make it
    sticky until dismissed.
  - `persist: true` survives a `document.location.reload()` via sessionStorage — for callers that
    reload right after firing a toast.
- **Failed API calls already notify.** The Axios response interceptor in `src/api/repository.js`
  routes errors through the `useErrorHandler` composable, which resolves the message from
  `api.errors.*` / `api.fields.*` i18n keys and raises a sticky error toast itself. Do not add
  your own error toast in a `catch` for an API call — you will get two.
- Call `notificationHub.clearErrors()` before retrying an action to dismiss the previous failure.

## Form Validation
- Form rules plugin: `src/plugins/formRules.js`, injected as `formRules`
- Provides 11 rules: `required`, `requiredIfNotNA`, `atleastone`, `oneselected`, `max`,
  `max_value`, `min_value`, `numeric`, `sameAs`, `uppercaseAlphanumeric`, `oneOfTwo`.
  **There is no `email` rule**, and the length rule is `max`, not `maxLength`.
- Each rule is a plain Vuetify validator taking the field *value*, not a factory taking a label.
  Pass single-argument rules bare — `:rules="[formRules.required]"` — and wrap the rest in an
  arrow: `:rules="[(value) => formRules.max(value, 200)]"`.
- `:rules` goes on the input, not on `<v-form>`. Error messages come from the rule's own
  `_errors.*` i18n key, so do not pass a message.
- Full signatures are documented in `.claude/agents/vue-ui-developer.md`.
