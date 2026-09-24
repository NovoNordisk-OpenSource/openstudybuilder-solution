const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

let projectName, programmeName

When('Test project is found', () => cy.searchAndCheckPresence(projectName, true))

When('Test project with linked study is found', () => cy.searchAndCheckPresence('CDISC Dev', true))

When('Test project is no longer available', () => cy.searchAndCheckPresence(projectName, false))

Given ('A Clinical Programme is created', () => {
    programmeName = `Test programme ${getShortUniqueId()}`
    cy.clickButton('add-clinical-programme')
    cy.fillInput('clinical-programme-name', programmeName) 
})

When('Click on the + button to create a new project', () => cy.clickButton('add-project'))

When('Select an existing clinical programme', () => cy.selectAutoComplete('template-activity-group', programmeName))

When('Input a project name, project number and description', () => fillProjectData())

When('Update the project name to a new one', () => {
    projectName += 'Update'
    cy.wait(1000)
    cy.fillInput('project-name', projectName)
})

Then('User tries to update project name', () => cy.fillInput('project-name', 'Update'))

function fillProjectData() {
    projectName = `Test project ${getShortUniqueId()}` 
    cy.fillInput('project-name', projectName)
    cy.fillInput('project-number', getShortUniqueId())
    cy.fillInput('project-description', `Test description ${getShortUniqueId()}`)
}