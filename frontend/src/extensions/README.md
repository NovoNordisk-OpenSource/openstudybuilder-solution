# StudyBuilder Frontend Extensions

This folder contains frontend extensions for the StudyBuilder application. Extensions are modular Vue.js components that add new functionality to the application without modifying the core codebase.

## Architecture Overview

The extensions system provides:
- **Dynamic Loading**: Extensions are automatically discovered and loaded at runtime
- **Route Integration**: Extensions can add new routes to existing sections
- **Menu Integration**: Extensions can add menu items to the sidebar
- **Localization**: Extensions can provide their own translations
- **API Integration**: Extensions can define API client methods
- **Isolated Components**: Each extension has its own views, stores, and routing

## Directory Structure

```
extensions/
├── README.md                          # This file
│
└── hello/                             # Example "hello" extension
    ├── api/
    │   └── extensions.js              # API client methods
    ├── locales/
    │   └── en/
    │       ├── index.js               # Locale exports
    │       └── app.json               # Translation keys
    ├── router/
    │   └── index.js                   # Route definitions
    ├── stores/
    │   └── app.js                     # Menu items and app state
    └── views/
        └── HelloExtensionView.vue     # Vue components
```

## How Extensions Are Loaded

Extensions are automatically discovered and loaded by the core application:

1. **Routes**: `src/router/index.js` uses `import.meta.glob` to dynamically import all `extensions/*/router/index.js` files
2. **Translations**: `src/plugins/i18n.js` loads and merges translations from `extensions/*/locales/en/index.js`
3. **Menu Items**: `src/stores/app.js` loads and merges menu items from `extensions/*/stores/app.js`

## Creating a New Extension

Follow these steps to create a new extension:

### 1. Create Extension Directory

Create a new folder in `src/extensions/` with your extension name (lowercase, hyphens for multi-word names):

```bash
mkdir src/extensions/my-extension
```

### 2. Create Required Structure

Create the necessary subdirectories:

```bash
mkdir -p src/extensions/my-extension/{api,locales/en,router,stores,views}
```

### 3. Define Routes (Required)

Create `router/index.js` to define your extension's routes:

```javascript
import roles from '@/constants/roles'

const myExtensionRoute = {
  path: 'my-extension/:tab?',
  name: 'MyExtension',
  component: () => import('../views/MyExtensionView.vue'),
  meta: {
    resetBreadcrumbs: true,
    authRequired: true,
    section: 'Administration', // or 'Library', 'Studies'
    requiredPermission: roles.ADMIN_READ,
    // featureFlag: 'my_extension', // Optional: feature flag
  },
}

export function addExtensionRoutes(routes) {
  // Find the parent route (e.g., Administration)
  const administrationRoute = routes.find(
    (route) => route.path === '/administration'
  )
  
  // Add your route as a child
  if (administrationRoute?.children) {
    administrationRoute.children.push(myExtensionRoute)
  }
}
```

**Key Points:**
- Must export a function named `addExtensionRoutes`
- Add routes to existing sections like `/administration`, `/library`, or `/studies`
- Use lazy loading with `import()` for components
- Set appropriate `meta` properties for authentication and permissions

### 4. Add Menu Items (Required)

Create `stores/app.js` to add menu items:

```javascript
import { i18n } from '@/plugins/i18n'

export default {
  menuItems: {
    Administration: {  // Match the section where you added the route
      items: [
        {
          title: i18n.t('MyExtension.menu_label'),
          url: { name: 'MyExtension' },
          icon: 'mdi-puzzle-outline', // Material Design Icon
          // featureFlag: 'my_extension', // Optional: show only when feature flag is enabled
        },
      ],
    },
  },
}
```

**Menu Sections:**
- `Library` - Library section menu
- `Studies` - Studies section menu
- `Administration` - Administration section menu

### 5. Add Translations (Recommended)

Create `locales/en/app.json` with your translation keys:

```json
{
  "MyExtension": {
    "menu_label": "My Extension",
    "title": "My Extension Title",
    "description": "Description of what this extension does",
    "save": "Save",
    "cancel": "Cancel",
    "success_message": "Operation completed successfully",
    "error_message": "An error occurred"
  }
}
```

Create `locales/en/index.js` to export translations:

```javascript
import app from './app.json'

export default {
  ...app,
}
```

