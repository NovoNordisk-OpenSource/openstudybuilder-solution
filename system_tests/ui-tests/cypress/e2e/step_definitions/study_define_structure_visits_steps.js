const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
import { getCurrStudyUid } from '../../support/helper_functions'

let studyVisits_uid

When('User is presented with correct unscheduled visit name', () => cy.get('[data-cy="visit-name"] input').should('have.value', 'Unscheduled'))

When('User is presented with visit start rule set as {string}', (startRule) => cy.get(`[data-cy="visit-start-rule"] textarea[value="${startRule}"]`).should('be.visible'))

When('User must be able to set vist start rule as {string}', (startRule) => cy.get('.v-overlay [data-cy="visit-start-rule"] [class="v-field__input"]').clear().type(startRule))

When('User waits for the Basic epoch for unscheduled visit to load', () => cy.get('[data-cy="study-period"]').should('contain.text', 'Basic'))

When('User intercepts create visit request', () => cy.intercept('**/study-visits').as('visitRequest'))

Then('The study visit is created', () => cy.wait('@visitRequest').then(request => expect(request.response.statusCode).to.eq(201)))

When('User search for visit with name {string}', (visitName) => cy.searchAndCheckPresence(visitName, true))

When('Epoch {string} is selected for the visit', (epoch) => cy.selectVSelect('study-period', epoch))

When('First available epoch is selected', () => cy.selectFirstVSelect('study-period'))

When('Time unit {string} is selected for the visit', (timeUnit) => selectFromDropdown('time-unit', timeUnit))

When('Visit timing {int} is selected for the visit', (value) => cy.fillInput('visit-timing', value))

Given('The study visits uid array is cleared', () => cy.cleanStudyVisitsUidArray())

When('Anchor visit checkbox is checked', () => cy.get('[data-cy="anchor-visit-checkbox"] input').check())

Given('Add visit button is clicked', () => cy.clickButton('add-visit'))

Given('Visit scheduling type is selected as {string}', (visitType) => cy.get(`[data-cy=${visitType}] input`).check())

When('Visit description is changed to {string}', (value) => cy.fillInput('visit-description', value))

Then('Visit number field is disabled', () => cy.get('[data-cy="visit-number"]').should('have.class', 'v-input--disabled'))

When('Visit Type is selected as {string}', (visitType) => selectFromDropdown('visit-type', visitType))

When('Contact mode is selected as {string}', (contactMode) => selectFromDropdown('contact-mode', contactMode))

When('Time reference is selected as {string}', (timeReference) => selectFromDropdown('time-reference', timeReference))

When('Visit name is set to {string}', (value) => cy.fillInput('visit-name', value))

When('Visit short name is set to {string}', (value) => cy.fillInput('visit-short-name', value))

When('Visit number is set to {string}', (value) => cy.fillInput('visit-number', value))

When('Visit unique number is set to {int}', (value) => cy.fillInput('visit-unique-number', value))

Then('Visits {string} have group displayed as {string} in table', (visits, group) => {
    const visitArray = visits.split(',')
    const visitsIndexes = []
    visitArray.forEach(visit => visitArray.push(visit.trim().replace('V', '') - 1))
    visitsIndexes.forEach(index => cy.checkRowByIndex(index, 'Collapsible visit group', group))
})

Then('The validation appears for missing study period', () => cy.checkIfValidationAppears('study-period'))

Then('The validation appears for missing visit type', () => cy.checkIfValidationAppears('visit-type'))

Then('The validation appears for missing contact mode', () => cy.checkIfValidationAppears('contact-mode'))

Then('The validation appears for missing time reference', () => cy.checkIfValidationAppears('time-reference'))

Then('The validation appears for missing visit timing', () => cy.checkIfValidationAppears('visit-timing'))

Then('Time Reference for anchor visit is disabled for edition', () => {
    cy.get('[data-cy="time-reference"]').should('have.class', 'v-input--disabled')
})

Then('Visit description is displayed in the table as {string}', (value) => cy.checkRowByIndex(0, 'Visit description', value))

Then('The new Anchor Visit is visible within the Study Visits table', () => {
    cy.checkRowByIndex(0, 'Global anchor visit', 'Yes')
    cy.checkRowByIndex(0, 'Visit name', 'Visit 1')
    cy.checkRowByIndex(0, 'Time reference', 'Global anchor visit')
    cy.checkRowByIndex(0, 'Timing', '0 day')
    cy.checkRowByIndex(0, 'Visit number', '1')
    cy.checkRowByIndex(0, 'Visit short name', 'V1')
    cy.checkRowByIndex(0, 'Study duration days', '0 days')
    cy.checkRowByIndex(0, 'Study duration weeks', '0 weeks')
    cy.checkRowByIndex(0, 'Study day', 'Day 1')
    cy.checkRowByIndex(0, 'Study week', 'Week 1')
    cy.checkRowByIndex(0, 'Week in Study', 'Week 0')
})

