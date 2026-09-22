const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");


Then('The user is presented with {string} layout', (select) => cy.contains('.v-window .v-btn--active', select).should('be.visible'))

Then('Protocol page has following options available: Split SoA, Show epochs, Show milestones', () => {
    cy.contains('.v-row .v-selection-control', 'Split SoA')
    cy.contains('.v-row .v-selection-control', 'Show epochs')
    cy.contains('.v-row .v-selection-control', 'Show milestones')
})

When('The SoA split is created on {string}', (visitNumber) => {
    cy.contains('.split-class', visitNumber).within(() => cy.get('.mdi-content-cut').should('exist'))
})

When('The SoA Splitting is enabled', () => cy.contains('Split SoA').click({force: true}))

When('The user splits-unsplits the SoA by {string}', (visitNumber) => cy.contains('.v-btn__content', visitNumber).click())

When('The user unsplits the SoA by {string}', (visitNumber) => splitSoa(visitNumber, '**/soa-splits/**'))

Then('The SoA split on {string} is removed', (visitNumber) => cy.contains('.split-class', visitNumber).should('not.exist'))

When('User intercepts split soa request', () => cy.intercept('**/soa-splits').as('splitRequest'))

When('User intercepts unsplit soa request', () => cy.intercept('**/soa-splits/**').as('splitRequest'))

When('User waits for split soa request', () => cy.wait('@splitRequest').then(request => expect(request.response.statusCode).to.eq(200)))

When('Footnote index {string} has footnote text {string} displayed on the protocol page', (index, text) => {
    cy.contains('[id="protocolFlowchart"] .footnote', index).should('contain.text', text)
})

When('Footnote {string} is no longer available on the protocol page', (text) => {
    cy.contains('[id="protocolFlowchart"] .footnote', text).should('not.exist')
})

When('Footnote index {string} is assgined to visit {string} for activity {string}', (footnoteIndex, visit, activity) => {
    cy.contains('tr', 'Visit short name').contains('th', visit).invoke('index').then(index => {
        cy.contains('tr .activity', activity).parent().find('td').eq(index - 1).should('contain.text', footnoteIndex)
    })
})

When('Footnote index {string} is assgined to activity {string}', (footnoteIndex, activity) => {
    cy.contains('tr .activity', activity).should('contain.text', footnoteIndex)
})

When('Footnote index {string} is not assgined to activity {string}', (footnoteIndex, activity) => {
    cy.contains('tr .activity', activity).should('not.contain.text', footnoteIndex)
})