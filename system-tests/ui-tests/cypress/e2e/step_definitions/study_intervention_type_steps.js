const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The study intervention type is edited', () => {
    cy.fixture('studyInterventionType').then((intervention) => {
        cy.clickButton('edit-content')
        cy.wait(1000)
        cy.selectAutoComplete('Intervention type', intervention.intervention_type)
        cy.wait(1000)
        cy.selectMultipleSelect('Study intent type', intervention.study_intent_type)
        cy.selectAutoComplete('Control type', intervention.control_type)
        cy.selectAutoComplete('Intervention model', intervention.intervention_model)
        cy.selectRadio('Study is randomised', intervention.study_is_randomised)
        cy.selectRadio('Add-on to existing treatments', intervention.add_on_existing_treatments)
        cy.selectAutoComplete('Study blinding schema', intervention.study_blinding_schema)
        cy.fillInput('Stratification factor', intervention.stratification_factor)
        cy.setDuratinField('planned-study-length', intervention.planned_study_length_value, intervention.planned_study_length_unit)
        cy.clickButton('save-button')
        cy.waitForFormSave()
    })
})

Then('The study intervention type data is reflected in the table', () => {
    cy.fixture('studyInterventionType').then((intervention) => {
        cy.tableContains(intervention.intervention_type)
        cy.tableContains(intervention.study_intent_type)
        cy.tableContains(intervention.add_on_existing_treatments)
        cy.tableContains(intervention.control_type)
        cy.tableContains(intervention.intervention_model)
        cy.tableContains(intervention.study_is_randomised)
        cy.tableContains(intervention.stratification_factor)
        cy.tableContains(intervention.study_blinding_schema)
    })
})