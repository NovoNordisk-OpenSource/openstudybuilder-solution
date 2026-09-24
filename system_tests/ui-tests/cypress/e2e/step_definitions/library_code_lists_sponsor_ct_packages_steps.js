const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");
import { getCurrentDateYYYYMMDD } from "../../support/helper_functions";

let today_date = getCurrentDateYYYYMMDD(), availablePackage

When('The Create First One button is pressed on the Sponsor CT Package page', () => {
    cy.get('.v-card-text > .v-btn').click()
})

When('The Sponsor CT Package form is populated and saved', () => {
    startSponsorCTPackageCreation();
    cy.contains('SDTM CT 2014-09-26').click()
})

Then('The table presents created Sponsor CT Package', () => {
    cy.get('[data-cy="timeline-date"]').should('contain', today_date)
})

When('[API] User fetches first available package on ADAM CT', () => cy.getAvailablePackageName('SDTM+CT').then(packageName => availablePackage = packageName))

When('[API] User creates a package if it doesn not exists', () => cy.createCTPackage(availablePackage))

When('Sponsor CT Package is created for the same date as already existing one', () => {
    cy.waitForTable()
    cy.get('.mdi-plus').click()
    startSponsorCTPackageCreation()
    cy.contains(availablePackage.replaceAll('__', ' ')).click()
})

function startSponsorCTPackageCreation() {
    cy.wait(1000)
    cy.get('[data-cy="sponsor-ct-catalogue-dropdown"] .v-field__input').click()
    cy.get('.v-overlay__content .v-list-item').contains('SDTM CT').click()
    cy.contains('[role="combobox"]', 'Select a CDISC CT package').click()
}
