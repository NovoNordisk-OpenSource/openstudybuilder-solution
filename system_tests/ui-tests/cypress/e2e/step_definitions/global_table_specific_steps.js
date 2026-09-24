const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('Table contains value {string}', (value) => cy.contains('table tbody tr', value).should('be.visible'))

When('No results are returned in the form table', () => cy.get('.v-overlay tbody tr').should('have.text', 'No data available'))

When('User waits for the table', () => cy.longWaitForTable(60000))

When('User adds column {string} to filters', (headerName) => cy.tableHeaderActions(headerName, 'Add to filter'))

When('User sets status filter to {string}', (filterValue) => {
    cy.get(`.layoutSelector button[value=${filterValue}]`).filter(':visible').click()
    cy.longWaitForTable()
})

When('User searches for {string}', (value) => cy.searchAndCheckPresence(value, true))

When('User searches for {string} and confirms no results returned', (value) => cy.searchAndCheckPresence(value, false))

When('Only one row is present', () => cy.checkOnlyOneResultReturned())

Then('The item has status {string} and version {string}', (status, version) => {
    cy.checkRowByIndex(0, 'Status', status)
    cy.checkRowByIndex(0, 'Version', version)
})

Then('A table is visible with following headers', (headers) => {
    headers.rows().forEach((header) => cy.headerContains(header))
})

Then('A table is visible with following options', (dataTable) => {
    dataTable.rows().forEach(option => {
        const locator = option[0] == 'History' ? '.mdi-history' : `[data-cy="${option[0]}"]`
        cy.get(locator).should('be.visible')
    })
})

Then('The table is visible and not empty', () => cy.waitForTableData())

Then('The table is loaded', () => cy.waitForTable())

Then('The {string} row contains following values', (key, dataTable) => {
    cy.waitForTableData()
    cy.searchAndCheckPresence(key, true)
    dataTable.hashes().forEach(element => cy.checkRowByIndex(0, element.column, element.value))
})

Then('The search field is available in the table', () => cy.get('[data-cy="search-field"]').should('be.visible'))

Then('The table display the note {string}', (note) => cy.tableContains(note))

Then('The table display following predefined data', (dataTable) => {
    cy.waitForTable()
    cy.tableContainsPredefinedData(dataTable)
})

When('The {string} option is clicked from the three dot menu list', (action) => cy.performActionOnSearchedItem(action))

When('The {string} option is clicked for flagged item', (action) => cy.performActionOnFlaggedItem(action))

When('The item actions button is clicked', () => cy.clickTableActionsButton(0))

When('{string} action is available', action => cy.get(`[data-cy="${action}"]`).should('be.visible'))

When('{string} action is not available', action => cy.get(`[data-cy="${action}"]`).should('not.exist'))

Then('More than one result is found', () => cy.checkIfMoreThanOneResultFound())

Then('The not existing item is searched for', () => cy.searchFor('gregsfs'))

Then('The existing item is searched for by partial name', () => cy.searchFor('SearchTest'))

Then('The existing item in search by lowercased name', () => cy.searchFor('searchtest'))

Then('The item is not found and table is correctly filtered', () => cy.confirmNoResultsFound())

Then('Only actions that should be avaiable for the Codelist are displayed', () => {
    const allowedActions = ['Edit', 'Show terms', 'History']
    const notAllowedActions = ['New version', 'Inactivate', 'Reactivate', 'Delete', 'Approve']
    checkActionsAvailability(allowedActions, notAllowedActions)
})

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

Then('Only actions that should be avaiable for the Draft Activity Instance are displayed', () => {
    const allowedActions = ['Approve attributes', 'Approve groupings', 'Edit attributes', 'Edit groupings', 'Delete', 'History (attributes)', 'History (groupings)']
    const notAllowedActions = ['New version (attributes)', 'New version (groupings)', 'Inactivate', 'Reactivate']
    checkActionsAvailability(allowedActions, notAllowedActions)
})

Then('Only actions that should be avaiable for the Final Activity Instance are displayed', () => {
    const allowedActions = ['New version (attributes)', 'New version (groupings)', 'Inactivate', 'History (attributes)', 'History (groupings)']
    const notAllowedActions = ['Edit attributes', 'Edit groupings', 'Delete', 'Approve attributes', 'Approve groupings', 'Reactivate']
    checkActionsAvailability(allowedActions, notAllowedActions)
})

Then('Only actions that should be avaiable for the Retired Activity Instance are displayed', () => {
    const allowedActions = ['Reactivate', 'History (attributes)', 'History (groupings)']
    const notAllowedActions = ['New version (attributes)', 'New version (groupings)', 'Inactivate', 'Edit attributes', 'Edit groupings', 'Delete', 'Approve attributes', 'Approve groupings']
    checkActionsAvailability(allowedActions, notAllowedActions)
})

When('The user switches pages of the table', () => {
    cy.waitForTable()
    cy.intercept('**page_number=2**').as('tablePage')
    cy.get('.v-data-table-footer__pagination .mdi-chevron-right').click()
})

Then('The table page presents correct data', () => {
    cy.wait('@tablePage').its('response.statusCode').should('eq', 200)
})

function checkActionsAvailability(allowedActions, notAllowedActions) {
    allowedActions.forEach(action => cy.get(`[data-cy="${action}"]`).should('be.visible'))
    notAllowedActions.forEach(action => cy.get(`[data-cy="${action}"]`).should('not.exist'))
}
