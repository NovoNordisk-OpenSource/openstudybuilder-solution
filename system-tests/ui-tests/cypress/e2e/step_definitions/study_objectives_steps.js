const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The objective is created from studies', () => {
    cy.createTestObjective('Study_000002')
    cy.waitForTable()
    cy.clickButton('add-study-objective')
    cy.clickButton('objective-from-select', true)
    cy.clickButton('creationMode-continue-button', true)
})

When('The test study for objective copying is selected', () => {
    cy.selectVSelect('Select studies', 'CDISC DEV-1234')
    cy.clickButton('selectStudies-continue-button', true)
})

When('The objective from test study is copied', () => {
    cy.get('[data-cy="form-body"]').within(() => {
        cy.clickFirstButton('Copy item', true)
        cy.clickButton('selectObjective-save-button', true)
    })
    cy.waitForFormSave()
})

Then('The objective copied from test study is visible within the table with correct data', () => {
    cy.fixture('studyObjective').then((fixture) => {
        cy.wait(1000)
        cy.tableContains(fixture.template_selected_from_study)
    })
})

When('The objective is copied from existing template', () => {
    cy.waitForTable()
    cy.clickButton('add-study-objective')
    cy.clickButton('objective-from-template', true)
    cy.clickButton('creationMode-continue-button', true)
    cy.get('[data-cy="form-body"]').within(() => {
        cy.clickFirstButton('Select template', true)
        cy.clickButton('selectTemplate-continue-button', true)
    })
})

Then('The objective created from existing template is visible within the table with correct data', () => {
    cy.fixture('studyObjective').then((fixture) => {
        cy.wait(1000)
        cy.tableContains(fixture.objective_template)
    })
})

When('The objective is created from scratch based on following template', (docstring) => {
    cy.waitForTable()
    cy.clickButton('add-study-objective')
    cy.get('[data-cy="form-body"]').within(() => {
        cy.clickButton('objective-from-scratch', true)
        cy.clickButton('creationMode-continue-button', true)
        cy.get('div.ql-editor.ql-blank').type('Study objective for E2E test run.')
        cy.clickButton('createTemplate-continue-button', true)
        cy.clickButton('createObjective-continue-button', true)
    })
})

When('The objective level is selected and the form is saved', () => {
    cy.selectAutoComplete('Objective level', 'Primary Objective')
    cy.clickButton('objectiveLevel-save-button', true)
})

Then('The objective created from scratch is visible within the table with correct data', (docstring) => {
    cy.tableContains('Study objective for E2E test run.')
})