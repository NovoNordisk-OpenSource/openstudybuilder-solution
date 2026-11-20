const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The study visits timeline view shows no visits defined for the current study with a message {string}', (message) => {
    cy.get('.empty-state').should('contain.text', message)
})

Then('The create study visit button is visible', () => {
    cy.get('[data-cy=add-visit-empty-state]').should('be.visible')
})

When('The user defines a visit in the timeline view with following data:', (dataTable) => defineVisit(dataTable.rowsHash()))

When('The user edits visit {string} in the timeline view with following data:', (visitName, dataTable) => editVisit(visitName, dataTable.rowsHash()))

When('The user selects visit {string} in the timeline view', (visitShortName) => {
    cy.contains('[data-cy="visit-box"]', visitShortName)
        .should('be.visible')
        .click()
})

Then('The visit {string} is visible in the Study Visits timeline view:', (visitShortName, dataTable) => {
    const fields = {
        epoch: { row: '.epoch-row', content: '.epoch-name' },
        visitType: { row: '.type-row', content: '.type-name' },
        studyDay: { label: 'Study Day' },
        studyWeek: { label: 'Study Week' },
        visitWindow: { label: 'Visit window' },
    }

    const expected = dataTable.rowsHash()

    cy.get('[data-cy="visit-box"]').should(($visits) => {
        const $visit = $visits.filter((_, element) =>
            element.textContent.trim() === visitShortName
        )

        expect($visit, `Visit "${visitShortName}"`).to.have.length(1)

        const $visitCell = $visit.closest('td.visit-cell')
        const $tbody = $visitCell.closest('tbody')
        const columnIndex = $visitCell
            .parent()
            .children('td.visit-cell')
            .index($visitCell)

        Object.entries(expected).forEach(([field, value]) => {
            const config = fields[field]

            const $row = config.row
                ? $tbody.children(config.row)
                : $tbody.children('tr.value-row').filter((_, row) =>
                    Cypress.$(row).children('th.row-label').text().trim() === config.label
                )

            expect($row, `${field} row`).to.have.length(1)

            const $cell = getTimelineCell($row, columnIndex)
            const $content = config.content
                ? $cell.find(config.content)
                : $cell

            expect($content, `${field} content`).to.have.length(1)
            expect($content.text().trim(), field).to.equal(value)
        })
    })
})

Then('The visit {string} is not visible in the Study Visits timeline view', (visitShortName) => {
    cy.get('body').should(($body) => {
        const $visit = $body.find('[data-cy="visit-box"]').filter((_, element) =>
            element.textContent.trim() === visitShortName
        )

        expect($visit, `Visit "${visitShortName}"`).to.have.length(0)
    })
})

function getTimelineCell($row, columnIndex) {
    const $cells = $row.children('th, td').not('.row-label')
    let columnStart = 0

    for (let index = 0; index < $cells.length; index++) {
        const $cell = $cells.eq(index)
        const columnEnd = columnStart + Number($cell.attr('colspan') || 1)

        if (columnIndex >= columnStart && columnIndex < columnEnd) {
            return $cell
        }

        columnStart = columnEnd
    }

}

const setVisitClass = (value) => {
    const buttons = {
        'Manually defined visit': 'manually-defined-visit-switch',
        'Global anchor visit': 'global-anchor-visit-switch',
        'Anchor visit in visit group': 'anchor-visit-in-group-switch',
        'Repeating visit': 'repeating-visit-switch',
    }

    const button = buttons[value]

    setSwitch(button, true)
}

function setSwitch(dataCy, value) {
    const actions = { true: 'check', false: 'uncheck' }
    const enabled = value === true || value === 'true'
    const selector = `[data-cy="${dataCy}"] input[type="checkbox"]`

    cy.get(selector)[actions[value]]()

    cy.get(selector).should(enabled ? 'be.checked' : 'not.be.checked')
    cy.wait(500)
}

const visitFieldActions = {
    visitClass: { set: (value) => setVisitClass(value) },
    visitType: autoCompleteActions('visit-type'),
    isTechnicalVisit: { set: (value) => setSwitch('technical-visit-switch', value) },
    contactMode: autoCompleteActions('contact-mode'),

    visitGroup: autoCompleteActions('visit-group'),
    timeReference: autoCompleteActions('time-reference'),
    timing: inputActions('visit-timing'),
    timeUnit: {
        ...autoCompleteActions('time-unit'),
        set: (value) => {
            cy.selectAutoComplete('time-unit', value)
            cy.wait(1000)
        },
    },
    expectedTiming: inputActions('expected-timing'),
    visitSuffix: inputActions('visit-suffix'),
    studyDay: inputActions('study-day'),
    studyWeek: inputActions('study-week'),

    visitName: inputActions('visit-name'),
    visitShortName: inputActions('visit-short-name'),
    uniqueVisitNumber: inputActions('visit-unique-number'),

    visitWindowMin: inputActions('visit-window-min'),
    visitWindowMax: inputActions('visit-window-max'),
    visitWindowUnit: autoCompleteActions('visit-window-unit'),

    startRule: inputActions('visit-start-rule'),
    endRule: inputActions('visit-end-rule'),
    epoch: autoCompleteActions('study-period'),
    epochAllocationRule: autoCompleteActions('epoch-allocation-rule'),
    description: inputActions('visit-description'),
    showVisitInProtocol: { set: (value) => setSwitch('show-visit-switch', value) },
    soaMilestone: { set: (value) => setSwitch('soa-milestone-switch', value) },
    repeatingFrequency: autoCompleteActions('repeating-frequency'),
}

function inputActions(dataCy) {
    return {
        set: (value) => cy.fillInput(dataCy, value),
        clear: () => cy.clearInputField(dataCy),
    }
}

function autoCompleteActions(dataCy) {
    return {
        set: (value) => cy.selectAutoComplete(dataCy, value),
        clear: () => cy.clearDropdown(dataCy),
    }
}

function defineVisit(visitData = {}) {
    cy.wait(1000)
    cy.clickButton('add-visit-timeline')
    cy.clickButton('toggle-visit-details')

    fillVisit(visitData)
}

function editVisit(visitName, visitData = {}) {
    const exactName = new RegExp(`^\\s*${Cypress._.escapeRegExp(visitName)}\\s*$`)

    cy.contains('[data-cy="visit-box"]', exactName)
        .should('be.visible')
        .click()

    cy.clickButton('toggle-visit-details')

    fillVisit(visitData)
}

function fillVisit(visitData, rowSelector) {
    Object.entries(visitData).forEach(([key, value]) => {
        value ? visitFieldActions[key].set(value, rowSelector) : visitFieldActions[key].clear()
    })
}
