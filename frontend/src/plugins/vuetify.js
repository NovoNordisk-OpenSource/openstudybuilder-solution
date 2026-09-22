import 'vuetify/styles'
import '@/styles/global.scss'
import '@fontsource-variable/open-sans'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'

export const DEFAULT_THEME = 'NNCustomLightTheme'

// Each file in ./themes/ default-exports a Vuetify theme definition (dark/colors)
// plus a display `title`. Adding a theme is just adding a file here.
const themeModules = import.meta.glob('./themes/*.js', { eager: true })
export const APP_THEMES = Object.fromEntries(
  Object.entries(themeModules).map(([path, mod]) => [
    path.match(/\/([^/]+)\.js$/)[1],
    mod.default,
  ])
)

export const THEME_NAMES = Object.keys(APP_THEMES)

const vuetify = createVuetify({
  defaults: {
    VBtn: {
      class: 'text-uppercase',
    },
    VTextField: {
      variant: 'outlined',
      density: 'compact',
      rounded: 'lg',
      autocomplete: 'off',
    },
    VTextarea: {
      variant: 'outlined',
      density: 'compact',
      rounded: 'lg',
      autocomplete: 'off',
    },
    VSelect: {
      variant: 'outlined',
      density: 'compact',
      rounded: 'lg',
      autocomplete: 'off',
    },
    VAutocomplete: {
      variant: 'outlined',
      density: 'compact',
      rounded: 'lg',
      autocomplete: 'off',
    },
    VCombobox: {
      variant: 'outlined',
      density: 'compact',
      rounded: 'lg',
      autocomplete: 'off',
    },
    VFileInput: {
      variant: 'outlined',
      density: 'compact',
      rounded: 'lg',
    },
    VNumberInput: {
      variant: 'outlined',
      density: 'compact',
      rounded: 'lg',
    },
    VCheckbox: {
      density: 'compact',
      color: 'primary',
    },
    VCheckboxBtn: {
      density: 'compact',
      color: 'primary',
    },
    VRadio: {
      density: 'compact',
      color: 'primary',
    },
    VRadioGroup: {
      density: 'compact',
      color: 'primary',
    },
    VSwitch: {
      density: 'compact',
      color: 'primary',
    },
  },
  theme: {
    defaultTheme: DEFAULT_THEME,
    themes: APP_THEMES,
  },
})

export function setApplicationTheme(themeName) {
  vuetify.theme.global.name.value = THEME_NAMES.includes(themeName)
    ? themeName
    : DEFAULT_THEME
}

export default vuetify
