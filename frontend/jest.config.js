module.exports = {
  preset: '@vue/cli-plugin-unit-jest',
  transform: {
    'vee-validate/dist/rules': 'babel-jest',
    '\\.md$': 'jest-raw-loader',
  },
  transformIgnorePatterns: [
    '<rootDir>/node_modules/(?!(vee-validate/dist/rules' +
      '|@okta/okta-auth-js' +
      '|vuetify' +
      '))',
  ],
  collectCoverage: true,
  collectCoverageFrom: [
    '**/src/**',
    '!**/node_modules/**',
    '!**/dist/**',
    '!**/src/locales/**',
    '!**/src/plugins/**',
    '!**/tests/unit/**',
  ],
  coverageReporters: ['lcov', 'text-summary', 'text'],
  setupFiles: ['./tests/setup.js'],
  reporters: [
    'default',
    [
      'jest-sonar',
      {
        outputDirectory: 'results',
        outputName: 'sonar-report.xml',
        reportedFilePath: 'absolute',
      },
    ],
  ],
}
