const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");
import { getCurrentDateYYYYMMDD } from "../../support/helper_functions";

let today_date = getCurrentDateYYYYMMDD()

When('The Create First One button is pressed on the Sponsor CT Package page', () => {
    cy.get('.v-card-text > .v-btn').click()
})

When('The Sponsor CT Package form is populated and saved', () => {
    startSponsorCTPackageCreation();
    cy.contains('SDTM CT 2014-09-26').click()
    cy.clickButton('save-button')
})

Then('The table presents created Sponsor CT Package', () => {
    cy.get('[data-cy="timeline-date"]').should('contain', today_date)
})

When('Sponsor CT Package is created for the same date as already existing one', () => {
    cy.createCTPackage('SDTM CT 2014-12-19')
    cy.waitForTable()
    cy.get('.mdi-plus').click()
    startSponsorCTPackageCreation()
    cy.contains('SDTM CT 2014-12-19').click()
    cy.clickButton('save-button')
})

function startSponsorCTPackageCreation() {
    cy.wait(1000)
    cy.get('[data-cy="sponsor-ct-catalogue-dropdown"] [role="combobox"]').click()
    cy.get('.v-overlay__content .v-list-item').contains('SDTM CT').click()
    cy.get('.v-overlay__content [role="combobox"]').eq(1).click()
}
