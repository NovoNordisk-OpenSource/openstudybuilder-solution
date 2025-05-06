const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Then('The item has status {string} and version {string}', (status, version) => cy.checkStatusAndVersion(status, version))

Then('A table is visible with following headers', (headers) => {
    headers.rows().forEach((header) => cy.headerContains(header))
})

Then('A table is visible with following options', (options) => {
    options.rows().forEach((option) => {
        const locator = option == 'search-field' ? `[data-cy="${option}"]` : `.v-card-title [title="${option}"]`
        cy.get(locator).should('be.visible')
    })
})

Then('The table is visible and not empty', () => {
    cy.waitForTable()
})

Then('The {string} row contains following values', (key, dataTable) => {
    cy.waitForTableData()
    cy.checkRowValues(key, dataTable)
})

When('The {string} action is clicked for first available item in table', (action) => {
    cy.waitForTableData()
    cy.tableRowActions(0, action)
})

Then('The following rows are available in first column', (values) => {
    let rowIndex = 0
    cy.waitForTableData()
    values.rows().forEach((value) => {
        cy.rowContains(rowIndex, value)
        rowIndex++
    })
})

Then('The search field is available in the table', () => cy.get('[data-cy="search-field"]').should('be.visible'))

Then('The table display the note {string}', (note) => {
    cy.tableContains(note)
})

Then('The table display following predefined data', (dataTable) => {
    cy.waitForTable()
    cy.tableCellContains(dataTable)
})

When('The user is searching for {string} value', (value) => {
    cy.intercept('**[%22Dummy%22]**').as('searchRequest')
    cy.wait(500)
    cy.fillInput('search-field', value)
})

Then('The results are shown in the table', () => {
    cy.wait('@searchRequest').then(requests => {
        expect(requests.response.statusCode).to.equal(200)
    })
})

When('The {string} option is clicked from the three dot menu list', (action) => {
    cy.performActionOnSearchedItem(action)
})

When('The item actions button is clicked', () => cy.clickTableActionsButton(0))

When('{string} action is available', action => cy.get(`[data-cy="${action}"]`).should('be.visible'))

Then('More than one item is found after performing partial name search', () => cy.searchAndCheckResults('SearchTest', false))

Then('More than one result is found', () => cy.checkSearchResults(false))

Then('The not existing item is searched for', () => cy.searchFor('gregsfs'))

Then('The existing item in status Draft is searched for', () => cy.searchFor('SearchTest'))

Then('The existing item in search by lowercased name', () => cy.searchFor('searchtest'))

Then('The item is not found and table is correctly filtered', () => cy.confirmNoResultsFound())

Then('Only actions that should be avaiable for the Draft item are displayed', () => {
    const allowedActions = ['Approve', 'Edit', 'Delete', 'History']
    const notAllowedActions = ['New version', 'Inactivate', 'Reactivate']
    checkActionsAvailability(allowedActions, notAllowedActions)
})

Then('Only actions that should be avaiable for the Final item are displayed', () => {
    const allowedActions = ['New version', 'Inactivate', 'History']
    const notAllowedActions = ['Edit', 'Delete', 'Approve', 'Reactivate']
    checkActionsAvailability(allowedActions, notAllowedActions)
})

Then('Only actions that should be avaiable for the Retired item are displayed', () => {
    const allowedActions = ['Reactivate', 'History']
    const notAllowedActions = ['New version', 'Inactivate', 'Edit', 'Delete', 'Approve']
    checkActionsAvailability(allowedActions, notAllowedActions)
})

When('The user switches pages of the table', () => {
    cy.waitForTable()
    cy.intercept('**page_number=2**').as('tablePage')
    cy.get('[data-test="v-pagination-next"]').click()

})

Then('The table page presents correct data', () => {
    cy.wait('@tablePage').its('response.statusCode').should('eq', 200)
})

function checkActionsAvailability(allowedActions, notAllowedActions) {
    allowedActions.forEach(action => cy.get(`[data-cy="${action}"]`).should('be.visible'))
    notAllowedActions.forEach(action => cy.get(`[data-cy="${action}"]`).should('not.exist'))
}
