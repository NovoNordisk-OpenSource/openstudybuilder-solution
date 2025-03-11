const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
import { stringToBoolean } from '../../support/helper_functions'

When('The study type is fully defined', () => {
    cy.nullStudyType('Study_000001')
    cy.wait(5000)
    cy.reload()
    cy.wait(3000)
    cy.fixture('studyType').then((type) => {
        startEdition()
        cy.selectAutoComplete('study-type', type.study_type)
        cy.selectMultipleSelect('trial-type', type.trial_type)
        cy.selectAutoComplete('study-phase-classification', type.phase_classification)
        cy.selectRadio('extension-study', type.extension_study)
        cy.selectRadio('adaptive-design', type.adaptive_design)
        cy.contains('.v-checkbox', 'NONE').find('input').uncheck()
        cy.fillInput('stop-rule', type.stop_rules)
        cy.setDuratinField('confirmed-resp-min-dur', type.confirmed_response_min_dur_value, type.confirmed_response_min_dur_unit)
        cy.selectRadio('post-auth-safety-indicator', type.post_auth_safety_indicator)
        cy.clickButton('save-button')
        cy.wait(1000)
    })
})

Then('The study type data is reflected in the table', () => {
    cy.fixture('studyType').then((type) => {
        cy.tableContains(type.study_type)
        cy.tableContains(type.trial_type)
        cy.tableContains('Phase 0 Trial')
        cy.tableContains(type.stop_rules)
        cy.tableContains(type.post_auth_safety_indicator)
    })
})

When('The Study Stop Rule NONE option is selected', () => {
    cy.nullStudyType('Study_000001')
    cy.wait(1000)
    cy.reload()
    cy.wait(1000)
    startEdition()
})

Then('The Study Stop Rule field is disabled', () => {
    cy.get('[data-cy="stop-rule"]').within(() => {
        cy.get('input').should('be.disabled')
    })
        
})

When('The Confirmed response minimum duration NA option is selected', () => {
    cy.nullStudyType('Study_000001')
    cy.wait(5000)
    cy.reload()
    startEdition()
    cy.get('[data-cy="not-applicable-checkbox"] input').check()
})

Then('The Confirmed response minimum duration field is disabled', () => {
    cy.get('[data-cy="duration-value"]').within(() => {
        cy.get('input').should('be.disabled')
    })
    cy.get('[data-cy="duration-unit"]').within(() => {
        cy.get('input').should('be.disabled')
    })
})

Given('Another study with study type defined exists', () => {
    cy.request(Cypress.env('API') + '/studies/Study_000002?include_sections=high_level_study_design').as('copyData')
})

When('The study type is partially defined', () => {
    cy.nullStudyType('Study_000001')
    cy.wait(5000)
    cy.reload()
    cy.fixture('studyType').then((type) => {
        startEdition()
        cy.selectAutoComplete('study-type', type.study_type)
        cy.setDuratinField('confirmed-resp-min-dur', type.confirmed_response_min_dur_value, type.confirmed_response_min_dur_unit)
        cy.selectRadio('post-auth-safety-indicator', type.post_auth_safety_indicator)
        cy.clickButton('save-button')
    })
})

When('The study type is copied from another study without overwriting', () => {
    cy.clickButton('copy-from-study')
    cy.selectVSelect('study-id', 'CDISC DEV-1234')
    cy.clickButton('overwrite-no', true)
    cy.clickButton('ok-form')
    cy.clickButton('save-button')
    cy.wait(2000)
})

Then('Only the missing information is filled from another study in the study type form', () => {
    cy.get('@copyData').then(request => {
        cy.fixture('studyType').then((type) => {
            cy.tableContains(type.study_type)
            if (request.body.current_metadata.high_level_study_design.trial_type_codes[0] !== undefined) {
                cy.tableContains(request.body.current_metadata.high_level_study_design.trial_type_codes[0].name);
              }
            cy.tableContains(stringToBoolean(request.body.current_metadata.high_level_study_design.is_extension_trial))
            cy.tableContains(stringToBoolean(request.body.current_metadata.high_level_study_design.is_adaptive_design))
            cy.tableContains(request.body.current_metadata.high_level_study_design.study_stop_rules)
        })
    })
})

When('The study type is copied from another study with overwriting', () => {
    cy.clickButton('copy-from-study')
    cy.selectVSelect('study-id', 'CDISC DEV-1234')
    cy.clickButton('overwrite-yes', true)
    cy.clickButton('ok-form')
    cy.clickButton('save-button')
    cy.wait(2000)
})

Then('All the informations are overwritten in the study type', () => {
    cy.get('@copyData').then(request => {
        if (request.body.current_metadata.high_level_study_design.trial_type_codes[0] !== undefined) {
            cy.tableContains(request.body.current_metadata.high_level_study_design.trial_type_codes[0].name);
          }
        cy.tableContains(stringToBoolean(request.body.current_metadata.high_level_study_design.is_extension_trial))
        cy.tableContains(stringToBoolean(request.body.current_metadata.high_level_study_design.is_adaptive_design))
        cy.tableContains(request.body.current_metadata.high_level_study_design.study_stop_rules)
    })
})

function startEdition() {
    cy.clickButton('edit-content')
    cy.wait(1000)
}