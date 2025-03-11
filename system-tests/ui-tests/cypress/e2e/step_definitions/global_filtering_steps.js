const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let filterValue

When('The user filters field {string}', (fieldName) => {
    cy.longWaitForTable()
    cy.clickButton("filters-button", false)
    cy.contains('[data-cy="filter-field"]', fieldName).click().then($filterField => {
        $filterField.find('.mdi-calendar-outline').length > 0 ? filterByDate() : filterByText()
    })
    cy.wait(500)
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

function filterByText() {
    cy.get('.v-overlay__content .v-list').filter(':visible').should('not.contain', 'No data available')
    cy.get('.v-overlay__content .v-list').filter(':visible').within(() => {
        cy.get('.v-list-item-title').first().then((element) => {
            cy.wrap(element).invoke('text').then(value => filterValue =  value.slice(0, 60))
            cy.intercept('**/headers**').as('filterRequest')
            cy.wrap(element).click()
        })
    })
    cy.wait(1500)
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
    cy.get('.v-overlay__content .v-list').filter(':visible').contains(statusValue).click()
    cy.wait(1500)
}