Then('Study visit class is {string} and the timing is {string}', (visitClass, timing) => {
    cy.checkRowByIndex(0, 'Visit Class', visitClass)
    cy.checkRowByIndex(0, 'Timing', timing)
})

Then('Visits are no longer grouped in table', () => {
    cy.checkRowByIndex(1, 'Collapsible visit group', '')
    cy.checkRowByIndex(2, 'Collapsible visit group', '')
    cy.checkRowByIndex(3, 'Collapsible visit group', '')
})

Then('The Anchor visit checkbox is disabled', () => cy.get('[data-cy="anchor-visit-checkbox"]').should('not.exist'))

Then('The study epoch field is enabled for editing', () => cy.get('[data-cy="study-period"] .v-field--active').should('exist'))

Then('Warning about visit window unit selection is displayed', () => cy.get('.v-alert').should('contain.text', "The  visit window unit   (days/weeks) you choose for the  first visit  will apply to all subsequent visits and  can't  be changed later without  deleting all visits.  This means that if you want to change the unit, you'll need to  remove all the subsequent visits  while keeping the first one, update the unit, and then  set up the remaining visits again."))

When('[API] Study vists uids are fetched for study {string}', (study_uid) => cy.getExistingStudyVisits(study_uid).then(uids => studyVisits_uid = uids))

When('[API] Study vists uids are fetched for selected study', () => cy.getExistingStudyVisits(getCurrStudyUid()).then(uids => studyVisits_uid = uids))

When('[API] Study visits in selected study are cleaned-up', () => deleteVisits(getCurrStudyUid()))

Given('[API] The static visit data is fetched', () => getVisitStaticData())

Given('[API] The dynamic visit data is fetched: contact mode {string}, time reference {string}, type {string}, epoch {string}', (contactMode, timeReference, visitType, epochName) => {
    getVisitDynamicData(contactMode, timeReference, visitType, epochName)
})

Given('[API] Global Anchor visit within epoch {string} exists', (epochName) => cy.createAnchorVisit(getCurrStudyUid(), epochName))

Given('[API] The visit with following attributes is created: isGlobalAnchor {int}, visitWeek {int}', (isGlobalAnchorVisit, visitWeek) => {
    createVisitViaAPI(isGlobalAnchorVisit, visitWeek)
})

Given('[API] The visit with following attributes is created: isGlobalAnchor {int}, visitWeek {int}, minVisitWindow {int}, maxVisitWindow {int}', (isGlobalAnchorVisit, visitWeek, minVisitWindow, maxVisitWindow) => {
    createVisitViaAPI(isGlobalAnchorVisit, visitWeek, minVisitWindow, maxVisitWindow)
})

Given('[API] All visit groups uids are fetched', () => cy.getVisitGroupsUid(getCurrStudyUid()))

Given('[API] All visit groups are removed', () => cy.deleteAllVisitsGroups(getCurrStudyUid()))

Given('[API] Visits group with format {string} is created', (groupFormat) => cy.createVisitsGroup(getCurrStudyUid(), groupFormat))

function getVisitStaticData() {
    cy.getEpochAllocationUid()
    cy.getDayAndWeekTimeUnitUid()
}

function getVisitDynamicData(contactMode, timeReference, visitType, epochName) {
    cy.getContactModeTermUid(contactMode)
    cy.getTimeReferenceUid(timeReference)
    cy.getVisitTypeUid(visitType)
    cy.getEpochUid(getCurrStudyUid(), epochName)
}

function createVisitViaAPI(isGlobalAnchorVisit, visitWeek, minVisitWindow = 0, maxVisitWindowValue = 0) {
    cy.createVisit(getCurrStudyUid(), isGlobalAnchorVisit, visitWeek, minVisitWindow, maxVisitWindowValue)
}

function deleteVisits(study_uid) {
    const studyVisitsSorted_uid = studyVisits_uid.sort().reverse()
    studyVisitsSorted_uid.forEach(visit_uid => cy.deleteVisitByUid(study_uid, visit_uid))
}

function selectFromDropdown(locator, value) {
    cy.get(`.v-form [data-cy="${locator}"]`).click()
    cy.contains('.v-list-item-title', value, {matchCase: true}).click()
}