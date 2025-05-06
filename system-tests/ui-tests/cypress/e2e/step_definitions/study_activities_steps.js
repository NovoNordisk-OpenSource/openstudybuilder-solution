import { apiActivityName } from "./library_activities_steps";
const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let activity_placeholder_name, activity_library, activity_soa_group, activity_group, activity_sub_group, activity_activity

Given('Study activities for Study_000001 are loaded', () => {
    cy.intercept('/api/studies/Study_000001/study-activities?*').as('getData')
    cy.wait('@getData', {timeout: 30000})
})

Given('The activity exists in the library', () => {
    cy.log('Handled by import script')
})

Given('Study Activity is found', () => cy.searchFor(apiActivityName))

When('The Study Activity is added from an existing study by study id', () => {
    createActivity('id', '999-3000')
})

When('The Study Activity is added from an existing study by study acronym', () => {
    createActivity('acronym', 'DummyStudy 0')
})

When('The Study Activity is added from the library', () => {
    activity_soa_group = 'INFORMED CONSENT'
    initiateActivityCreation()
    selectActivityAndGetItsData(activity_soa_group)
    saveActivity()
})

When('User tries to add Activity in Draft status', () => {
    initiateActivityCreation()
    cy.searchForInPopUp(apiActivityName)
    cy.waitForTable()    
})

When('User initiate adding Study Activity from Library', () => {
    initiateActivityCreation()
    addLibraryActivityByName()
    cy.clickFormActionButton('save')
})

When('User adds newly created activity with status Final', () => {
    initiateActivityCreation()
    addLibraryActivityByName()
    saveActivity()
})

Then('The Study Activity created from library is visible within the Study Activities table', () => {  
    checkIfTableContainsActivity()
})

Then('The Study Activity copied from existing study is visible within the Study Activities table', () => {
    checkIfTableContainsActivity()
})

Then('The Activity in Draft status is not found', () => cy.contains('.v-sheet table tbody tr', 'No data available'))

Then('The new Study Activity added from Library is visible in table', () => {  
    cy.searchFor(activity_activity)
    cy.tableContains(activity_activity)
})

When('The Study Activity is added as a placeholder for new activity request', () => {
    activity_placeholder_name = `Placeholder Instance Name ${Date.now()}`
    cy.clickButton('add-study-activity', true)
    cy.get('[data-cy="create-placeholder"]').within(() => cy.get('.v-selection-control__input').click())
    cy.clickFormActionButton('continue')
    cy.contains('.choice .text', 'Create a placeholder activity without submitting for approval').click()
    cy.selectVSelect('flowchart-group', 'INFORMED CONSENT')
    cy.get('[data-cy="activity-group"] input').type('General')
    cy.selectFirstVSelect('activity-group')
    cy.selectFirstVSelect('activity-subgroup')
    cy.fillInput('instance-name', activity_placeholder_name)
    cy.fillInput('activity-rationale', 'Placeholder Test Rationale')
    cy.clickFormActionButton('save')
})

Then('The Study Activity placeholder is visible within the Study Activities table', () => {
    cy.tableContains('Requested')
    cy.tableContains('INFORMED CONSENT')
    cy.tableContains('General')
    cy.tableContains(activity_placeholder_name)
    cy.rowActionsByValue('INFORMED CONSENT', 'Remove Activity')
})

When('Study Activity edition is initiated', () => {
    cy.reload()
    cy.rowActionsByValue('INFORMED CONSENT', 'Edit')
})

When('Study Activity Placeholder edition is initiated', () => cy.rowActionsByValue(activity_placeholder_name, 'Edit'))

Then('The edited Study Activity data is reflected within the Study Activity table', () => {
    cy.tableContains('EFFICACY')
})

When('The Study Activity Placeholder is deleted', () => {
    cy.rowActionsByValue(activity_placeholder_name, 'Remove Activity')
    cy.clickButton('continue-popup')
})

Then('The Study Activity Placeholder is no longer available', () => cy.tableNotContains(activity_placeholder_name))

When('The Study Activity select from study form is opened on second step', () => {
    cy.clickButton('add-study-activity', true)
    cy.get('[data-cy="select-from-studies"]').within(() => {
        cy.get('.v-selection-control__input').click()
    })    
    cy.clickFormActionButton('continue')
})

When('The user tries to go to Activity Selection without study chosen', () => {
    cy.clickFormActionButton('continue')
})

Then('The validation appears and Create Activity form stays on Study Selection', () => {
    cy.elementContain('select-study-for-activity-by-acronym', 'This field is required')
    cy.elementContain('select-study-for-activity-by-id', 'This field is required')
})

