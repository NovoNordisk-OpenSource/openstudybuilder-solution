const { Then } = require('@badeball/cypress-cucumber-preprocessor')

Then('Export button is available', () => {
    cy.get('button[title="Export"]').click()
    cy.get('.v-overlay-container .v-list').should('contain', 'JSON')
})

Then('A JSON text field showing the study definition in USDM format is displayed', () => {
    cy.get('button[title="Export"]').click()
    cy.get('[id="json-data"]').invoke('text').then(text => expect(isValidJsonFormat(text)).to.be.true)
})

function isValidJsonFormat(text) {
    try {
        JSON.parse(text)
        return true
    } catch (e) {
        cy.log('Text is not parsable to JSON!')
        return false
    }
}