**Translation Best Practices:**
- Group translations under a namespace matching your extension name
- Use descriptive keys (e.g., `save_button` instead of `btn1`)
- Include common actions like save, cancel, error messages

### 6. Create Vue Components (Required)

Create your main view in `views/MyExtensionView.vue`:

```vue
<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('MyExtension.title') }}
    </div>

    <v-alert
      color="nnLightBlue200"
      icon="mdi-information-outline"
      class="text-nnTrueBlue mx-0 my-0 mb-6"
    >
      {{ $t('MyExtension.description') }}
    </v-alert>

    <v-card>
      <v-card-text>
        <!-- Your extension content here -->
        <p>Welcome to my extension!</p>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const isLoading = ref(false)

onMounted(() => {
  // Initialize your extension
  console.log(t('MyExtension.menu_label'), 'mounted')
})
</script>

<style scoped>
/* Component-specific styles */
</style>
```

**Key Component Patterns:**
- Use Composition API with `<script setup>`
- Import `useI18n` for translations
- Use Vuetify components (v-card, v-btn, v-data-table, etc.)
- Follow the project's styling conventions

### 7. Add API Client (Optional)

If your extension needs to call backend APIs, create `api/extensions.js`:

```javascript
import repository from '../../../api/repositoryExtensions'

export default {
  getMyData(params = {}) {
    return repository.get(`/my-extension/data`, { params })
  },
  
  createMyData(data) {
    return repository.post(`/my-extension/data`, data)
  },
  
  updateMyData(id, data) {
    return repository.patch(`/my-extension/data/${id}`, data)
  },
  
  deleteMyData(id) {
    return repository.delete(`/my-extension/data/${id}`)
  },
}
```

**API Repository:**
- Use `repositoryExtensions` which points to the extensions API endpoint
- Returns Axios promises
- Automatically handles authentication headers

**Using API in Components:**

```vue
<script setup>
import extensionsApi from '../api/extensions'

const loadData = async () => {
  try {
    const response = await extensionsApi.getMyData()
    console.log(response.data)
  } catch (error) {
    console.error('Error loading data:', error)
  }
}
</script>
```

### 8. Run OpenStudyBuilder Application (Including Your Extension)

Start the development server:

```bash
yarn dev
```

Your extension will be automatically loaded and accessible at:
- URL: `http://localhost:5173/administration/my-extension`
- Menu: Visible in the Administration sidebar

### 9. Test Your Extension

Run code quality checks:

```bash
# Format code
yarn format

# Lint code
yarn lint
```

## Vuetify Components

Extensions should use Vuetify 4 components for consistency:

### Common Components

```vue
<!-- Cards -->
<v-card elevation="0" rounded="lg">
  <v-card-title>Title</v-card-title>
  <v-card-text>Content</v-card-text>
  <v-card-actions>
    <v-btn>Action</v-btn>
  </v-card-actions>
</v-card>

<!-- Buttons -->
<v-btn
  color="primary"
  variant="flat"
  rounded="lg"
  prepend-icon="mdi-check"
  @click="handleClick"
>
  {{ $t('MyExtension.save') }}
</v-btn>

<!-- Data Tables -->
<v-data-table
  :headers="headers"
  :items="items"
  :loading="isLoading"
  item-key="uid"
>
  <template #[`item.actions`]="{ item }">
    <v-btn
      icon="mdi-pencil"
      size="small"
      @click="edit(item)"
    />
  </template>
</v-data-table>

<!-- Alerts -->
<v-alert
  color="nnLightBlue200"
  icon="mdi-information-outline"
  class="text-nnTrueBlue"
>
  {{ $t('MyExtension.info') }}
</v-alert>

<!-- Text Fields -->
<v-text-field
  v-model="value"
  :label="$t('MyExtension.field_label')"
  variant="outlined"
  rounded="lg"
  color="nnBaseBlue"
  density="compact"
/>
```

