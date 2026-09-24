const { defineConfig } = require("cypress");
const createBundler = require("@bahmutov/cypress-esbuild-preprocessor");
const preprocessor = require("@badeball/cypress-cucumber-preprocessor");
const createEsbuildPlugin = require("@badeball/cypress-cucumber-preprocessor/esbuild");
const allureWriter = require("@shelex/cypress-allure-plugin/writer");

async function setupNodeEvents(on, config) {
  await preprocessor.addCucumberPreprocessorPlugin(on, config);

  on(
    "file:preprocessor",
    createBundler({
      plugins: [createEsbuildPlugin.default(config)],
    })
  );
  allureWriter(on, config);

  return config;
}

module.exports = defineConfig({
  e2e: {
    baseUrl: 'https://studybuilder.clinicalmdr-dev.corp.azure.novonordisk.com/neodash/',
    experimentalStudio: true,
    video: false,
    numTestsKeptInMemory: 5,
    experimentalMemoryManagement:true,
    screenshotOnRunFailure: true,
    defaultCommandTimeout: 15000,
    viewportWidth: 1920,
    viewportHeight: 1080,
    specPattern: "cypress/e2e/features/**/*.feature",
    supportFile: "cypress/support/e2e.js",
    setupNodeEvents,
    reporter: 'junit',
    reporterOptions: {
    mochaFile: 'results/junit/[suiteName].xml',
  }
    
  },
});