Cypress.Commands.add('waitForTable', () => waitForTableToStopLoading(10000))

Cypress.Commands.add('longWaitForTable', () => waitForTableToStopLoading(30000))

Cypress.Commands.add('waitForTableData', () => {
    cy.get('.v-table__wrapper')
        .should('not.contain', 'Loading items...')
        .and('not.contain', 'No data available')
        .and('not.contain', 'No matching records found')
})

Cypress.Commands.add('waitForPage', () => {
    cy.get('.v-container', {timeout: 20000}).should('be.visible')
})

Cypress.Commands.add('waitForFormSave', () => {
    cy.get('[data-cy="form-body"]').should('not.be.visible')
})

Cypress.Commands.add('waitForData', (dataName) => {
    cy.intercept('**/' + dataName + '**').as('waitingForThisRequest')
    cy.wait('@waitingForThisRequest')
})

function waitForTableToStopLoading(timeout) {
    cy.get('.v-table__wrapper', {timeout: timeout}).should('not.contain', 'Loading items...')
    cy.get('.v-data-table--loading', {timeout: timeout}).should('not.exist')
}