Refer to [Vuetify 4 Documentation](https://vuetifyjs.com/) for more components.

## Best Practices

1. **Naming Convention**: Use kebab-case for folder names (e.g., `my-extension`)
2. **Component Names**: Use PascalCase for Vue components (e.g., `MyExtensionView.vue`)
3. **Route Names**: Use PascalCase for route names (e.g., `name: 'MyExtension'`)
4. **Translations**: Namespace all translations under your extension name
5. **Feature Flags**: Use feature flags to control extension visibility
6. **Permissions**: Set appropriate RBAC permissions on routes
7. **Loading States**: Always show loading states for async operations
8. **Error Handling**: Handle errors gracefully with user-friendly messages
9. **Responsive Design**: Ensure your extension works on different screen sizes
10. **Code Style**: Follow the project's ESLint and Prettier configurations

## Authentication & Authorization

Extensions inherit the authentication system from the main application:

```javascript
import roles from '@/constants/roles'

// Route-level authentication
const myRoute = {
  path: 'my-extension',
  name: 'MyExtension',
  component: () => import('../views/MyExtensionView.vue'),
  meta: {
    authRequired: true,                    // Require authentication
    requiredPermission: roles.ADMIN_READ,  // Require specific permission
  },
}
```

**Available Roles:**
- `roles.ADMIN_READ` - Admin read access
- `roles.ADMIN_WRITE` - Admin write access
- Check `src/constants/roles.js` for all available roles

## Common Patterns

### Using Pinia Stores

```javascript
// In your component
import { useMyStore } from '@/stores/myStore'

const myStore = useMyStore()

// Access state
const items = computed(() => myStore.items)

// Call actions
await myStore.fetchItems()
```

### Form Validation

```vue
<script setup>
import { inject } from 'vue'

const formRules = inject('formRules')
</script>

<template>
  <v-form ref="form">
    <v-text-field
      v-model="email"
      :label="$t('field.email')"
      :rules="[formRules.required, formRules.email]"
    />
  </v-form>
</template>
```

### Notifications

```vue
<script setup>
import { useNotificationHub } from '@/composables/notifications'

const notificationHub = useNotificationHub()

const showSuccess = () => {
  notificationHub.add({
    msg: t('MyExtension.success_message'),
    type: 'success',
  })
}

const showError = () => {
  notificationHub.add({
    msg: t('MyExtension.error_message'),
    type: 'error',
  })
}
</script>
```

### Tabs Navigation

```vue
<template>
  <NavigationTabs :tabs="tabs">
    <template #default="{ tabKeys }">
      <v-window-item value="tab1">
        <v-card :key="`tab1-${tabKeys['tab1']}`">
          <!-- Tab 1 content -->
        </v-card>
      </v-window-item>
      <v-window-item value="tab2">
        <v-card :key="`tab2-${tabKeys['tab2']}`">
          <!-- Tab 2 content -->
        </v-card>
      </v-window-item>
    </template>
  </NavigationTabs>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import NavigationTabs from '@/components/ui/NavigationTabs.vue'

const { t } = useI18n()

const tabs = [
  { key: 'tab1', label: t('MyExtension.tab1') },
  { key: 'tab2', label: t('MyExtension.tab2') },
]
</script>
```

## Troubleshooting

### Extension Not Loading
- Verify the folder structure matches the required pattern
- Check browser console for JavaScript errors
- Ensure `addExtensionRoutes` function is exported from `router/index.js`
- Verify translations are properly exported

### Menu Item Not Appearing
- Check that the section name matches (`Administration`, `Library`, or `Studies`)
- Verify the feature flag is enabled if used
- Ensure user has required permissions
- Check that menu item is added to the correct section in `stores/app.js`

### Route Not Working
- Verify route is added to the correct parent route
- Check that component path in `import()` is correct
- Ensure route name is unique
- Verify authentication and permission requirements

### Translations Not Working
- Check that `locales/en/index.js` exports the translations
- Verify translation keys match usage in components
- Ensure translations are namespaced correctly
- Check browser console for i18n warnings

## Examples

Refer to the existing **hello** extension for a complete working example.

## Development Workflow

1. **Create Extension Structure** - Set up folders and files
2. **Define Routes** - Add routes to appropriate sections
3. **Add Menu Items** - Make extension discoverable
4. **Create Translations** - Add i18n support
5. **Build Components** - Create Vue components
6. **Add API Client** - Connect to backend if needed
7. **Test Locally** - Run `yarn dev` and test thoroughly
8. **Code Quality** - Run `yarn format` and `yarn lint`
9. **Documentation** - Add comments and update README if needed

## Support

For questions or issues with the extensions system:
1. Review the `hello` extension for working examples
2. Check the main Vue.js and Vuetify documentation
3. Consult the team's development guidelines
4. Review the core application's patterns in `src/`
