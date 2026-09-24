import { activityName } from "./library_concepts_activities_activities_steps";
import { activity_uid, subgroup_uid, group_uid, requestedActivity_uid } from "../../support/api_requests/library_activities";
import { getCurrStudyUid } from "../../support/helper_functions";
const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

const setPlaceholderName = (name) => cy.fillInput('instance-name', name)

export let activity_activity, current_activity_uid, study_activity_uid, exchangedActivities = []
let apiGroupName, apiSubgroupName, apiActivityName
let rowIndex, activity_soa_group, activity_group, activity_sub_group, old_placeholder_name

When('User gets full activity name starting with {string}', (name) => cy.contains('table tbody td', name).invoke('text').then(text => activity_activity = text))

Then('Activity, Group And Subgroup created via API names are fetch to be used in Study Activities tests', () => {
    cy.getGroupNameByUid().then(name => apiGroupName = name)
    cy.getSubGroupNameByUid().then(name => apiSubgroupName = name)
    cy.getActivityNameByUid().then(name => apiActivityName = name)
})

Then('The Study Activity is available in the first row of the table', () => cy.checkRowByIndex(0, 'Activity', apiActivityName))

Then('The Study Activity Subgroup is displayed as {string} in the table', (value) => cy.checkRowByIndex(0, 'Activity subgroup', value))

Then('The Study Activity Group is displayed as {string} in the table', (value) => cy.checkRowByIndex(0, 'Activity group', value))

Then('The Study Activity SoA Group is displayed as {string} in the table', (value) => cy.checkRowByIndex(0, 'SoA group', value))

Then('The Study Activity Data Collection is displayed as {string} in the table', (value) => cy.checkRowByIndex(0, 'Data collection', value))

Then('The Study Activity Library is displayed as {string} in the table', (value) => cy.checkRowByIndex(0, 'Library', value))

Then('The Study Activity is searched for', () => cy.searchFor(activity_activity))

Then('The Study Activity with name {string} is searched for', (name) => cy.searchForInPopUp(name))

Then('The Study Activity creation search field is cleared', () => cy.clearSearchInPopUp())

Then('The Study Activity is searched by name and is found', () => cy.searchAndCheckPresence(apiActivityName, true))

Then('The Study Activity is searched by lowercased name', () => cy.searchFor(apiActivityName.toLowerCase()))

Then('The Study Activity is searched by partial name and is found', () => cy.searchAndCheckPresence(apiActivityName.slice(0, 3), true))

Then('The Study Activity is searched by group and is found', () => cy.searchAndCheckPresence(apiGroupName, true))

Then('The Study Activity is searched by subgroup and is found', () => cy.searchAndCheckPresence(apiSubgroupName, true))

When('User sets Activity Placeholder name with {string}', (name) => setPlaceholderName(`${name}_${getShortUniqueId()}`))

When('User sets Activity Placeholder name', () => setPlaceholderName(activity_activity = `Placeholder_${getShortUniqueId()}`))

When('User sets Activity Placeholder name that is already used', () => setPlaceholderName(activity_activity))

When('User updates Activity Placeholder name', () => {
    old_placeholder_name = activity_activity
    setPlaceholderName(activity_activity = `Edit name ${getShortUniqueId()}`)
})

When('User sets Activity rationale', () => cy.fillInput('activity-rationale', 'Activity Test Rationale'))

When('User selects Activity SoA group as {string}', (soaGroup) => cy.selectVSelect('flowchart-group', soaGroup))

When('User edits Activity SoA group to {string}', (soaGroup) => cy.selectAutoComplete('flowchart-group', soaGroup))

When('User selects first group for placeholder', () => cy.selectFirstVSelect('activity-group'))

When('User selects second group for placeholder', () => cy.selectSecondVSelect('activity-group'))

When('User selects first subgroup for placeholder', () => cy.selectFirstVSelect('activity-subgroup'))

When('User selects second subgroup for placeholder', () => cy.selectSecondVSelect('activity-subgroup'))

When('User gets selected activity group name', () => cy.get('[data-cy="activity-group"] .v-autocomplete__selection-text').invoke('text').then(val => activity_group = val))

