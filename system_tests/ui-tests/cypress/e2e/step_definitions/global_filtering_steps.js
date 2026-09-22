const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let filterValue

When('Users enables filters in the form window', () => cy.get('.v-overlay [data-cy="filters-button"]').click())

When('The Final status is selected by default', () => cy.get('.v-btn--active[value="final"]').should('be.visible'))

When('The user filters field {string}', (fieldName) => {
    cy.longWaitForTable()
    cy.clickButton("filters-button", false)
    cy.contains('[data-cy="filter-field"]', fieldName).click()
    cy.intercept('**filters=**').as('filterRequest')
    cy.get('.v-overlay__content .v-list').filter(':visible').find('.v-list-item').first().should('not.contain.text', 'No data available').click({ force: true })
    cy.wait('@filterRequest') //wait for the first request
})

When('The user filters study list by field {string}', (fieldName) => {
    cy.longWaitForTable()
    cy.get('button .mdi-filter-outline').click()
    cy.contains('.filterAutocompleteLabel [role="combobox"]', fieldName).click().then(() => {
        cy.get('.v-overlay__content .v-list').filter(':visible').should('not.contain', 'No data available')
        cy.get('.v-overlay__content .v-list').filter(':visible').find('.v-list-item-title').first().then((element) => {
            cy.wrap(element).invoke('text').then(value => {
                cy.wrap(element).click()
                cy.longWaitForTable()
                cy.checkRowByIndex(0, fieldName, value.slice(0, 60))
            })
        })
    })
})

When('The status filter is not available when expanding available filters', () => {
    cy.clickButton("filters-button", false)
    cy.contains('[data-cy="filter-field"]', 'Status').should('not.exist')
})

When('The user filters table by status {string}', (statusValue) => filterByStatus(statusValue, true))

When('The user changes status filter value to {string}', (statusValue) => filterByStatus(statusValue, false))

Then('The table is filtered correctly', () => {
    cy.get('@filterRequest.all').its('length').then(len => {
        for (let i = 1; i < len; i++) {
            //wait for remaining requests and check response status code
            cy.wait('@filterRequest').then(request => expect(request.response.statusCode).to.equal(200))
        }
    })
})

When('The user adds status to filters', () => cy.addTableFilter('Status'))

function filterByText() {
    cy.intercept('**filters=**').as('filterRequest')
    cy.get('.v-overlay__content .v-list').filter(':visible').find('.v-list-item').first().should('not.contain.text', 'No data available').click({ force: true })
    cy.wait('@filterRequest') //wait for the first request
}

function filterByDate() {
    //datepicker - to be implemented
}

function filterByStatus(statusValue, initialFiltering) {
    cy.longWaitForTable()
    if (initialFiltering) cy.clickButton("filters-button", false)
    cy.get('button.clearAllBtn').filter(':visible').click()
    cy.contains('[data-cy="filter-field"]', 'Status').click()
    cy.get('.v-overlay__content .v-list').filter(':visible').should('not.contain', 'No data available')
    cy.get('.v-overlay__content .v-list').filter(':visible').contains('.v-list-item', statusValue).find('input').click()
    cy.wait(500)
}