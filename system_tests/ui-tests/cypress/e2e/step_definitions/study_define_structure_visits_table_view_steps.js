const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");


When('The user defines a visit in the table view with following data:', (dataTable) => defineVisit(dataTable.rowsHash()))

When('The user edits the visit {string} in table view with following data:', (visitName, dataTable) => {
    cy.intercept('**preview').as('previewIntercept')
    editVisit(visitName, dataTable.rowsHash())
    cy.wait('@previewIntercept')
})

When('The user intercepts study visit {string} request', (requestType) => {
    if (requestType === 'create') {
        cy.intercept({ method: 'POST', url: '**study-visits**', times: 1 }).as('createStudyVisit')
    } else if (requestType === 'edit') {
        cy.intercept({ method: 'PATCH', url: '**/study-visits/**', times: 1 }).as('patchStudyVisits')
    }
})

When('The {string} visit is saved', (actionType) => {
    if (actionType === 'created') {
        cy.clickButton('save-visit-changes')
        cy.wait('@createStudyVisit', { timeout: 10000 })
    } else if (actionType === 'edited') {
        cy.clickButton('save-visit-changes')
        cy.wait('@patchStudyVisits', { timeout: 10000 })
    }
})

Then('The visit {string} is visible in the Study Visits table view:', (visitName, dataTable) => {
    checkVisitRow(visitName, dataTable.rowsHash())
})

function checkVisitRow(visitName, expected) {
    const exactName = new RegExp(`^\\s*${Cypress._.escapeRegExp(visitName)}\\s*$`)

    cy.get('table tbody')
        .filter(':visible')
        .contains('td a', exactName)
        .closest('tr')
        .invoke('index')
        .then((rowIndex) => {
            Object.entries(expected).forEach(([columnName, value]) => {
                cy.checkRowByIndex(rowIndex, columnName, value)
            })
        })
}

const visitFieldActions = {
    visitClass: selectActions('visit-class'),
    visitName: inputActions('visit-name'),
    visitShortName: inputActions('visit-short-name'),
    visitType: selectActions('visit-type'),
    contactMode: selectActions('contact-mode'),
    timing: inputActions('timing'),
    uniqueVisitNumber: inputActions('visit-unique-number'),
    epoch: selectActions('study-period'),
    startRule: inputActions('visit-start-rule'),
    endRule: inputActions('visit-end-rule'),
    epochAllocationRule: selectActions('epoch-allocation-rule'),
    description: inputActions('visit-description'),
    timeReference: selectActions('time-reference'),
    timeUnit: selectActions('time-unit'),
}

function inputActions(dataCy) {
    return {
        set: (value, rowSelector) => inVisitRow(rowSelector, () => cy.fillInput(dataCy, value)),
        clear: (rowSelector) => inVisitRow(rowSelector, () => cy.clearInputField(dataCy)),
    }
}

function selectActions(dataCy) {
    return {
        set: (value, rowSelector) => cy.selectAutoComplete(dataCy, value, rowSelector),
        clear: (rowSelector) => inVisitRow(rowSelector, () => cy.clearDropdown(dataCy)),
    }
}

function inVisitRow(rowSelector, action) {
    rowSelector ? cy.get(rowSelector).within(action) : action()
}

function defineVisit(visitData = {}) {
    cy.wait(200)
    cy.clickButton('edit-study-visits')
    cy.wait(200)
    cy.clickButton('add-visit')
    fillVisit(visitData)
}

function editVisit(visitName, visitData) {
    const findVisitRow = ($rows) => $rows.filter((_, row) => {
        const $row = Cypress.$(row)
        const $headers = $row.closest('table').find('thead th')
        const nameIndex = $headers.toArray().findIndex(header => header.textContent.trim() === 'Visit name')
        expect(nameIndex, 'Visit name column index').to.be.at.least(0)
        const $nameCell = $row.children('td').eq(nameIndex)
        const $nameInput = $nameCell.find('[data-cy="visit-name"] input')

        return $nameInput.length ? $nameInput.val() === visitName : $nameCell.text().trim() === visitName
    })

    cy.get('table tbody tr')
        .should(($rows) => {
            expect(findVisitRow($rows), `Visit "${visitName}"`).to.have.length(1)
        })
        .then(($rows) => {
            const $row = findVisitRow($rows)
            const rowSelector = `table tbody tr:nth-child(${$row.index() + 1})`

            fillVisit(visitData, rowSelector)
        })
}

function fillVisit(visitData, rowSelector) {
    Object.entries(visitData).forEach(([key, value]) => {
        value ? visitFieldActions[key].set(value, rowSelector) : visitFieldActions[key].clear()
    })
}
