export let objectName, objectVersion
let tableRowLocator = 'table tbody tr'
let tableRowLocatorInPopUp = '.v-sheet table tbody tr'
let tableHeaderLocator = 'table thead'
let tableHeaderCellLocator = 'table thead th'
let tableHeaderCellLocatorInPopUp = '.v-sheet table thead th'
let expandActionsLocator = 'table-item-action-button'
let regex = (column) => new RegExp(`^${column}$`, 'g')

Cypress.Commands.add('tableRowActions', (rowIndex, action) => {
    clickTableActionsButton(rowIndex)
    cy.clickButton(action, true)
})

Cypress.Commands.add('performActionOnSearchedItem', (action, message = null) => {
    cy.tableRowActions(0, action)
    if (message != null) cy.checkSnackbarMessage(message)
    cy.wait(1500)
})

Cypress.Commands.add('rowActionsByValue', (value, action) => {
    cy.contains(tableRowLocator, value).within(() => cy.clickButton(expandActionsLocator, true))
    cy.clickButton(action, true)
})

Cypress.Commands.add('clickTableActionsButton', (rowIndex) => clickTableActionsButton(rowIndex))

Cypress.Commands.add('searchAndCheckResults', (value, uniqueSearchResult = true) => {
    cy.fillInput('search-field', value)
    cy.wait(1500)
    uniqueSearchResult ? cy.get('table tbody tr').should('have.length', 1) : cy.get('table tbody tr').should('have.length.above', 1)
})

Cypress.Commands.add('searchAndCheckPresence', (value, shouldBePresent) => {
    cy.searchFor(value, false)
    shouldBePresent ? cy.tableContains(value) : cy.confirmNoResultsFound(value)
})

Cypress.Commands.add('checkSearchResults', (uniqueSearchResult = true) => {
    uniqueSearchResult ? cy.get('table tbody tr').should('have.length', 1) : cy.get('table tbody tr').should('have.length.above', 1)
})

Cypress.Commands.add('searchFor', (value, delay = true) => {
    delay ? cy.fillInput('search-field', value) : cy.fillInputWithoutDeplay('search-field', value)
    cy.wait(1500)
})

Cypress.Commands.add('searchForInPopUp', (value) => {
    cy.get('.v-overlay__content [data-cy="search-field"]').type(value)
    cy.wait(1500)
})

Cypress.Commands.add('confirmNoResultsFound', () => {
    cy.get('table tbody tr').should('have.text', 'No data available')
})

Cypress.Commands.add('checkStatusAndVersion', (status, version) => {
    cy.checkRowByIndex(0, 'Status', status)
    cy.checkRowByIndex(0, 'Version', version)
})

Cypress.Commands.add('headerContains', (value) => {
    cy.get('button.v-btn--loading').should('not.exist')
    cy.get(tableHeaderLocator).should('contain', value.toString())
})

Cypress.Commands.add('tableContains', (value) => {
    cy.get('table tbody').should('contain', value)
})

Cypress.Commands.add('tableNotContains', (value) => {
    cy.get('table tbody').should('not.contain', value)
})

Cypress.Commands.add('rowContains', (rowIndex, value) => {
    cy.get(tableRowLocator).eq(rowIndex).should('contain', value)
})

Cypress.Commands.add('tableCellContains', (dataTable) => {
    dataTable.hashes().forEach((data) => cy.getValueFromCellsWithIndex(data.row, data.column).should('contain', data.value))
})

Cypress.Commands.add('checkRowValues', (rowKey, dataTable) => {
    cy.contains(tableRowLocator, rowKey).invoke('index').then((rowIndex) => {
        dataTable.hashes().forEach((data) => checkValue(rowIndex, data.column, data.value))
    })
})

Cypress.Commands.add('checkRowValueByColumnName', (rowKey, columnName, expected) => {
    cy.contains(tableRowLocator, rowKey).invoke('index').then((rowIndex) => checkValue(rowIndex, columnName, expected))
})