When('The Study Activity select from library form is opened on second step', () => {
    cy.clickButton('add-study-activity')
    cy.get('[data-cy="select-from-library"]').within(() => {
        cy.get('.v-selection-control__input').click()
    })    
    cy.clickFormActionButton('continue')
})

When('The user tries to go further without SoA group chosen', () => {
    cy.get('.v-data-table__td--select-row input').not('[aria-disabled="true"]').eq(0).check()
    cy.clickFormActionButton('save')
})

When('The user tries to go further in activity placeholder creation without SoA group chosen', () => {
    cy.fillInput('instance-name', `Placeholder Instance Name ${Date.now()}`)
    cy.fillInput('activity-rationale', 'Placeholder Test Rationale')
    cy.clickFormActionButton('save')
})

Then('The validation appears and Create Activity form stays on SoA group selection', () => {
    cy.get('.v-snackbar__content').should('contain', 'Every selected Activity needs SoA Group')
    cy.get('[data-cy="flowchart-group"]').should('be.visible')
})

Then('The validation appears under empty SoA group selection', () => {
    cy.get('[data-cy="flowchart-group"]').find('.v-messages').should('contain', 'This field is required')
})

When('The Study Activity create placeholder form is opened on second step', () => {
    cy.clickButton('add-study-activity', true)
    cy.get('[data-cy="create-placeholder"]').within(() => cy.get('.v-selection-control__input').click())
    cy.clickFormActionButton('continue')
    cy.contains('.choice .text', 'Create a placeholder activity without submitting for approval').click()
})

Then('The SoA group can be changed', () => {
    cy.wait(1000)
    cy.selectAutoComplete('flowchart-group', 'EFFICACY')
    cy.get('.v-card-actions button').contains('Save').click( {force: true} )
})

Then('Warning that {string} {string} can not be added to the study is displayed', (status, item) => {
    cy.get('.v-snackbar__content').should('contain', `has status ${status}. Only Final ${item} can be added to a study.`)
})

function getActivityData(rowIndex, getSoAGroupValue) {
    cy.getCellValueInPopUp(rowIndex, 'Library').then((text) => activity_library = text)
    if (getSoAGroupValue) cy.getCellValueInPopUp(rowIndex, 'SoA group').then((text) => activity_soa_group = text)
    cy.getCellValueInPopUp(rowIndex, 'Activity group').then((text) => activity_group = text)
    cy.getCellValueInPopUp(rowIndex, 'Activity subgroup').then((text) => activity_sub_group = text)
    cy.getCellValueInPopUp(rowIndex, 'Activity').then((text) => activity_activity = text.slice(0, 50))
}

function checkIfTableContainsActivity() {
    cy.wait(1000)
    cy.tableContains(activity_library)
    cy.tableContains(activity_soa_group)
    cy.tableContains(activity_group)
    cy.tableContains(activity_sub_group)
    cy.tableContains(activity_activity)
}

function createActivity(activityBy, value) {
    initiateActivityCreation(activityBy, value)
    selectActivityAndGetItsData()
    saveActivity()
}

function addLibraryActivityByName() {
    activity_activity = apiActivityName
    cy.searchForInPopUp(activity_activity)
    cy.waitForTable()
    cy.get('[data-cy="select-activity"] input').check()
    cy.selectVSelect('flowchart-group', 'INFORMED CONSENT')
}

function initiateActivityCreation(activityBy = null, activityValue = null) {
    let radioButtonLocator = activityBy ? 'studies' : 'library'
    cy.waitForTable()
    cy.clickButton('add-study-activity')
    cy.get(`[data-cy="select-from-${radioButtonLocator}"] input`).check( {force: true} )
    if (activityBy) cy.selectVSelect(`select-study-for-activity-by-${activityBy}`, activityValue)
    cy.clickFormActionButton('continue')
}

function selectActivityAndGetItsData(activity_soa_group = null) {
    cy.get('.v-data-table__td--select-row input').each((el, index) => {
        if (el.is(':enabled')) {
            cy.wrap(el).check()
            if(activity_soa_group) {
                cy.get('[data-cy="flowchart-group"]').eq(index).click()
                cy.contains('.v-overlay .v-list-item-title', activity_soa_group).click({force: true})
            }
            getActivityData(index, !activity_soa_group)
            return false
        }
    })
}

function saveActivity() {
    cy.clickFormActionButton('save')
    cy.get('.v-snackbar__content').should('contain', 'Study activity added')
    cy.waitForTable()
}
