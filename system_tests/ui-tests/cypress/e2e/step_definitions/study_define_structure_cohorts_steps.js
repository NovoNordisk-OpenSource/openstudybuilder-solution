const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getCurrStudyUid } = require("../../support/helper_functions");
const { getShortUniqueId } = require("../../support/helper_functions");
const { getRandomIntOneToNinetyNine } = require("../../support/helper_functions");

let cohortDescription, cohortName, cohortCode, cohortShortName
const assignCohortName = () => cohortName = `Cohort${getShortUniqueId()}`
const assignCohortShortName = () => cohortShortName = `C${cohortCode = getRandomIntOneToNinetyNine()}`

When('[API] The Study Cohort is created within selected study', () => cy.createCohort(getCurrStudyUid()))

Given('[API] Get all Study Cohorts within selected study', () => cy.getCohortsUids(getCurrStudyUid()))

Given('[API] Delete all Study Cohorts within selected study', () => cy.deleteCohorts(getCurrStudyUid()))

When('The Study Cohort is found', () => cy.searchAndCheckPresence(cohortName, true))

Then('Add cohort button is clicked', () => cy.clickButton('add-study-cohort'))

When('First available study arm is selected', () => cy.selectFirstMultipleSelect('study-arm'))

When('Cohort description is set to {string}', (value) => cy.fillInput('study-cohort-description', cohortDescription = value))

When('User waits for cohort edit form to load', () => cy.get('[data-cy="study-cohort-name"] input').should('have.value', cohortName))

When('The form for new study cohort is filled', () => fillCohortData(assignCohortName(), assignCohortShortName(), cohortCode))

When('The study cohort is edited', () => fillCohortData(cohortName += ' Update', cohortShortName += ' Update', cohortCode))

Then('The field study arm is enabled for edition', () => cy.get('[data-cy="study-arm"]').should('not.have.attr', 'disabled'))

Then('The field study branch is enabled for edition', () => cy.get('[data-cy="branch-arm"]').should('not.have.attr', 'disabled'))

When('Planned number of subjects for cohort is set as {string}', (example) => cy.fillInput('study-cohort-planned-number-of-subjects', example))

When('Cohort name is set as string with length {int}', (number) => cy.fillInput('study-cohort-name', "x".repeat(number)))

When('Cohort short name is set as string with length {int}', (number) => cy.fillInput('study-cohort-short-name', "x".repeat(number)))

When('The Study Branch field is not populated in the Study Cohorts form', () => cy.get('[data-cy="branch-arm"]').clear({ force: true }))

When('The Cohort name field is not populated', () => cy.clearField('study-cohort-name'))

When('The Cohort short name field is not populated', () => cy.clearField('study-cohort-short-name'))

When('The Cohort code field is not populated', () => cy.clearField('study-cohort-code'))

When('Another Study Cohort is created with the same cohort name', () => fillCohortData(cohortName, 'Test', '10'))

When('Another Study Cohort is created with the same cohort short name', () => fillCohortData('Test', cohortShortName, '10'))

When('Another Study Cohort is created with the same cohort code', () => fillCohortData('Test', 'Test', cohortCode))

When('Cohort code is set as {string}', (number) => cy.fillInput('study-cohort-code', parseInt(number)))

When('Cohort code is set to random string', () => cy.fillInput('study-cohort-code', cohortCode = getShortUniqueId()))

When('The validation message appears for cohort name {string}', (value) => cy.checkIfValidationAppears('study-cohort-name', value))

When('The validation message appears for cohort short name {string}', (value) => cy.checkIfValidationAppears('study-cohort-short-name', value))

When('The validation message appears for cohort code {string}', (value) => cy.checkIfValidationAppears('study-cohort-code', value))

When('The validation message appears for cohort number of subjects {string}', (value) => cy.checkIfValidationAppears('study-cohort-planned-number-of-subjects', value))

Then('The study cohort is visible within the table', () => checkCohortData(cohortName, cohortShortName, cohortCode, cohortDescription))

Then('The new study cohort data is available in the table', () => checkCohortData('Cohort Test 1', 'CT1', 'C1', 'Description C1'))

Then('The new study cohort data is updated in the table', () => checkCohortData('Cohort Test 1 Update', 'CT1 Update', 'C1U', 'Description C1 Update'))

Then('The study cohort {int} data is visible in the table, including numberOfParticipants {int}', (index, numberOfParticipants) => {
    checkCohortData(`Cohort Test ${index}`, `CT${index}`, `C${index}`, `Description C${index}`, numberOfParticipants)
})

Then('The study arm {string} is connected to the cohort', (name) => cy.checkRowByIndex(0, 'Arm name', name))

Then('The study branch {string} is connected to the cohort', (name) => cy.checkRowByIndex(0, 'Branch name', name))

function fillCohortData(name, shortName, code) {
    cy.fillInput('study-cohort-name', name)
    cy.fillInput('study-cohort-short-name', shortName)
    cy.fillInput('study-cohort-code', code)
}

function checkCohortData(name, shortName, code, description, numberOfParticipants = '') {
    cy.checkRowByIndex(0, 'Cohort Name', name)
    cy.checkRowByIndex(0, 'Short Name', shortName)
    cy.checkRowByIndex(0, 'Cohort Code', code)
    cy.checkRowByIndex(0, 'Description', description)
    if (numberOfParticipants) cy.checkRowByIndex(0, 'No. of participants', numberOfParticipants)
}