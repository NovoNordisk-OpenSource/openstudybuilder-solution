import { apiActivityName, apiGroupName, apiSubgroupName, apiInstanceName } from "./api_library_steps";
const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

const clickOnLinkInTable = (name) => cy.get('table tbody tr td').contains(name).click()
const verifyThatValuesPresent = (values) => values.forEach(value => cy.get('.v-table__wrapper').contains(value))

When('I search for the test activity through the filter field', () => cy.searchAndCheckPresence(apiActivityName, true))

When('I search for the test instance through the filter field', () => cy.searchAndCheckPresence(apiInstanceName, true))

When('I search for the test group through the filter field', () => cy.searchAndCheckPresence(apiGroupName, true))

When('I search for the test subgroup through the filter field', () => cy.searchAndCheckPresence(apiSubgroupName, true))

Then('The test group, test subgroup and test activity should be displayed in the row of the test instance', () => {
    cy.checkRowByIndex(0, 'Activity group', apiGroupName)
    cy.checkRowByIndex(0, 'Activity subgroup', apiSubgroupName)  
    cy.checkRowByIndex(0, 'Activity', apiActivityName) 
})

Then('The test group should be displayed in the row for the test subgroup', () => {
    cy.checkRowByIndex(0, 'Activity group', apiGroupName)
})

When('I click on the link for the test group in table', () => clickOnLinkInTable(apiGroupName))

Then('The test group overview page should be opened', () => verifyOverviewPage(apiGroupName))

Then('The test subgroup overview page should be opened', () => verifyOverviewPage(apiSubgroupName))

Then('The test activity overview page should be opened', () => verifyOverviewPage(apiActivityName))

Then('The test instance overview page should be opened', () => verifyOverviewPage(apiInstanceName))

When('I click on the link for the test subgroup in the activity page', () => goToPageSearchAndClickLink('activities', apiActivityName, apiSubgroupName))

When('I click on the test activity name in the activity page', () => goToPageSearchAndClickLink('activities', apiActivityName, apiActivityName))

When('I click on the link for the test subgroup in the instance page', () => goToPageSearchAndClickLink('activity-instances', apiInstanceName, apiSubgroupName))

When('I click on the link for the test instance name in the instance page', () => goToPageSearchAndClickLink('activity-instances', apiInstanceName, apiInstanceName))

When('I click on the link for the test subgroup in the subgroup page', () => goToPageSearchAndClickLink('activity-subgroups', apiSubgroupName, apiSubgroupName))

Then('The test group, test subgroup and test instance should be displayed on the test activity overview page', () => {
    verifyThatValuesPresent([apiGroupName, apiSubgroupName, apiInstanceName])
})

Then('The test group and test activity should be displayed on the subgroup overview page', () => {
    verifyThatValuesPresent([apiGroupName, apiActivityName])
})

Then('The test group, test subgroup and test activity should be displayed on the test instance overview page', () => {
    verifyThatValuesPresent([apiGroupName, apiSubgroupName, apiActivityName])
})

Then('The test subgroup should be displayed on the group overview page', () => verifyThatValuesPresent([apiSubgroupName]))

Then('The group overview page can be opened by clicking the group link in overview page', () => openLinkedItemAndGoBack(apiGroupName))

Then('The subgroup overview page can be opened by clicking the subgroup link in overview page', () => openLinkedItemAndGoBack(apiSubgroupName))

Then('The activity overview page can be opened by clicking the activity link in overview page', () => openLinkedItemAndGoBack(apiActivityName))

Then('The test group, the test subgroup and the test activity should be displayed in the row for the test instance', () => {
    cy.checkRowByIndex(0, 'Activity group', apiGroupName)
    cy.checkRowByIndex(0, 'Activity subgroup', apiSubgroupName) 
    cy.checkRowByIndex(0, 'Activity', apiActivityName)  
})

Then('The activity instance overview page can be opened by clicking the activity instance link in the instance overview page', () => {
    cy.get('.v-table__wrapper').contains('a', apiInstanceName).click();
    verifyOverviewPage(apiInstanceName)
})

When('I click on the COSMoS YAML tab', () => cy.get('button.v-btn.v-tab[value="cosmos"]').click())

Then('The COSMoS YAML page should be opened with Download button and Close button displayed', () => {
    cy.get('button[title="Download YAML content"]').should('be.visible');
    cy.get('button[title="Close YAML viewer"]').should('be.visible');
})

Then('The Download YAML content button is clicked', () => cy.get('button[title="Download YAML content"]').click())

When('I click on the Close button in the COSMoS YAML page', () => cy.get('button[title="Close YAML viewer"]').click())

When('I click on the history button', () => cy.get('button[title="History"]').click())

Then('The history page should be opened', () => {
    cy.get(`[data-cy="version-history-window"]`).should("exist");
    cy.clickButton('close-button')
})

Then('The {string} file should be downloaded in {string} format', (filename, format) => {
    const filePath = `cypress/downloads/${filename}.${format}`
    cy.readFile(filePath).then((file ) => {cy.log(file)})
})

function verifyOverviewPage(pageName){
    cy.get('.d-flex.page-title').invoke('text').should('match', new RegExp(pageName));
    cy.get('button[role="tab"][value="html"]').contains('Overview');
}

function goToPageSearchAndClickLink(endpoint, searchFor, clickOn) {
    cy.visit(`/library/activities/${endpoint}`)
    cy.searchAndCheckResults(searchFor)
    cy.get('table tbody tr td').contains(clickOn).click()
}

function openLinkedItemAndGoBack(itemName) {
    cy.get('.v-table__wrapper').contains('a', itemName).click();
    verifyOverviewPage(itemName) 
    cy.go(-1); // Go back to the previous page
    cy.wait(1000)
}
