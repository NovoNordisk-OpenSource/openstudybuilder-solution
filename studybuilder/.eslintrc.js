module.exports = {
  root: true,
  parserOptions: {
    sourceType: 'module',
    ecmaVersion: 2022,
  },
  env: {
    node: true,
  },
  extends: ['plugin:vue/vue3-recommended', 'eslint:recommended', 'prettier'],
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
  },
}
