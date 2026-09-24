const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getCurrStudyUid } = require("../../support/helper_functions");
const { getShortUniqueId } = require("../../support/helper_functions");
const { getRandomIntOneToNinetyNine } = require("../../support/helper_functions");

let branchDescription  = 'E2E Test Branch', randomisationGroup ='B', branchName, branchShortName
const assignBranchName = () => branchName = `Branch${getShortUniqueId()}`
const assignBranchShortName = () => branchShortName = `B${getRandomIntOneToNinetyNine()}`

Given('[API] The Study Branch is created within selected study', () => cy.createBranch(getCurrStudyUid()))

When('The Study Branch is found', () => cy.searchAndCheckPresence(branchName, true))

When('The Study Branch is no longer available', () => cy.searchAndCheckPresence(branchName, false))

Given('The first available arm is selected for the branch', () => cy.selectFirstVSelect('study-arm'))

Then('The option to create branch arm is not visible', () => cy.get('[data-cy="add-study-branch-arm"]').should('not.exist'))

When('Add branch button is clicked', () => cy.clickButton('add-study-branch-arm'))

When('The Study Branch description is filled in', () => cy.fillInput('study-branch-arm-description', branchDescription))

When('The Study Branch description is updated', () => cy.fillInput('study-branch-arm-description', branchDescription += ' Update'))

When('The form for new study branch arm is filled', () => fillBranchData(assignBranchName(), assignBranchShortName(), randomisationGroup))

When('The study branch arm is edited', () => fillBranchData(branchName += ' Update', branchShortName += ' Update', randomisationGroup = 'U'))

Then('The stady arm field is disabled', () => cy.get('[data-cy="study-arm"]').should('have.class', 'v-input--disabled'))

When('Planned number of subjects for branch is set as {string}', (example) => cy.fillInput('study-branch-arm-planned-number-of-subjects', example))

When('The Study Arm field is not populated in the Study Branch Arms form', () => cy.clearInput('study-arm'))

When('The Branch name field is not populated', () => cy.clearInput('study-branch-arm-name'))

When('The Branch short name field is not populated', () => cy.clearInput('study-branch-arm-short-name'))

When('Another Study Branch Arm is created with the same arm name', () => fillBranchData(branchName, getShortUniqueId(), getShortUniqueId()))

When('Another Study Branch Arm is created with the same branch arm short name', () => fillBranchData(getShortUniqueId(), branchShortName, getShortUniqueId()))

When('Branch arm code text is set to value longer than 20 characters', () => cy.fillInput('study-branch-arm-code', 'a'.repeat(21)))

When('The validation message appears for branch number of subjects {string}', (value) => cy.checkIfValidationAppears('study-branch-arm-planned-number-of-subjects', value))

When('The validation message appears for branch randomisation code {string}', (value) => cy.checkIfValidationAppears('study-branch-arm-code', value))

When('The validation message appears for empty branch name', () => cy.checkIfValidationAppears('study-branch-arm-name'))

When('The validation message appears for empty branch short name', () => cy.checkIfValidationAppears('study-branch-arm-short-name'))

When('The validation message appears for empty study arm', () => cy.checkIfValidationAppears('study-arm'))

function fillBranchData(branchName, branchShortName, randomisationGroup) {
    cy.fillInput('study-branch-arm-name', branchName)
    cy.fillInput('study-branch-arm-short-name', branchShortName)
    cy.fillInput('study-branch-arm-randomisation-group', randomisationGroup)
}

Then('The study branch arm is visible within the table', () => {
    cy.checkRowByIndex(0, 'Branch name', branchName)
    cy.checkRowByIndex(0, 'Short name', branchShortName)
    cy.checkRowByIndex(0, 'Random. Code', randomisationGroup)
    cy.checkRowByIndex(0, 'Random. group', randomisationGroup)
})

Then('The study branch arm data is visible, including arm name {string}, cohort name {string}, cohort code {string}, branch short name {string} and number of participants {int}', (armName, cohortName, cohortCode, branchShortName, numberOfParticipants) => {
    cy.checkRowByIndex(0, 'Branch name', `${armName} ${cohortName}`)
    cy.checkRowByIndex(0, 'Short name', branchShortName)
    cy.checkRowByIndex(0, 'No. of participants', numberOfParticipants)
    cy.checkRowByIndex(0, 'Arm name', armName)
    cy.checkRowByIndex(0, 'Cohort name', cohortName)
    cy.checkRowByIndex(0, 'Cohort code', cohortCode)
})
