const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId, getCurrStudyUid } = require("../../support/helper_functions");

let epochDescription

When('User intercepts epochs codelists request', () => cy.intercept({
     method: 'GET',
     pathname: '/api/ct/codelists/terms',
     query: { codelist_submission_value: 'EPCHALLC' },
 }).as('epochsCodelists'))
 
When('User waits for epochs codelists request', () => cy.wait('@epochsCodelists'))

When('User intercepts epochs data', () => cy.intercept(`**/study-epochs**`).as('epochsRequests'))

When('User waits for epochs data', () => cy.wait('@epochsRequests'))

When('Study Epoch is found', () => cy.searchAndCheckPresence(epochDescription, true))

When('The study epoch with subtype {string} is found', (subtype) => cy.searchAndCheckPresence(subtype, true))

When('Study Epoch is not available', () => cy.searchAndCheckPresence(epochDescription, false))

When('User click create epoch button', () => cy.clickButton('create-epoch'))

When('User sets epoch {string} as {string}', (locator, value) => cy.selectAutoComplete(`epoch-${locator}`, value))

When('User sets epoch {string} rule as {string}', (locator, value) => cy.fillInput(`epoch-${locator}-rule`, value))

When('User sets epoch lag time {string} as {string}', (field, value) => cy.fillInput(field, value))

When('User sets epoch lag time {string} as {string} with unit {string}', (field, value, unit) => {
    cy.fillInput(field, value)
    cy.selectAutoComplete(`${field}-unit`, unit)
})

When('User clears epoch lag time {string}', (field) => cy.get(`[data-cy="${field}"] input`).clear())

When('User attempts to continue to next step of study structure stepper', () => cy.get('button[data-cy="continue-stepper"]').click())

Given('User intercepts study epochs request', () => cy.intercept('GET', '**/study-epochs*').as('epochsRequests'))

When('User sets epoch description', (locator, value) => cy.fillInput('description', epochDescription = `Epoch ${getShortUniqueId()}`))

When('User updates epoch description', (locator, value) => cy.fillInput('description', epochDescription = `Edited epoch ${getShortUniqueId()}`))

Then('The added Epoch name, type {string} and subtype {string} is visible in the table', (type, subtype) => {
    cy.checkRowByIndex(0, 'Epoch name', subtype)
    cy.checkRowByIndex(0, 'Epoch type', type)
    cy.checkRowByIndex(0, 'Epoch subtype', subtype)
})

Then('The Epoch name start rule {string} and end rule {string} are visible in the table', (startRule, endRule) => {
    cy.checkRowByIndex(0, 'Start rule', startRule)
    cy.checkRowByIndex(0, 'End rule', endRule)
})

Then('The Epoch description is visible in the table', (startRule, endRule) => cy.checkRowByIndex(0, 'Description', epochDescription))

Then('The study epoch lag-time fields are not visible', () => {
    ['ae_lag_time', 'hypo_lag_time', 'ce_lag_time'].forEach((field) => cy.get(`[data-cy="${field}"]`).should('not.exist'))
})

Then('The study epoch lag-time columns are not visible', () => {
    ['Adverse event lag time', 'Hypoglycaemic event lag time', 'Clinical event lag time'].forEach((header) => cy.get('table thead').should('not.contain', header))
})

Then('The study epoch lag-time columns are visible', () => {
    ['Adverse event lag time', 'Hypoglycaemic event lag time', 'Clinical event lag time'].forEach((header) => cy.headerContains(header))
})

Then('User can select only plural lag-time units', () => {
    cy.get('[data-cy="ae_lag_time-unit"] .v-field__input').click()
    cy.get('.v-overlay__content .v-list').filter(':visible').find('.v-list-item-title').then((items) => {
        const options = [...items].map((item) => item.textContent.trim())
        expect(options).to.include.members(['days', 'weeks'])
        expect(options).not.to.include.members(['day', 'week', 'year', 'years'])
    })
    cy.get('[data-cy="form-body"]').click({ force: true })
})

Then('The study epochs request includes lag-time data', () => {
    cy.wait('@epochsRequests').then(({ request, response }) => {
        expect(response.body.items[0]).to.include.keys('ae_lag_time', 'hypo_lag_time', 'ce_lag_time')
    })
})

Then('The study epochs request does not include lag-time data', () => {
    cy.wait('@epochsRequests').then(({ request }) => {
        expect(request.query.with_lag_time).to.be.undefined
    })
})

Then('The study epoch lag time {string} is {string} in row {int}', (field, value, row) => {
    const headers = {
        ae_lag_time: 'Adverse event lag time',
        hypo_lag_time: 'Hypoglycaemic event lag time',
        ce_lag_time: 'Clinical event lag time',
    }
    cy.checkRowByIndex(row, headers[field], value)
})

Then('The study epoch lag time {string} is empty in row {int}', (field, row) => {
    const headers = {
        ae_lag_time: 'Adverse event lag time',
        hypo_lag_time: 'Hypoglycaemic event lag time',
        ce_lag_time: 'Clinical event lag time',
    }
    cy.checkRowByIndex(row, headers[field], null)
})

Then('The validation message {string} is displayed for {string}', (message, field) => cy.get(`[data-cy="${field}"]`).should('contain', message))

Then('The snackbar message {string} is displayed', (message) => cy.checkSnackbarMessage(message))

Then('The epoch type is disabled', () => cy.checkIfInputDisabled('epoch-type'))

Then('The epoch subtype is disabled', () => cy.checkIfInputDisabled('epoch-subtype'))

Given('[API] The epoch with type {string} and subtype {string} exists in selected study', (type, subtype) => {
    createEpochViaAPI(type, subtype)
})

Given('[API] All epochs assigned to the selected study are fetched', () => cy.getEpochsUids(getCurrStudyUid()))

Given('[API] All epochs assigned to the selected study are deleted', () => cy.deleteEpochs(getCurrStudyUid()))

Given('[API] An epoch with lag-time values exists in the selected study', () => {
    epochDescription = `Lag time epoch ${getShortUniqueId()}`
    cy.createEpochWithLagTimes(getCurrStudyUid(), epochDescription).then((response) => {
        epochDescription = response.body.description
        expect(response.body.ae_lag_time).to.eq(5)
        expect(response.body.hypo_lag_time).to.eq(2)
        expect(response.body.ce_lag_time).to.eq(7)
    })
})

function createEpochViaAPI(epochType, epochSubType) {
    cy.getEpochTypeAndSubType(epochType, epochSubType)
    cy.createEpoch(getCurrStudyUid())
}
