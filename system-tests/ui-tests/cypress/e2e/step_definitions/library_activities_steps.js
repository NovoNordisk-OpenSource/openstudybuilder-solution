const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

export let activityName
let synonym
let nciconceptid = "NCIID"
let nciconceptname = "NCINAME"
let abbreviation = "ABB"
let definition = "DEF"
let approvalConfirmation = 'Activity is now in Final state'
let inactivationConfirmation = 'Activity inactivated'

When('The Add activity button is clicked', () => cy.clickButton('add-activity'))

When('The Activity group and Activity name fields are not filled with data', () => cy.clickButton('save-button'))

Then('Activity is created and confirmation message is shown', () => saveActivity())

Then('The test activity container is filled with data', () => {
    cy.clickButton('add-activity')
    fillNewActivityData()
})

Then('The user adds another activity with already existing synonym', () => {
    cy.clickButton('add-activity')
    fillNewActivityData(false)
})

Then('The user is not able to save activity with already existing synonym and error message is displayed', () => {
    cy.clickButton('save-button')
    cy.get('div[data-cy="form-body"]').should('be.visible');          
    cy.get('.v-snackbar__content').should('be.visible').should('contain.text', 'Following Activities already have the provided synonyms'); 
})

Then('The newly added activity is added in the table', () => {  
    cy.searchAndCheckResults(activityName)
    cy.checkRowByIndex(0, 'Activity name', activityName)
    cy.checkRowByIndex(0, 'Sentence case name', activityName.toLowerCase())
    cy.checkRowByIndex(0, 'Synonyms', synonym)
    cy.checkRowByIndex(0, 'NCI Concept ID', nciconceptid)
    cy.checkRowByIndex(0, 'NCI Concept Name', nciconceptname)
    cy.checkRowByIndex(0, 'Abbreviation', abbreviation)
    cy.checkRowByIndex(0, 'Data collection', "Yes")
    cy.checkStatusAndVersion('Draft', '0.1')
})

Then('The user is not able to save the acitivity', () => {   
    cy.get('div[data-cy="form-body"]').should('be.visible');          
    cy.get('span.dialog-title').should('be.visible').should('have.text', 'Add activity'); 
})

Then('The message is displayed as {string} in the above mandatory fields', (message) => {
    cy.warningIsDisplayedForField('[data-cy="activityform-activity-group-class"]', message)
    cy.warningIsDisplayedForField('[data-cy="activityform-activity-name-class"]', message)
})

Then('The message is displayed as {string} in the Activity subgroup field', (message) => {   
    cy.warningIsDisplayedForField('[data-cy="activityform-activity-subgroup-class"]', message) 
})

Then('The message is displayed as {string} in the Sentence case name field', (message) => {
    cy.warningIsDisplayedForField('[data-cy="sentence-case-name-class"]', message) 
})

When('Select a value for Activity group field, but not for Activity subgroup field', () => {
    cy.clickButton('add-activity', true)
    cy.selectFirstVSelect('activityform-activity-group-dropdown')
    cy.clickButton('save-button', true)
})

Then('The default value for Data collection must be checked', () => {      
    cy.get('[data-cy="activityform-datacollection-checkbox"]').within(() => {
        cy.get('.mdi-checkbox-marked').should('exist');
    })
})

When('The user enters a value for Activity name', () => {
    cy.fillInput('activityform-activity-name-field', "TEST")
})

Then('The field for Sentence case name will be defaulted to the lower case value of the Activity name', () => {      
    cy.get('[data-cy$="activity-name-field"] input').then(($input) => {
        cy.get('[data-cy="sentence-case-name-field"] input').should('have.value', $input.val().toLowerCase())
    })
})

When('The user define a value for Sentence case name and it is not identical to the value of Activity name', () => {
    cy.fillInput('activityform-activity-name-field', "TEST")
    cy.fillInput('sentence-case-name-field', "TEST2")
    cy.clickButton('save-button', true)
})

When('The activity item container is filled with data', () => fillNewActivityData())

Given('The activity exists with status as Draft', () => createDraftActivityAndConfirmStatus())

Given('The activity exists with status as Final', () => createActivityAndApprove())

Given('The activity exists with status as Retired', () => {      
    createActivityAndApprove()
    cy.performActionOnSearchedItem('Inactivate', inactivationConfirmation)
    cy.checkStatusAndVersion('Retired', '1.0')
})

Given('First activity for search test is created', () => createDraftActivity('SearchTest'))

Given('Second activity for search test is created', () => createDraftActivity('SearchTest'))

Then('The activity has status {string} and version {string}', (status, version) => cy.checkStatusAndVersion(status, version))

When('The activity is edited', () => {
    editActivity()
    cy.clickButton('save-button', true)
    cy.wait(500)
})

When('The activity edition form is filled with data', () => editActivity())

Then('The activity is no longer available', () => cy.confirmItemNotAvailable(activityName))

Then('The activity is not created', () => cy.confirmItemNotAvailable(activityName))

Then('The activity is not edited', () => cy.confirmItemNotAvailable(activityName))

When('I search and select activity', () => {
    cy.intercept('/api/concepts/activities/activities?page_number=1&page_size=0&total_count=true&filters=%7B%7D').as('getData')
    cy.wait('@getData', {timeout: 20000})
    cy.wait(1000)
    cy.searchAndCheckResults(activityName)
    cy.get('table tbody tr td').contains(activityName).click()
})

Then('One activity is found after performing full name search', () => cy.searchAndCheckResults(activityName))

function fillNewActivityData(uniqueSynonym = true, namePrefix = 'Activity') {
    activityName = `${namePrefix}${Date.now()}`
    if (uniqueSynonym) synonym = `Synonym${Date.now()}`
    cy.selectFirstVSelect('activityform-activity-group-dropdown')
    cy.selectFirstVSelect('activityform-activity-subgroup-dropdown')
    cy.fillInput('activityform-activity-name-field', activityName)
    cy.fillInput('activityform-nci-concept-id-field', nciconceptid)
    cy.fillInput('activityform-nci-concept-name-field', nciconceptname)
    cy.fillInputNew('activityform-synonyms-field', synonym)
    cy.fillInput('activityform-abbreviation-field', abbreviation)
    cy.fillInput('activityform-definition-field', definition)
}

function saveActivity() {
    cy.intercept('/api/concepts/activities/activities?page_number=1&page_size=0&total_count=true&filters=%7B%7D').as('getData')
    cy.clickButton('save-button')
    cy.checkSnackbarMessage('Activity created')
    cy.wait('@getData', {timeout: 20000})
    cy.get('.dialog-title').should('not.exist')
}

function createDraftActivity(namePrefix = 'Activity') {
    cy.clickButton('add-activity', true)
    fillNewActivityData(true, namePrefix)
    saveActivity()
}

function createDraftActivityAndConfirmStatus() {
    createDraftActivity()
    cy.searchAndCheckResults(activityName)
    cy.checkStatusAndVersion('Draft', '0.1')
}

function createActivityAndApprove() {
    createDraftActivityAndConfirmStatus()
    cy.performActionOnSearchedItem('Approve', approvalConfirmation)
    cy.checkStatusAndVersion('Final', '1.0')
}

function editActivity() {
    activityName = `Update ${activityName}`
    cy.fillInput('activityform-activity-name-field', activityName)
    cy.contains('.v-label', 'Reason for change').parent().find('[value]').type('Test update')
}
