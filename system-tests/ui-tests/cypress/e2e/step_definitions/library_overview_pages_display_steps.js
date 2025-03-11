const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let activityName 
let activityInstance 
let activitygroup 
let activitysubgroup 
let nciconceptid = "NCI-ID"
let nciconceptname = "NCINAME"
let topiccode = "Totic-code"
let definition = "DEF"
let abbreviation = "ABB"
let adamcode = "Adam-code"
let approvalConfirmation = 'Activity is now in Final state'

Given('A test group has been created', () => createGroupAndApprove())

Given('A test subgroup has been created and linked to the test group', () => createSubGroupAndApprove())

Given('A test activity has been created and linked to the test group', () => createActivityAndApprove())

Given('A test activity instance has been created and linked to the test activity', () => createInstanceAndApprove())

When('I search for the test activity through the filter field', () => {
    cy.searchAndCheckResults(activityName)
})

When('I search for the test instance through the filter field', () => {
    cy.searchAndCheckResults(activityInstance)
})

Then('The test group, test subgroup and test activity should be displayed in the row of the test instance', () => {
    cy.checkRowByIndex(0, 'Activity group', activitygroup)
    cy.checkRowByIndex(0, 'Activity subgroup', activitysubgroup)  
    cy.checkRowByIndex(0, 'Activity', activityName) 
})

When('I search for the test group through the filter field', () => {
    cy.searchAndCheckResults(activitygroup)
})

When('I search for the test subgroup through the filter field', () => {
    cy.searchAndCheckResults(activitysubgroup)
})

Then('The test group should be displayed in the row for the test subgroup', () => {
    cy.checkRowByIndex(0, 'Activity group', activitygroup)
})

When('I click on the link for the test group in the activity page', () => {
    cy.get('table tbody tr td').contains(activitygroup).click()
})

Then('The test group overview page should be opened', () => {
    verifyOverviewPage(activitygroup)
})

When('I click on the link for the test subgroup in the activity page', () => {
    cy.visit("/library/activities/activities")
    cy.searchAndCheckResults(activityName)
    cy.get('table tbody tr td').contains(activitysubgroup).click()
})

Then('The test subgroup overview page should be opened', () => {
    verifyOverviewPage(activitysubgroup)
})

When('I click on the test activity name in the activity page', () => {
    cy.visit("/library/activities/activities")
    cy.searchAndCheckResults(activityName)
    cy.get('table tbody tr td').contains(activityName).click()
})

Then('The test activity overview page should be opened', () => {
    verifyOverviewPage(activityName)
})

Then('The test group, test subgroup and test instance should be displayed on the test activity overview page', () => {
    cy.get('.v-table__wrapper').contains(activitygroup)
    cy.get('.v-table__wrapper').contains(activitysubgroup)
    cy.get('.v-table__wrapper').contains(activityInstance)
})

Then('The group overview page can be opened by clicking the group link in the activity overview page', () => {
    cy.get('.v-table__wrapper').contains('a', activitygroup).click();
    verifyOverviewPage(activitygroup)   
    cy.go(-1); // Go back to the previous page
})

Then('The subgroup overview page can be opened by clicking the subgroup link in the activity overview page', () => {
    cy.get('.v-table__wrapper').contains('a', activitysubgroup).click();
    verifyOverviewPage(activitysubgroup) 
})

When('I search for the test instance in the instance page through the filter field', () => {
    cy.visit("/library/activities/activity-instances")
    cy.searchAndCheckResults(activityInstance)
})

Then('The test group, the test subgroup and the test activity should be displayed in the row for the test instance', () => {
    cy.checkRowByIndex(0, 'Activity group', activitygroup)
    cy.checkRowByIndex(0, 'Activity subgroup', activitysubgroup) 
    cy.checkRowByIndex(0, 'Activity', activityName)  
})

When('I click on the link for the test group in the instance page', () => {
    cy.visit("/library/activities/activity-instances")
    cy.searchAndCheckResults(activityInstance)
    cy.get('table tbody tr td').contains(activitygroup).click()
})

When('I click on the link for the test subgroup in the instance page', () => {
    cy.visit("/library/activities/activity-instances")
    cy.searchAndCheckResults(activityInstance)
    cy.get('table tbody tr td').contains(activitysubgroup).click()
})

When('I click on the link for the test instance name in the instance page', () => {
    cy.visit("/library/activities/activity-instances")
    cy.searchAndCheckResults(activityInstance)
    cy.get('table tbody tr td').contains(activityInstance).click()
})

Then('The test instance overview page should be opened', () => {
    verifyOverviewPage(activityInstance)
})

Then('The test group, test subgroup and test activity should be displayed on the test instance overview page', () => {
    cy.get('.v-table__wrapper').contains(activitygroup)
    cy.get('.v-table__wrapper').contains(activitysubgroup)
    cy.get('.v-table__wrapper').contains(activityName)
})

