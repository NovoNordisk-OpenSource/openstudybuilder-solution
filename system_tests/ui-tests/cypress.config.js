const { defineConfig } = require('cypress')
const createBundler = require('@bahmutov/cypress-esbuild-preprocessor')
const preprocessor = require('@badeball/cypress-cucumber-preprocessor')
const createEsbuildPlugin = require('@badeball/cypress-cucumber-preprocessor/esbuild')
const allureWriter = require('@shelex/cypress-allure-plugin/writer')

async function setupNodeEvents(on, config) {
  await preprocessor.addCucumberPreprocessorPlugin(on, config)

  on(
    'file:preprocessor',
    createBundler({
      plugins: [createEsbuildPlugin.default(config)],
    })
  )

  allureWriter(on, config)

  return config
}

module.exports = defineConfig({
  env: {},
  video: false,
  screenshotOnRunFailure: true,
  // numtestskeptinmemory: 1,
  experimentalMemoryManagement: false,
  defaultCommandTimeout: 10000,
  viewportWidth: 1920,
  viewportHeight: 1080,
  e2e: {
    setupNodeEvents,
    reporter: 'junit',
    reporterOptions: {
    mochaFile: 'results/junit/results-[hash].xml',
  },

    baseUrl: 'https://studybuilder.clinicalmdr-dev.corp.azure.novonordisk.com',
    specPattern: 'cypress/e2e/**/*.feature',
    experimentalStudio: true
    },
})