Cypress.Commands.add('checkRowValueInVisibleTableByColumnIndex', (rowKey, columnIndex, expected) => {
    cy.get('table').filter(':visible').within(() => {
        cy.get('tbody tr').contains(rowKey).invoke('index').then((rowIndex) => {
            cy.get('tbody tr').eq(rowIndex).find('td').eq(columnIndex).should('contain', expected)
        })
    })
})

Cypress.Commands.add('checkRowByIndex', (rowIndex, columnName, expected) => {
    checkValue(rowIndex, columnName, expected)
})

Cypress.Commands.add('checkRowByIndexToNotContain', (rowIndex, columnName, expected) => {
    getCellByName(rowIndex, columnName).should('not.contain', expected)
})

Cypress.Commands.add('checkLastRow', (columnName, expectedValue) => {
    cy.get(tableRowLocator).then((rows) => { 
        getCellByName(rows.length - 1, columnName).should('contain', expectedValue) })
})

Cypress.Commands.add('getRowIndexByText', (text) => {
    cy.contains(tableRowLocator, text).invoke('index').then((index) => {
        return cy.wrap(index)
    })
}) 

Cypress.Commands.add('getValueFromCellsWithIndex', (rowIndex, cellIndex) => {
    cy.get(tableRowLocator).eq(rowIndex).find('td').eq(cellIndex).invoke('text').then((text) => {
        return cy.wrap(text)
    })
})

Cypress.Commands.add('getCellValue', (rowIndex, columnName) => {
    return getCellByName(rowIndex, columnName).invoke('text')
})

Cypress.Commands.add('getCellValueInPopUp', (rowIndex, columnName) => {
    return getCellByName(rowIndex, columnName, true).invoke('text')
})

Cypress.Commands.add('searchAndGetData', (status, columnName) => {
    cy.searchFor(status, false)
    cy.getCellValue(0, 'Version').then(version => objectVersion = parseFloat(version))
    cy.getCellValue(0, columnName).then((name) => {
        cy.searchAndCheckResults(name)
        objectName = name
    })
})

Cypress.Commands.add('searchAndApprove', (name) => {
    cy.searchAndCheckResults(name)
    cy.performActionOnSearchedItem('Approve')
    cy.checkStatusAndVersion('Final', '1.0')
})

Cypress.Commands.add('searchAndConfirmStatusAndVersion', (name, status, version) => {
    cy.searchAndCheckResults(name)
    cy.checkStatusAndVersion(status, version)
})

Cypress.Commands.add('confirmItemNotAvailable', (itemName) => {
    cy.fillInput('search-field', itemName)
    cy.contains(itemName).should('not.exist')
})

Cypress.Commands.add('addTableFilter', (filerName) => {
    cy.waitForTable()
    cy.contains(tableHeaderCellLocator, filerName).find('button').click()
    cy.contains('.v-overlay__content .v-list-item', 'Add to filter').click()
})

function clickTableActionsButton(rowIndex) {
    cy.get(tableRowLocator).filter(':visible').eq(rowIndex).within(() => cy.clickButton('table-item-action-button', true))
}

function getCellByName(rowIndex, columnName, isPopUp = false) {
    let headerCellLocator = isPopUp ? tableHeaderCellLocatorInPopUp : tableHeaderCellLocator
    let rowLocator = isPopUp ? tableRowLocatorInPopUp : tableRowLocator 
    return cy.contains(headerCellLocator, regex(columnName))
            .invoke('index')
            .then((columnIndex) => cy.get(rowLocator).eq(rowIndex).find('td').eq(columnIndex))
}

function checkValue(rowIndex, columnName, expected) {
    if (expected == null) {
        getCellByName(rowIndex, columnName).should('be.empty')
    } else {
        getCellByName(rowIndex, columnName).should('contain', expected)
    }
}
