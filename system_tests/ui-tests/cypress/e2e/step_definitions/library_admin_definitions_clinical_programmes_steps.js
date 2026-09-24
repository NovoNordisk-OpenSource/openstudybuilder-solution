const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

let programmeName, projectName

When('Clinical programme is found', () => cy.searchAndCheckPresence(programmeName, true))

When('Clinical programme is no longer available', () => cy.searchAndCheckPresence(programmeName, false))

When('Click on the + button to create a new clinical programme', () => cy.clickButton('add-clinical-programme'))

When('Input a clinical programme name', () => fillName(`Programme ${getShortUniqueId()}`))

Given('A test clinical programme exists and is not linked to any project', () => fillName(`Programme ${getShortUniqueId()}`))

When('Update the clinical programme name to a new one', () => fillName(`Update ${getShortUniqueId()}`))

When('User tries to update programme name', () => cy.fillInput('clinical-programme-name', 'Update'))

Given ('Create project and link it to the programme', () => {
    projectName = `Test project ${getShortUniqueId()}` 
    cy.selectAutoComplete('template-activity-group', programmeName)
    cy.fillInput('project-name', projectName)
    cy.fillInput('project-number', getShortUniqueId())
    cy.fillInput('project-description', `Test description ${getShortUniqueId()}`)
});

function fillName(name) {
    programmeName = name
    cy.fillInput('clinical-programme-name', programmeName) 
}