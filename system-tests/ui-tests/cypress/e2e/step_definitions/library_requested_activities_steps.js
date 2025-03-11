const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let activityName 
let rationaleforrequest = "RFR", abbreviation = "ABB", definition = "DEF"

When('The Add activity request button is clicked', () => cy.clickButton('add-activity'))

When('The activity request container is filled with data and saved', () => addActivity())

When('The activity request form is filled with data', () => addActivity(false))

When('The requested activity edition form is filled with data', () => editActivity(false))

Then('The newly added activity request is visible in the the table', () => {  
    cy.searchAndCheckResults(activityName)
    cy.checkRowByIndex(0, 'Activity', activityName)
    cy.checkRowByIndex(0, 'Sentence case name', activityName.toLowerCase())
    cy.checkRowByIndex(0, 'Abbreviation', abbreviation)
    cy.checkRowByIndex(0, 'Definition', definition)
    cy.checkRowByIndex(0, 'Rationale for activity request', rationaleforrequest)
    cy.checkStatusAndVersion('Draft', '0.1')
})

When('The Activity group, Activity name, Sentence case name and Rationale for activity request fields are not filled with data', () => {
    cy.clickButton('save-button')
})

Then('The user is not able to save the acitivity request', () => {   
    cy.get('div[data-cy="form-body"]').should('be.visible');          
    cy.get('span.dialog-title').should('be.visible').should('contain', 'Add activity request'); 
})

Then('The message is displayed as {string} in mandatory fields', (message) => {
    checkVisibilityOfWarningMessage('[data-cy="requestedform-activity-group-class"]', message)
    checkVisibilityOfWarningMessage('[data-cy="requestedform-activity-name-class"]', message) 
    checkVisibilityOfWarningMessage('[data-cy="requestedform-rationale-for-request-class"]', message)
})

Then('The message is not displayed as {string} in optional fields', (message) => {
    checkVisibilityOfWarningMessage('[data-cy="sentence-case-name-field"]', message, false)
    checkVisibilityOfWarningMessage('[data-cy="requestedform-abbreviation-field"]', message, false) 
    checkVisibilityOfWarningMessage('[data-cy="requestedform-definition-field', message, false)
})

Then('The message is displayed as {string} in empty Sentance case name field', (message) => {
    checkVisibilityOfWarningMessage('[data-cy="sentence-case-name-field"]', message)
})

When('Input a value for Activity group field, but not for Activity subgroup field', () => {
    cy.clickButton('add-activity')
    cy.selectFirstVSelect('requestedform-activity-group-dropdown')
    cy.clickButton('save-button')
})

Then('The message is displayed as {string} in the subgroup field', (message) => {
    checkVisibilityOfWarningMessage('[data-cy="requestedform-activity-subgroup-class"]', message)
})

When('The user input a value for Activity name {string}', (name) => cy.fillInput('requestedform-activity-name-field', name))

When('The user clear default value from Sentance case name', () => cy.clearInput('sentence-case-name-field'))

When('The value for Sentence case name independent of case is not identical to the value of Activity name', () => {
    cy.fillInput('requestedform-activity-name-field', "TEST")
    cy.fillInput('sentence-case-name-field', "TEST2")
    cy.clickButton('save-button')
})

Given('The test activity request exists with a status as Draft', () => createDraftActivity())

Given('The test activity request exists with a status as Final', () => createActivityAndApprove())

Given('The test activity request exists with a status as Retired', () => {      
    createActivityAndApprove()
    cy.performActionOnSearchedItem('Inactivate')
    cy.checkStatusAndVersion('Retired', '1.0')
})

Given('First activity request for search test is created', () => addActivity(true, 'SearchTest'))

Given('Second activity request for search test is created', () => addActivity(true, 'SearchTest'))

Then('The requested activity has status {string} and version {string}', (status, version) => cy.checkStatusAndVersion(status, version))

When('The activity request is edited', () => editActivity())

Then('The requested activity is no longer available', () => cy.confirmItemNotAvailable(activityName))

Then('The requested activity is not created', () => {
    cy.waitForTable()
    cy.confirmItemNotAvailable(activityName)
})

Then('The requested activity is not edited', () => {
    cy.searchAndCheckResults(activityName)
    cy.performActionOnSearchedItem('Edit')
    cy.get('[data-cy="requestedform-rationale-for-request-field"] textarea').should('have.value', rationaleforrequest)
})

Then('One activity request is found after performing full name search', () => cy.searchAndCheckResults(activityName))

function addActivity(save = true, namePrefix ='Requested') {
    activityName = `${namePrefix}${Date.now()}`
    cy.clickButton('add-activity')
    cy.selectFirstVSelect('requestedform-activity-group-dropdown')
    cy.selectFirstVSelect('requestedform-activity-subgroup-dropdown')
    cy.fillInput('requestedform-activity-name-field', activityName)
    cy.fillInput('requestedform-abbreviation-field', abbreviation)
    cy.fillInput('requestedform-definition-field', definition)
    cy.fillInput('requestedform-rationale-for-request-field', rationaleforrequest)
    if (save) {
        cy.intercept('/api/concepts/activities/activities?page_number=1&page_size=0&*').as('getData')
        cy.clickButton('save-button')
        cy.checkSnackbarMessage('Activity created')
        cy.wait('@getData', {timeout: 20000})
    }
}

function createDraftActivity() {
    addActivity()
    cy.searchAndCheckResults(activityName)
    cy.checkStatusAndVersion('Draft', '0.1')
}

function createActivityAndApprove() {
    createDraftActivity()
    cy.performActionOnSearchedItem('Approve')
    cy.checkStatusAndVersion('Final', '1.0')
}

function editActivity(save = true) {
    cy.fillInput('requestedform-rationale-for-request-field', `Update ${rationaleforrequest}`)
    cy.fillInput('requestedform-change-description-field', "e2e test")
    if (save) cy.clickButton('save-button')
}

function checkVisibilityOfWarningMessage(fieldLocator, message, shouldBeVisible = true) {
    let condition = shouldBeVisible ? 'be.visible' : 'not.exist'
    cy.get(fieldLocator).contains('.v-messages__message', message).should(condition); 
}