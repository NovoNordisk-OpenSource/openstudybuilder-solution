const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const popUpRowLocator = '.v-sheet table tbody tr'

let activity_placeholder_name, activity_library, activity_soa_group, activity_group, activity_sub_group, activity_activity
let foundActivities

Given('The activity exists in the library', () => {
    cy.log('Handled by import script')
})

When('The Study Activity is added from an existing study by study id', () => {
    createActivity('id', '999-3000')
})

When('The Study Activity is added from an existing study by study acronym', () => {
    createActivity('acronym', 'DummyStudy 0')
})
When('The Study Activity is added from the library', () => {
    activity_soa_group = 'INFORMED CONSENT'
    cy.clickButton('add-study-activity', true)
    cy.get('[data-cy="select-from-library"]').within(() => cy.get('.v-selection-control__input').click())
    cy.clickFormActionButton('continue')
    cy.get('.v-data-table__td--select-row input').each((el, index) => {
        if (el.is(':enabled')) {
            cy.wrap(el).check()
            cy.get('[data-cy="flowchart-group"]').eq(index).click()
            cy.contains('.v-overlay .v-list-item-title', activity_soa_group).click({force: true})
            cy.get(popUpRowLocator).eq(index).find('td').eq(1).invoke('text').then((text) => activity_library = text)
            cy.get(popUpRowLocator).eq(index).find('td').eq(3).invoke('text').then((text) => activity_group = text)
            cy.get(popUpRowLocator).eq(index).find('td').eq(4).invoke('text').then((text) => activity_sub_group = text)
            cy.get(popUpRowLocator).eq(index).find('td').eq(5).invoke('text').then((text) => activity_activity = text)
            return false
        }
    })
    saveActivity()
})

Then('The Study Activity created from library is visible within the Study Activities table', () => {  
    checkIfTableContainsActivity()
})

Then('The Study Activity copied from existing study is visible within the Study Activities table', () => {
    checkIfTableContainsActivity()
})

When('The Study Activity is added as a placeholder for new activity request', () => {
    activity_placeholder_name = `Placeholder Instance Name ${Date.now()}`
    cy.clickButton('add-study-activity', true)
    cy.get('[data-cy="create-placeholder"]').within(() => cy.get('.v-selection-control__input').click())
    cy.clickFormActionButton('continue')
    cy.contains('.choice .text', 'Create a placeholder activity without submitting for approval').click()
    cy.selectVSelect('flowchart-group', 'INFORMED CONSENT')
    cy.selectVSelect('activity-group', 'General')
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

When('The Study Activity is deleted', () => {
    cy.searchAndCheckResults(activity_activity, false)
    cy.get('table tbody tr').its('length').then(len => foundActivities = len)
    cy.tableRowActions(0, 'Remove Activity')
    cy.clickButton('continue-popup')
})

When('The Study Activity Placeholder is deleted', () => {
    cy.rowActionsByValue(activity_placeholder_name, 'Remove Activity')
    cy.clickButton('continue-popup')
})

Then('The Study Activity is no longer available', () => {
    foundActivities == 1 ? cy.tableContains('No data available') : cy.get('table tbody tr').should('have.length', foundActivities - 1)
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

function getValuesFromRow(rowIndex) {
    cy.get(popUpRowLocator).eq(rowIndex).find('td').eq(2).invoke('text').then((text) => activity_library = text)
    cy.get(popUpRowLocator).eq(rowIndex).find('td').eq(3).invoke('text').then((text) => activity_soa_group = text)
    cy.get(popUpRowLocator).eq(rowIndex).find('td').eq(4).invoke('text').then((text) => activity_group = text)
    cy.get(popUpRowLocator).eq(rowIndex).find('td').eq(5).invoke('text').then((text) => activity_sub_group = text)
    cy.get(popUpRowLocator).eq(rowIndex).find('td').eq(6).invoke('text').then((text) => activity_activity = text.slice(0, 30))
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
    cy.waitForTable()
    cy.clickButton('add-study-activity', true)
    cy.get('[data-cy="select-from-studies"]').within(() => cy.get('.v-selection-control__input').click())
    cy.selectVSelect(`select-study-for-activity-by-${activityBy}`, value)
    cy.clickFormActionButton('continue')
    cy.get('.v-data-table__td--select-row input').each((el, index) => {
        if (el.is(':enabled')) {
            cy.wrap(el).check()
            getValuesFromRow(index)
            return false
        }
    })
    saveActivity()
}

function saveActivity() {
    cy.clickFormActionButton('save')
    cy.get('.v-snackbar__content').should('contain', 'Study activity added')
    cy.waitForTable()
}
