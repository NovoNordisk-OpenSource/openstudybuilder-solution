const { defineConfig } = require('cypress')
const preprocessor = require('@badeball/cypress-cucumber-preprocessor')
const browserify = require('@badeball/cypress-cucumber-preprocessor/browserify')
const allureWriter = require('@shelex/cypress-allure-plugin/writer')

async function setupNodeEvents(on, config) {
  await preprocessor.addCucumberPreprocessorPlugin(on, config)

  on('file:preprocessor', browserify.default(config))

  allureWriter(on, config)

  return config
}

module.exports = defineConfig({
  video: false,
  screenshotOnRunFailure: true,
  defaultCommandTimeout: 10000,
  viewportWidth: 1920,
  viewportHeight: 1080,
  e2e: {
    setupNodeEvents,
    reporter: 'junit',
    reporterOptions: {
    mochaFile: 'results/junit/[suiteName].xml',
  },

    baseUrl: 'https://openstudybuilder.com',
    specPattern: 'cypress/e2e/**/*.feature',
    experimentalStudio: true
    },
})