When('User gets selected activity subgroup name', () => cy.get('[data-cy="activity-subgroup"] .v-autocomplete__selection-text').invoke('text').then(val => activity_sub_group = val))

When('User intercepts available studies request', () => cy.intercept('/api/studies/list?has_study_activity=true').as('availableStudies'))

When('User intercepts all available studies request', () => cy.intercept('/api/studies/list?minimal_response=false').as('availableStudies'))

When('User waits for available studies request', () => cy.wait('@availableStudies'))

When('Name of Activity from Library for exchaning placeholder is saved', () => cy.getActivityNameByUid().then(name => exchangedActivities.push(name)))

When('Study activity add button is clicked', () => cy.clickButton('add-study-activity'))

Then('The Study Activity is found', () => cy.searchAndCheckPresence(activity_activity, true))

Then('The Study Activity is not found', () => cy.searchAndCheckPresence(activity_activity, false))

When('Old The Study Activity is found', () => cy.searchAndCheckPresence(old_placeholder_name, true))

Then('The Old study Activity Placeholder is not available', () => cy.searchAndCheckPresence(old_placeholder_name, false))

When('{int} Activity that exchanged the placeholder is found in Study Activities table', (index) => cy.searchAndCheckPresence(exchangedActivities[index -1], true))

When('Activity placeholder is searched for', () => cy.searchForInPopUp(activity_activity))

When('{int} Activity for exchanging the placeholder is searched in filters', (index) => cy.get('.border-b').filter(':visible').within(() => { cy.get('input').clear().type(exchangedActivities[index - 1])}))

When('{int} Activity is found and click in the filters', (index) => cy.contains('.v-overlay .v-list-item', exchangedActivities[index - 1]).find('input').check())

When('{int} Activity for exchanging the placeholder is searched for', (index) => {
    cy.get('[data-cy="form-body" ] [data-cy="search-field"] input').clear().type(exchangedActivities[index - 1])
})

When('User clears list of exchanged activities', () => exchangedActivities = [])

When('The {int} activity is disabled for selection', (index) => cy.contains('.v-overlay table tbody tr', exchangedActivities[index - 1]).find('input[type=checkbox]').should('be.disabled'))

Given('Study activities for selected study are loaded', () => {
    cy.intercept(`/api/studies/${getCurrStudyUid()}/study-activities?*`).as('getData')
    cy.wait('@getData', { timeout: 30000 })
})

When('User searches for activity created via API', () => cy.searchForInPopUp(activityName))

When('Data of selected activity is saved', () => getSelectedActivityData())

When('SoA group assigned to the selected activity is saved', () => cy.getCellValueInPopUp(rowIndex, 'SoA group').then((text) => activity_soa_group = text))

When('User selects SoA group as {string} for selected activity', (soaGroup) => selectSoAGroup(rowIndex, soaGroup))

Then('The Study Activity name, group and subgroup are visible in table', () => {
    cy.checkRowByIndex(0, 'Activity subgroup', activity_sub_group)
    cy.checkRowByIndex(0, 'Activity group', activity_group)
    cy.checkRowByIndex(0, 'Activity', activity_activity)
})

Then('The Study Activity SoA group is visible in the table', () => cy.checkRowByIndex(0, 'SoA group', activity_soa_group))

Then('The Activity in Draft status is not found', () => cy.contains('.v-sheet table tbody tr', 'No data available'))

When('User selects option to create placeholder without submitting', () => cy.contains('.choice .text', 'Create a placeholder activity without submitting for approval').click())

When('User selects option to create placeholder with submitting', () => cy.contains('.choice .text', 'Request and submit for approval').click())

When('The activity request approval form is filled with definition', () => {
    cy.get('[data-cy="sponsorform-definition-field"] textarea').not('[readonly]').type('Test')
})

When('Data collection flag is unchecked', () => cy.get('input[aria-label="Data collection"]').uncheck())

When('Data collection flag is checked', () => cy.get('input[aria-label="Data collection"]').check())

When('Activity from studies is selected', () => cy.get('[data-cy="select-from-studies"] input').check())

When('Activity from library is selected', () => cy.get('[data-cy="select-from-library"] input').check({ force: true }))

