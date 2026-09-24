const js = require('@eslint/js')
const eslintConfigPrettier = require('eslint-config-prettier')
const vue = require('eslint-plugin-vue')
const globals = require('globals')

module.exports = [
  {
    ignores: [
      '.DS_Store',
      'dist/**',
      '*.gz',
      '.env*',
      'coverage/**',
      'cypress/screenshots/**',
      'cypress/videos/**',
      'results/**',
      'playwright-report/**',
      'test-results/**',
    ],
  },
  js.configs.recommended,
  ...vue.configs['flat/recommended'],
  {
    files: ['**/*.{js,mjs,vue}'],
    languageOptions: {
      ecmaVersion: 2022,
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.node,
        globalThis: 'readonly',
        __DEMO_GIT_COMMIT__: 'readonly',
      },
    },
    rules: {
      'vue/no-v-html': 'off',
      'vue/no-template-shadow': 'off',
      'vue/component-name-in-template-casing': [
        'error',
        'PascalCase',
        {
          registeredComponentsOnly: true,
          ignores: [],
        },
      ],
      'require-atomic-updates': 'off',
      'no-unused-vars': [
        'error',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
          caughtErrorsIgnorePattern: '^_',
        },
      ],
      'no-useless-assignment': 'off',
    },
  },
  eslintConfigPrettier,
]
