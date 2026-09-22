const { Then } = require("@badeball/cypress-cucumber-preprocessor");

Then('The {string} title is visible', (title) => {
    cy.get('[data-cy="page-title"]').should('contain', title).and('be.visible')
})

Then('The following tabs are visible', (dataTable) => {
    dataTable.rows().forEach(tab => cy.get(`[data-cy="${tab}"]`).should('be.visible'))
})

Then('The following buttons are visible', (dataTable) => {
    dataTable.rows().forEach(element => cy.get(`[data-cy="${element}"]`).should('be.visible'))
})

Then('A tile {string} is visible with following description', (tileTitle, docstring) => {
    cy.get(`[data-cy="tiles-box"] [data-cy="${tileTitle}"] .v-expansion-panel-title`).click({ force: true })
    cy.get(`[data-cy="${tileTitle}"]`).should('contain', docstring)
})

Then('The user is prompted with a notification message {string}', (message) => {
    cy.get('.v-card-text').should('contain', message)
})

Then('The {string} button is visible', (buttonName) => {
    cy.get('.v-btn__content').should('contain', buttonName)
})

Then('The {string} button is not visible', button => cy.get(`[data-cy="${button}"]`).should('not.exist'))

Then('The {string} element is visible', button => cy.get(`[data-cy="${button}"]`).should('be.visible'))

Then('The {string} button is present', button => { cy.contains(button).should('exist') })

Then('The red alert badge is not present', () => {
    cy.get('[data-cy="data-table"]').within(() => {
        cy.get('.mdi-alert-circle-outline').should('not.exist')
    })
})

Then('The red alert badge is present', () => {
    cy.get('[data-cy="data-table"]').within(() => {
        cy.get('.mdi-alert-circle-outline').should('be.visible')
    })
})

Then('The yellow alert badge is not present', () => {
    cy.get('[data-cy="data-table"]').within(() => {
        cy.get('.mdi-alert-outline').should('not.exist')
    })
})

Then('The yellow alert badge is present', () => {
    cy.get('[data-cy="data-table"]').within(() => {
        cy.get('.mdi-alert-outline').should('be.visible')
    })
})