const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Given("[API] The feature flag {string} is enabled", (feature_flag) => enableFlag(feature_flag, true))

Given("[API] The feature flag {string} is disabled", (feature_flag) => enableFlag(feature_flag, false))

When('User switch to {string} feature flags', (name) => cy.contains('.layoutSelector button', name).click())

When('User enables {string} feature flag', (name) => toggleOnOff(name, true))

When('User disables {string} feature flag', (name) => toggleOnOff(name, false))

function toggleOnOff(featureName, on) {
  cy.contains('table tbody tr', featureName).find('.v-switch input').then(el => on ? cy.wrap(el).check() : cy.wrap(el).uncheck())
}

function enableFlag(flagName, state) {
  cy.sendGetRequest('/feature-flags?include_retired=true').then((response) => {
    const flag = response.body.find(
      (element) => element.name === flagName || element.feature === flagName
    )
    expect(
      flag,
      `Feature flag '${flagName}' not found in GET /feature-flags response`
    ).to.exist
    cy.sendUpdateRequest('PATCH', `/feature-flags/${flag.uid}`, { enabled: state })
  })
}