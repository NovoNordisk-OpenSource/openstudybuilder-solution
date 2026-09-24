const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
import { currentDate } from "../../support/helper_functions";

let currentTimestamp = currentDate()

When('A Controlled Terminology Version is added', () => {
    cy.clickButton('add-ct-standard-version')
    cy.selectFirstVSelect('sponsor-ct-package-dropdown')    
    cy.fillInput('description-field','Test Description')
})

Then('The Controlled Terminology Version data is reflected in the table', () => {
    cy.checkLastRow('CT Catalogue', 'SDTM CT')
    cy.checkLastRow('CDISC CT Package', 'SDTM CT 2014-09-26')
    cy.checkLastRow('Sponsor CT Package', 'Sponsor SDTM CT 2024-07-15')
    cy.checkLastRow('Description', 'Test Description')
    cy.checkLastRow('Modified', currentTimestamp)
    cy.checkLastRow('Modified by', '8e0e7301-7bd3-49f2-b39e-e7fdd4dcdd22')

})

When('The Controlled Terminology Version is edited', () => {
    currentTimestamp = currentDate()
    cy.get('.mdi-menu-down').click()
    cy.selectFirstVSelect('sponsor-ct-package-dropdown')    
    cy.fillInput('description-field','Edited description')
})

Then('The edited Controlled Terminology Version data is reflected in the table', () => {
    cy.checkLastRow('CT Catalogue', 'SDTM CT')
    cy.checkLastRow('CDISC CT Package', 'SDTM CT 2014-09-26')
    cy.checkLastRow('Sponsor CT Package', 'Sponsor SDTM CT 2024-07-15')
    cy.checkLastRow('Description', 'Edited description')
    cy.checkLastRow('Modified', currentTimestamp)
    cy.checkLastRow('Modified by', '8e0e7301-7bd3-49f2-b39e-e7fdd4dcdd22')
})

Then('The Controlled Terminology Version data is removed from the table', () => {
    cy.tableContains('No data available')
})

When('The user opens show version history', () => {
    cy.clickButton('show-ct-standard-version-history')
})

When('The user is presented with version history of the output containing timestamp and username', () => {
    checkHistoryData()
    cy.checkLastRow('From', currentTimestamp)
    cy.checkLastRow('To', currentTimestamp)
})

When('The user clicks on History for particular element', () => checkHistoryData())

function checkHistoryData() {
    cy.get('[data-cy="version-history-window"]').should('contain', 'Standard version selections history')
    cy.get('[data-cy="version-history-window"]').should('contain', 'CT Catalogue')
    cy.get('[data-cy="version-history-window"]').should('contain', 'Sponsor CT Package')
    cy.get('[data-cy="version-history-window"]').should('contain', 'Description')
    cy.get('[data-cy="version-history-window"]').should('contain', 'Change type')
    cy.get('[data-cy="version-history-window"]').should('contain', 'User')
    cy.get('[data-cy="version-history-window"]').should('contain', 'From')
    cy.get('[data-cy="version-history-window"]').should('contain', 'To')
}