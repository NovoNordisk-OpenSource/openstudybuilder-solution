const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('User sets row page to {int} in the settings menu', (rowsPerPage) => {
    cy.sendUpdateRequest('PATCH', '/user-preferences', {"rows_per_page": rowsPerPage})
})