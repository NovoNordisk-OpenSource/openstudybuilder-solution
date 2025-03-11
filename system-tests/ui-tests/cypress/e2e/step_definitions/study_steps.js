const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Given('A test study is selected', () => {
    cy.selectTestStudy('Study_000001')
})

// Usage: 
// Given A 'CDISC DEV-0000' study is selected
Given('A {string} study is selected', (study_id) => {
    cy.selectStudyByStudyId(study_id)
})

Given('A secondary test study is selected', () => {
    cy.selectTestStudy('Study_000002')
})

Given('The study with multiple visists created has been selected', () => {
    cy.selectTestStudy('Study_000003')
})

Given('A study in draft status without study number is selected', () => {
    cy.selectTestStudy('Study_000004')
})

Given('A study in draft status without title is selected', () => {
    cy.selectTestStudy('Study_000005')
})

Given('A study in draft status with defined study number and study title is selected', () => {
    cy.selectTestStudy('Study_000006')
})

Given('A study in locked status with defined study number and study title is selected', () => {
    cy.selectTestStudy('Study_000007')
})

Given('A study exists in the database', () => {
    cy.checkStudyExists()
})

When('A new study is added', () => {
    cy.waitForTable()
    cy.clickButton('add-study')
    cy.selectAutoComplete('project-id', 'CDISC DEV')
    cy.fillInput('study-number', '5555')
    cy.fillInput('study-acronym', 'AutomationTest')
    cy.clickButton('save-button')
})

Then('The study is visible within the table', () => {
    cy.waitForTableData()
    cy.wait(500)
    cy.checkRowValueByColumnName('CDISC DEV-5555', 'Study acronym', 'AutomationTest')
    cy.checkRowValueByColumnName('CDISC DEV-5555', 'Study number', '5555')
    cy.checkRowValueByColumnName('CDISC DEV-5555', 'Project ID', 'CDISC DEV')
})