const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let activitysubgroup
let abbreviation = "ABB", definition = "DEF"

When('The Add activity subgroup button is clicked', () => cy.clickButton('add-activity'))

When('The test activity subgroup container is filled with data and saved', () => createSubGroupAndSave(false))

When('The test activity subgroup container is filled with data', () => fillSubGroupData())

Then('The newly added activity subgroup is visible in the the table', () => {  
    cy.searchAndCheckResults(activitysubgroup)
    cy.checkRowByIndex(0, 'Activity subgroup', activitysubgroup)
    cy.checkRowByIndex(0,'Sentence case name', activitysubgroup.toLowerCase())
    cy.checkRowByIndex(0, 'Abbreviation', abbreviation)
    cy.checkRowByIndex(0, 'Definition', definition)
    cy.checkStatusAndVersion('Draft', '0.1')
})

When('The Activity groups, Subgroup name, Sentence case name and Definition fields are not filled with data', () => {
    cy.fillInput('groupform-activity-group-field', 'test')
    cy.clearInput('sentence-case-name-field')
    cy.clearInput('groupform-activity-group-field')
    cy.clickButton('save-button')
})

Then('The user is not able to save the acitivity subgroup', () => {   
    cy.get('div[data-cy="form-body"]').should('be.visible');          
    cy.get('span.dialog-title').should('be.visible').should('have.text', 'Add activity subgroup'); 
})

Then('The message is displayed as {string} in each of the mandatory field', (message) => {  
    cy.get('[data-cy="groupform-subgroup-class"]').contains('.v-messages__message', message).should('be.visible'); 
    cy.get('[data-cy="groupform-activity-group-class"]').contains('.v-messages__message', message).should('be.visible'); 
    cy.get('[data-cy="sentence-case-name-class"]').contains('.v-messages__message', message).should('be.visible');
    cy.get('[data-cy="groupform-definition-class"]').contains('.v-messages__message', message).should('be.visible');
})

When('The user enters a value for Activity subgroup name', () => {
    cy.fillInput('groupform-activity-group-field', "TEST")
})

Then('The field for Sentence case name will be defaulted to the lower case value of the Activity subgroup name', () => {      
    cy.get('[data-cy="sentence-case-name-field"] input').should('have.value', 'test')
})

When('The user define a value for Sentence case name and it is not identical to the value of Activity subgroup name', () => {
    cy.fillInput('groupform-activity-group-field', "TEST")
    cy.fillInput('sentence-case-name-field', "TEST2")
    cy.clickButton('save-button')
})

Given('The activity subgroup exists with status as Draft', () => {
    createSubGroupAndSave()
    cy.searchAndConfirmStatusAndVersion(activitysubgroup, 'Draft', '0.1')
})

Given('The activity subgroup exists with status as Final', () => {
    createSubGroupAndSave()
    cy.searchAndApprove(activitysubgroup)
})

Given('The activity subgroup exists with status as Retired', () => {      
    createSubGroupAndSave()
    cy.searchAndApprove(activitysubgroup)
    cy.performActionOnSearchedItem("Inactivate")
    cy.checkStatusAndVersion('Retired', '1.0')
})

Given('First activity subgroup for search test is created', () => createSubGroupAndSave(true, 'SearchTest'))

Given('Second activity subgroup for search test is created', () => createSubGroupAndSave(true, 'SearchTest'))

Then('The activity subgroup has status {string} and version {string}', (status, version) => {
    cy.searchAndConfirmStatusAndVersion(activitysubgroup, status, version)
})

When('The activity subgroup is edited', () => {
    editSubGroup()
    saveSubGroup('updated')
})

When('The activity subgroup edition form is filled with data', () => editSubGroup())

Then('The activity subgroup is no longer available', () => cy.confirmItemNotAvailable(activitysubgroup))

Then('The activity subgroup is not created', () => cy.confirmItemNotAvailable(activitysubgroup))

Then('The activity subgroup is not edited', () => cy.confirmItemNotAvailable(activitysubgroup))

Then('One activity subgroup is found after performing full name search', () => cy.searchAndCheckResults(activitysubgroup))

function fillSubGroupData(clickAddButton = true, namePrefix = 'Subgroup') {
    activitysubgroup = `${namePrefix}${Date.now()}`
    if (clickAddButton) cy.clickButton('add-activity')
    cy.selectFirstVSelect('groupform-activity-group-dropdown')
    cy.fillInput('groupform-activity-group-field', activitysubgroup)
    cy.fillInput('groupform-abbreviation-field', abbreviation)
    cy.fillInput('groupform-definition-field', definition) 
}

function createSubGroupAndSave(clickAddButton = true, namePrefix = 'Subgroup') {
    fillSubGroupData(clickAddButton, namePrefix)
    saveSubGroup()
}

function editSubGroup() {
    activitysubgroup = `${activitysubgroup}Edited`
    cy.fillInput('groupform-activity-group-field', activitysubgroup)
    cy.fillInput('groupform-change-description-field', "e2e test")
}

function saveSubGroup(action = 'created') {
    cy.intercept('/api/concepts/activities/activity-sub-groups?page_number=1&*').as('getData')
    cy.clickButton('save-button')
    cy.get('.v-snackbar__content').contains(`Subgroup ${action}`).should('be.visible')
    cy.wait('@getData', {timeout: 20000}) 
}