When('Activity from placeholder is selected', () => cy.get('[data-cy="create-placeholder"] input').check())

Then('The validation appears and Create Activity form stays on Study Selection', () => {
    cy.contains('.v-overlay .v-window-item .v-input', 'Study ID / Acronym').should('contain.text', 'This field is required')
})

When('User selects first activity available for selection', () => {
    cy.get('.v-data-table__td--select-row input').each((el, index) => {
        if (el.is(':enabled')) {
            cy.wrap(el).check()
            rowIndex = index
            return false
        }
    })
})

Then('The validation appears and Create Activity form stays on SoA group selection', () => {
    cy.get('.v-alert').should('contain', 'Every selected Activity needs SoA Group')
    cy.get('[data-cy="flowchart-group"]').should('be.visible')
})

Then('The validation appears under empty SoA group selection', () => {
    cy.get('[data-cy="flowchart-group"]').find('.v-messages').should('contain', 'This field is required')
})

Then('The activity group is edited to {string}', (value) => selectFromDropdownInEditForm('Activity group', value))

Then('The activity subgroup is edited to {string}', (value) => selectFromDropdownInEditForm('Activity subgroup', value))

Then('Warning that {string} {string} can not be added to the study is displayed', (status, item) => {
    cy.get('.v-alert').should('contain', `has status ${status}. Only Final ${item} can be added to a study.`)
})

When('The first matching activity is selected', () => cy.get('[data-cy="select-activity"] input').eq(0).check())

When('Activity row containing {string} is selected', (value) => cy.contains('.v-overlay table tbody tr', value).find('[data-cy="select-activity"] input').check())

When('SoA group {string} is selected for activity row containing {string}', (soaGroup, value) => cy.contains('.v-overlay table tbody tr', value).invoke('index').then(index => selectSoAGroup(index, soaGroup)))

When('The user is presented with the changes to request', () => {
    cy.get('[data-cy="form-body"]').should('contain', activity_activity)
})

When('The user accepts the changes', () => cy.contains('button', 'Accept').click())

When('The user declines the changes', () => cy.contains('button', 'Decline').click())

When('The user opens bulk review changes window', () => cy.contains('Review activity updates').click())

When('The user filters the table by red alert status', () => cy.get('[value="updated"]').click())

When('The user filters the table by yellow alert status', () => cy.get('[value="reviewed"]').click())

Then('The activities with red alert are present', () => {
    cy.get('tbody tr').each(row => cy.wrap(row).find('.mdi-alert-circle-outline').should('exist'))
})

Then('The activities with yellow alert are present', () => {
    cy.get('tbody tr').each(row => cy.wrap(row).find('.mdi-alert-outline').should('exist'))
})

Then('The icon indicates which activity group is present in detailed soa', () => {
    cy.getGroupNameByUid(group_uid).then(name => cy.contains('[data-cy="form-body"] td', name).find('.mdi-eye-outline').should('exist'))
})

Then('The icon indicates which activity subgroup is present in detailed soa', () => {
    cy.getSubGroupNameByUid(subgroup_uid).then(name => cy.contains('[data-cy="form-body"] td', name).find('.mdi-eye-outline').should('exist'))
})

Then('The icon indicates which activity name is present in detailed soa', () => {
    cy.contains('[data-cy="form-body"] td', activity_activity).find('.mdi-eye-outline').should('exist')
})

When('User selects {int} activity from Library to exchange placeholder with', (index) => cy.get('.v-data-table__td--select-row input').eq(index - 1).check())

When('User sets SoA Group as {string} for first matching activity', (soaGroup) => selectSoAGroup(0, soaGroup))

When('User selects study {string}', (value) => {
    cy.contains('.v-overlay .v-window-item .v-input', 'Study ID / Acronym').click()
    cy.get('.v-overlay .v-list-item').should('not.contain', 'No data available')
    cy.contains('.v-overlay .v-window-item .v-input', 'Study ID / Acronym').type(value)
    cy.contains('.v-overlay .v-list-item', value).click()
})