Then('The group overview page can be opened by clicking the group link in the instance overview page', () => {
    cy.get('.v-table__wrapper').contains('a', activitygroup).click();
    verifyOverviewPage(activitygroup)   
    cy.go(-1); // Go back to the previous page
    
})

Then('The subgroup overview page can be opened by clicking the subgroup link in the instance overview page', () => {
    cy.get('.v-table__wrapper').contains('a', activitysubgroup).click();
    verifyOverviewPage(activitysubgroup) 
    cy.go(-1); // Go back to the previous page
})

Then('The activity overview page can be opened by clicking the activity link in the instance overview page', () => {
    cy.get('.v-table__wrapper').contains('a', activityName).click();
    verifyOverviewPage(activityName) 
})

When('I click on the link for the test group in the group page', () => {
    cy.get('table tbody tr td').contains(activitygroup).click()
})

Then('The test subgroup should be displayed on the group overview page', () => {
    cy.get('.v-table__wrapper').contains(activitysubgroup)
})

Then('The subgroup overview page can be opened by clicking the subgroup link in the group overview page', () => {
    cy.get('.v-table__wrapper').contains('a', activitysubgroup).click();
    verifyOverviewPage(activitysubgroup) 
})

When('I click on the link for the test group in the subgroup page', () => {
    cy.get('table tbody tr td').contains(activitygroup).click()
})

When('I click on the link for the test subgroup in the subgroup page', () => {
    cy.visit("/library/activities/activity-subgroups")
    cy.searchAndCheckResults(activitysubgroup)
    cy.get('table tbody tr td').contains(activitysubgroup).click()
})

Then('The test group and test activity should be displayed on the subgroup overview page', () => {
    cy.get('.v-table__wrapper').contains(activitygroup)
    cy.get('.v-table__wrapper').contains(activityName)
})

function createGroupAndApprove() {
    cy.visit("/library/activities/activity-groups")
    activitygroup = Date.now()
    cy.clickButton('add-activity')
    cy.fillInput('groupform-activity-group-field', activitygroup)
    cy.fillInput('groupform-abbreviation-field', abbreviation)
    cy.fillInput('groupform-definition-field', definition)
    cy.clickButton('save-button')
    cy.searchAndApprove(activitygroup)
}

function createSubGroupAndApprove() {
    cy.visit("/library/activities/activity-subgroups")
    activitysubgroup = Date.now()
    cy.clickButton('add-activity')
    cy.selectAutoComplete('groupform-activity-group-dropdown', activitygroup)
    cy.fillInput('groupform-activity-group-field', activitysubgroup)
    cy.fillInput('groupform-abbreviation-field', abbreviation)
    cy.fillInput('groupform-definition-field', definition) 
    cy.clickButton('save-button')
    cy.searchAndApprove(activitysubgroup)
}

function createActivityAndApprove() {
    cy.visit("/library/activities/activities")
    cy.clickButton('add-activity', true)
    fillNewActivityData()
    saveActivity()
    cy.searchAndCheckResults(activityName)
    cy.checkStatusAndVersion('Draft', '0.1')
    cy.performActionOnSearchedItem('Approve', approvalConfirmation)
}

function createInstanceAndApprove() {
    cy.visit("/library/activities/activity-instances")
    activityInstance = Date.now()
    cy.clickButton('add-activity', true)
    cy.wait(1000)
    fillInstanceActivityGroupData(activityName)
    fillInstanceClassData()
    cy.fillInput('instanceform-instancename-field', activityInstance)
    cy.fillInput('instanceform-definition-field', definition)
    cy.fillInput('instanceform-nciconceptid-field', nciconceptid)
    cy.fillInput('instanceform-topiccode-field', topiccode)
    cy.fillInput('instanceform-adamcode-field', adamcode)
    cy.get('[data-cy="instanceform-requiredforactivity-checkbox"] input').check()
    cy.clickFormActionButton('save')
}

function fillNewActivityData() {
    activityName = Date.now()
    cy.selectAutoComplete('activityform-activity-group-dropdown', activitygroup)
    cy.selectAutoComplete('activityform-activity-subgroup-dropdown', activitysubgroup)
    cy.fillInput('activityform-activity-name-field', activityName)
    cy.fillInput('activityform-nci-concept-id-field', nciconceptid)
    cy.fillInput('activityform-nci-concept-name-field', nciconceptname)
    //cy.fillInputNew('activityform-synonyms-field', synonym)
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

function fillInstanceActivityGroupData() {
    cy.get('[data-cy=instanceform-activity-dropdown] input').type(activityName)
    cy.contains('.v-list-item', activityName).click()
    cy.get('[data-cy=instanceform-activitygroup-table]').within(() => cy.get('.v-checkbox-btn').first().click())
    cy.clickFormActionButton('continue')
}

function fillInstanceClassData() {
    cy.selectFirstVSelect('instanceform-instanceclass-dropdown')
    cy.clickFormActionButton('continue')
}

function verifyOverviewPage(pageName){
    cy.get('button[role="tab"][value="html"]').contains('Overview');
    cy.get('.v-row').contains(pageName);
}

