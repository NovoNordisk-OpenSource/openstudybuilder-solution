import { createI18n } from 'vue-i18n'
import en from '@/locales/en'

// Dynamically load extension translations
const extensionLocales = import.meta.glob(
  '@/extensions/*/locales/en/index.js',
  {
    eager: true,
    import: 'default',
  }
)

// Merge extension translations with core translations
const mergedEnTranslations = { ...en }
for (const path in extensionLocales) {
  const extensionTranslations = extensionLocales[path]
  Object.assign(mergedEnTranslations, extensionTranslations)
}

const instance = createI18n({
  legacy: false,
  locale: import.meta.env.VUE_APP_I18N_LOCALE || 'en',
  fallbackLocale: import.meta.env.VUE_APP_I18N_FALLBACK_LOCALE || 'en',
  warnHtmlMessage: false,
  messages: {
    en: mergedEnTranslations,
  },
})

export default instance
export const i18n = instance.global
