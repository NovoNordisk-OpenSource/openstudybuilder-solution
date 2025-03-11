const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The {string} submenu is clicked in the {string} section', (submenu, section) => {
    cy.openFromSidebar(section, submenu)
})

When('The {string} tab is selected', (tabName) => {
    cy.clickTab(tabName)
})

When('The {string} button is clicked', (button) => {
    cy.clickButton(button)
})

When('The {string} button is clicked in Protocol Process page', (button) => {
    cy.get(`.v-card-text [data-cy="${button}"]`).click({force: true})
})

When('The {string} is clicked in the dropdown', (item) => cy.contains('.v-list-item--link', item).click({force: true}))

When('The last available item from timeline is clicked', () => {
    cy.waitForTable()
    cy.get('[data-cy="timeline-date"]').last().click()
})

When('The {string} is clicked in the dropdown of {string} tile', (link, tileName) => {
    expandPagesDropdown(tileName)
    cy.contains('.v-overlay__content .v-list-item-title', link).click()
    cy.wait(1000);
})

When('The {string} is not listed after the dropdown {string} is clicked', (link, tileName) => {
    expandPagesDropdown(tileName)
    cy.contains('.v-overlay__content .v-list-item-title', link).should('not.exist')
    cy.wait(1000);
})

Then('The form is not closed', () => {
    cy.get('[data-cy="form-body"]').should('be.visible')
})

When('The continue is clicked in confirmation popup', () => {
    cy.clickButton('continue-popup')
})

function expandPagesDropdown(tileName) {
    cy.wait(500)
    cy.get(`[data-cy="tiles-box"] [data-cy="${tileName}"] [data-cy="dropdown-button"]`).click()
    cy.wait(500)
}