When('Pop-up displays that there is already existing placeholder with such name, group and subgroup', () => {
    cy.contains('.v-overlay .v-card .v-card-text', `An activity named '${activity_activity}'`).should('be.visible')
    cy.contains('.v-overlay .v-card .v-card-text', `already exists in the library. Do you want to reuse it?`).should('be.visible')
})

When('The activity {string} is displayed as changed with new {string} value from {string} to {string}', (name, columnName, oldValue, newValue) => {
    validateReviewUpdatesOverview(`Activity ${columnName}`, name, oldValue, newValue)
})

When('The action {string} is clicked for activity {string}', (action, name) => {
    cy.contains('.v-overlay table tbody tr', name).contains('button', action).click()
})

Then('[API] Activity is assigned to the visit {int} in selected study', (visitIndex) => cy.assignActivityToVisit(getCurrStudyUid(), study_activity_uid, visitIndex))

Then('[API] All Activities are deleted from selected study', () => {
    cy.getExistingStudyActivities(getCurrStudyUid()).then((uids) => uids.forEach((uid) => cy.deleteActivityFromStudy(getCurrStudyUid(), uid)))
})

Then('[API] Get SoA Group {string} id', (name) => cy.getSoaGroupUid(name))

Then('[API] Activity is added to the selected study', () => addActivityToStudyAndGetValues(getCurrStudyUid()))

Then('[API] Create Unsubmitted Requested Activity', () => createAndApprovePlaceholderViaApi(false))

Then('[API] Create Submitted Requested Activity', () => createAndApprovePlaceholderViaApi(true))

Then('[API] Requested Activity is added to the study', () => cy.addActivityToStudy(getCurrStudyUid(), requestedActivity_uid, group_uid, subgroup_uid))

Then('[API] Activity is updated', () => cy.updateActivity(activity_activity))

Then('[API] Activity is updated with new name', () => cy.updateActivity(activity_activity = `New Activity name ${getShortUniqueId()}`))

function validateReviewUpdatesOverview(columnName, name, oldValue, newValue) {
    cy.contains('.v-overlay table thead th', columnName).invoke('index').then(index => {
        cy.contains('.v-overlay table tbody tr', name).find('td').eq(index).then(el => {
            const locator = columnName == 'status' ? '.text-red' : 'text-green' 
            cy.wrap(el).should('contain.text', oldValue).parentsUntil('.crossed-out').should('be.visible')
            cy.wrap(el).should('contain.text', newValue).parentsUntil(locator).should('be.visible')
        })
    })
}

function getSelectedActivityData() {
    cy.getCellValueInPopUp(rowIndex, 'Activity group').then((text) => activity_group = text)
    cy.getCellValueInPopUp(rowIndex, 'Activity subgroup').then((text) => activity_sub_group = text)
    cy.getCellValueInPopUp(rowIndex, 'Activity').then((text) => activity_activity = text.slice(0, 50))
}

function selectSoAGroup(rowIndex, soaGroup) {
    cy.get('[data-cy="flowchart-group"]').eq(rowIndex).click()
    cy.contains('.v-overlay .v-list-item', soaGroup).click({ force: true })
    cy.get('.v-overlay .dialog-title').click()
}

function selectFromDropdownInEditForm(inputName, value) {
    cy.contains('.v-overlay .v-input', inputName).clear()
    cy.contains('.v-overlay .v-input', inputName).type(value)
    cy.contains('.v-overlay .v-list-item', value).click({ force: true })
}

function addActivityToStudyAndGetValues(studyUid) {
    cy.addActivityToStudy(studyUid, activity_uid, group_uid, subgroup_uid).then((response) => {
        activity_activity = response.body[0].content.activity.name
        current_activity_uid = response.body[0].content.activity.uid
        study_activity_uid = response.body[0].content.study_activity_uid
    })
}

function createAndApprovePlaceholderViaApi(submitted) {
    let sufix = submitted ? 'Submitted' : 'Unsubmitted'
    cy.getFinalGroupUid()
    cy.getFinalSubGroupUid()
    cy.createRequestedActivity(submitted, activity_activity = `Placeholder_${sufix}_${getShortUniqueId()}`)
    cy.approveRequestedActivity()
}