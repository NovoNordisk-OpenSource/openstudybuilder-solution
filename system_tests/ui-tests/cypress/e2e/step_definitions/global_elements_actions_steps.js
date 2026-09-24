const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Then("The {string} is displayed", (value) => cy.get("body").should("contain", value));

When('The {string} submenu is clicked in the {string} section', (submenu, section) => {
    cy.get('.v-navigation-drawer__content').within(() => {
        cy.clickButton(section).within(() => cy.clickButton(submenu))
    })
})

When('The {string} tab is selected', (tabName) => cy.contains('.v-tab', tabName).click({force: true}))

When('The {string} button is clicked', (button) => cy.clickButton(button))

When('The button with text {string} is clicked', (name) => cy.contains('button', name).click())

When('The {string} is clicked in the dropdown', (item) => cy.contains('.v-overlay__content .v-list-item', item).click())

When('The {string} is clicked in the dropdown of {string} tile', (link, tileName) => {
    expandPagesDropdown(tileName)
    cy.contains('.v-overlay__content .v-list-item-title', link).click()
})

When('The {string} is not listed after the dropdown {string} is clicked', (link, tileName) => {
    expandPagesDropdown(tileName)
    cy.contains('.v-overlay__content .v-list-item-title', link).should('not.exist')
})

Then('The form is not closed', () => cy.get('[data-cy="form-body"]').should('be.visible'))

When('The online help button is clicked', () => cy.get('.page-title .mdi-help-circle-outline').click())

Then('The online help panel shows {string} panel with content {string}', (panelName, helpText) => {
    cy.contains('.v-expansion-panel', panelName).then((el) => {
        cy.wrap(el).click()
        cy.wrap(el).within(() => {
            cy.get('.v-expansion-panel-text__wrapper div').invoke('text').then((text) => {
                expect(text.trim()).to.eq(helpText.trim());
            })
        })
    })
})

Then('All Not Applicable checkboxes are checked', () => cy.get('[data-cy="not-applicable-checkbox"] input').each((btn) => cy.wrap(btn).check()))

Then('The edit content button is clicked', () => {
    cy.clickButton('edit-content')
    cy.wait(1000)
})

Then('The pencil button is clicked', () => {
    cy.get('button .mdi-pencil-outline').click()
    cy.wait(1000)
})

Then('The pencil button is not available', () => cy.get('button .mdi-pencil-outline').should('not.exist'))

Then('The plus button is clicked', () => cy.get('button .mdi-plus').click())

When('The Save button is clicked', () => cy.contains('button', 'Save').click())

Then('The new version plus button is clicked', () => cy.get('button .mdi-plus-circle-outline').click())

Then('The new version plus button is not available', () => cy.get('button .mdi-plus-circle-outline').should('not.exist'))

Then('The approve button is clicked', () => cy.get('button .mdi-check-decagram').click())

Then('The approve button is not available', () => cy.get('button .mdi-check-decagram').should('not.exist'))

Then('The inactivate button is clicked', () => cy.get('button .mdi-close-octagon-outline').click())

Then('The inactivate button is not available', () => cy.get('button .mdi-close-octagon-outline').should('not.exist'))

Then('The download button is clicked', () => cy.get('button .mdi-download-outline').filter(':visible').click())

Then('The download button is available', () => cy.get('button .mdi-download-outline').should('be.visible'))

Then('The close overview button is clicked', () => cy.get('button .mdi-close').filter(':visible').click())

Then('The history button is clicked', () => cy.get('button .mdi-history').click())

function expandPagesDropdown(tileName) {
    cy.wait(500)
    cy.get(`[data-cy="tiles-box"] [data-cy="${tileName}"] [data-cy="dropdown-button"]`).click()
    cy.wait(500)
}