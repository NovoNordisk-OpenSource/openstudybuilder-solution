const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let activitygroup, apiActivityGroupName
let abbreviation = "ABB", definition = "DEF"

When('The group can be find in table', () => cy.searchAndCheckPresence(apiActivityGroupName, true))

When('The add activity group button is clicked', () => cy.clickButton('add-activity'))

When('The activity group container is filled with data and saved', () => {
    fillGroupData(false)
    saveGroup()
})

When('The test activity group container is filled with data', () => fillGroupData())

Then('The newly added activity group is visible in the the table', () => {
    cy.searchAndCheckResults(activitygroup)
    cy.checkRowByIndex(0, 'Activity group', activitygroup)
    cy.checkRowByIndex(0,'Sentence case name', activitygroup.toLowerCase())
    cy.checkRowByIndex(0, 'Abbreviation', abbreviation)
    cy.checkRowByIndex(0, 'Definition', definition)
    cy.checkStatusAndVersion('Draft', '0.1')
})

When('The Group name and Sentence case name and Definition fields are not filled with data', () => {
    cy.fillInput('groupform-activity-group-field', 'Test')
    cy.clearInput('groupform-activity-group-field')
    cy.clearInput('sentence-case-name-field')
    cy.clickButton('save-button')
})

Then('The user is not able to save the acitivity group', () => {   
    cy.get('div[data-cy="form-body"]').should('be.visible');          
    cy.get('span.dialog-title').should('be.visible').should('have.text', 'Add activity group'); 
})

Then('The message is displayed as {string} in the mandatory fields', (message) => {   
    cy.get('[data-cy="groupform-activity-group-field"]').contains('.v-messages__message', message).should('be.visible'); 
    cy.get('[data-cy="sentence-case-name-field"]').contains('.v-messages__message', message).should('be.visible');
    cy.get('[data-cy="groupform-definition-field"]').contains('.v-messages__message', message).should('be.visible');
})

When('The user enters a value for Activity group name', () => cy.fillInput('groupform-activity-group-field', "TEST"))

Then('The field for Sentence case name will be defaulted to the lower case value of the Activity group name', () => {      
    cy.get('[data-cy="sentence-case-name-field"] input').should('have.value', 'test')
})

When('The user define a value for Sentence case name and it is not identical to the value of Activity group name', () => {
    cy.fillInput('groupform-activity-group-field', "TEST")
    cy.fillInput('sentence-case-name-field', "TEST2")
    cy.clickButton('save-button')
})

When('The activity group is edited', () => {
    editGroup()
    saveGroup('updated')
})

When('The activity group edition form is filled with data', () => editGroup())

Then('The activity group is no longer available', () => cy.confirmItemNotAvailable(apiActivityGroupName))

Then('The activity group is not created', () => cy.confirmItemNotAvailable(activitygroup))

Then('The activity group is not edited', () => cy.confirmItemNotAvailable(activitygroup))

Then('One activity group is found after performing full name search', () => cy.searchAndCheckResults(apiActivityGroupName))

When('[API] Activity group in status Draft exists', () => createGroupViaApi())

When('[API] Activity group is approved', () => cy.approveGroup())

When('[API] Activity group is inactivated', () => cy.inactivateGroup())

When('[API] Activity group is reactivated', () => cy.reactivateGroup())

When('[API] Activity group gets new version', () => cy.groupNewVersion())

Given('[API] First activity group for search test is created', () => createGroupViaApi(`SearchTest${Date.now()}`))

Given('[API] Second activity group for search test is created', () => cy.createGroup(`SearchTest${Date.now()}`))

When('Activity group is found', () => cy.searchFor(apiActivityGroupName))

function fillGroupData(clickAddButton = true) {
    activitygroup = `Group${Date.now()}`
    if (clickAddButton) cy.clickButton('add-activity')
    cy.fillInput('groupform-activity-group-field', activitygroup)
    cy.fillInput('groupform-abbreviation-field', abbreviation)
    cy.fillInput('groupform-definition-field', definition)
}

function saveGroup(action = 'created') {
    cy.intercept('/api/concepts/activities/activity-groups?page_number=1&*').as('getData')
    cy.clickButton('save-button')
    cy.get('.v-snackbar__content').contains(`Group ${action}`).should('be.visible');
    cy.wait('@getData', {timeout: 20000})
    cy.searchFor(activitygroup)
}

function editGroup() {
    activitygroup = `${activitygroup}Edited`
    cy.fillInput('groupform-activity-group-field', activitygroup)
    cy.fillInput('groupform-change-description-field', "e2e test")
}

function createGroupViaApi(customName = '') {
    cy.createGroup(customName)
    cy.getGroupNameByUid().then(name => apiActivityGroupName = name)
}