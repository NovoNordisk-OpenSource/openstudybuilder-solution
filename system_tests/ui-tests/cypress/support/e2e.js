// Import commands.js using ES2015 syntax:
import '@shelex/cypress-allure-plugin'
import '@4tw/cypress-drag-drop'
import './api_requests/authorisation_methods'
import './api_requests/crf_requests'
import './api_requests/ct_requests'
import './api_requests/disease_milestones_requests'
import './api_requests/library_activities'
import './api_requests/library_syntax_templates'
import './api_requests/library_units'
import './api_requests/rest_client'
import './api_requests/study_requests'
import './api_requests/study_activities_requests'
import './api_requests/study_desgin_matirx_requests'
import './api_requests/study_arm_requests'
import './api_requests/study_branch_requests'
import './api_requests/study_cohorts_requests'
import './api_requests/study_elements_requests'
import './api_requests/study_epochs_requests'
import './api_requests/study_visits_requests'
import './api_requests/study_compounds_request'
import './api_requests/study_data_suppliers_requests'
import './api_requests/trial_summary_parameters_requests'
import './front_end_commands/buttons_commands'
import './front_end_commands/drop_down_commands'
import './front_end_commands/elements_assertion_commands'
import './front_end_commands/input_field_commands'
import './front_end_commands/table_commands'
import './front_end_commands/waiting_commands'
import './helper_functions'

Cypress.on('uncaught:exception', (err, runnable) => {
    // returning false here prevents Cypress from
    // failing the test
    return false
})

//Run that command once prior to the whole test suit
before(function() {
    cy.prepareAuthTokens()
    cy.createTestStudy('9876', 'E2E Main Test Study')
    cy.createTestStudy('9844', 'E2E - Process testing - New')
    cy.createTestStudy('9866', 'Study cloning testing')
    cy.createTestStudy('9877', 'Study structure testing')
    cy.createTestStudy('9878', 'Manual structure testing')
    cy.createTestStudy('9879', 'Additional study for testing')
    cy.createTestStudy('9880', 'Study visits testing')
    cy.createTestStudy('9881', 'Empty study')
    cy.createTestStudy('9882', 'Study template testing')
    cy.createTestStudy('9883', 'Empty study 2')
    cy.createTestStudy('9901', 'Lock/Unlock study')
    cy.createTestStudy('9902', 'Lock/Unlock study - Final Protocol')
    cy.createTestStudy('8014', 'Data completness tags - complete study')
    cy.createTestStudy('8015', 'Data completness tags - uncomplete study')
    cy.createTestStudy('8016', 'Data completness tags - multiple tags')
});