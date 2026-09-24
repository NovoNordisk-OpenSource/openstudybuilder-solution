const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
import { getCurrStudyUid, stringToBoolean } from '../../support/helper_functions'

let studyType = 'Expanded Access', trialType = 'Adhesion Performance Study', phaseClassification = 'Phase 1'
let extensionStudy = 'Yes', adaptiveDesign = 'Yes', postAuthSafetyIndicator = 'Yes'
let confirmedResponseMinValue = '50', confirmedResponseUnit = 'days', stopRules = 'Test stop rule'
let intervetionType = 'Gene Therapy', studyIntentType = 'Cure', controlType = 'Active', intervetionModel = 'Crossover'
let isRandomised = 'Yes', addOnExistingTreatments = 'Yes', stratificationFactor = 'Test stratification factor', studyBindingSchema = 'Open Label'

When('The study intervention type is edited', () => {
    cy.wait(1000)
    cy.selectAutoComplete('Intervention type', intervetionType)
    cy.wait(1000)
    cy.selectMultipleSelect('Study intent type', studyIntentType)
    cy.selectAutoComplete('Control type', controlType)
    cy.selectAutoComplete('Intervention model', intervetionModel)
    cy.selectRadioButton('Study is randomised', isRandomised)
    cy.selectRadioButton('Add-on to existing treatments', addOnExistingTreatments)
    cy.selectAutoComplete('Study blinding schema', studyBindingSchema)
    cy.fillInput('Stratification factor', stratificationFactor)
    cy.setDuration('planned-study-length', '5', 'days')
})

Then('The study intervention type data is reflected in the table', () => {
    cy.tableContains(intervetionType)
    cy.tableContains(studyIntentType)
    cy.tableContains(addOnExistingTreatments)
    cy.tableContains(controlType)
    cy.tableContains(intervetionModel)
    cy.tableContains(isRandomised)
    cy.tableContains(stratificationFactor)
    cy.tableContains(studyBindingSchema)
})

When('[API] The null study type is created for the selected study', () => cy.nullStudyType(getCurrStudyUid()))

When('User intercepts study design request', () => cy.intercept('**?include_sections=high_level_study_design').as('studyDesignRequest'))

When('The study type is fully defined', () => {
    cy.selectAutoComplete('study-type', studyType)
    cy.selectMultipleSelect('trial-type', trialType)
    cy.selectAutoComplete('study-phase-classification', phaseClassification)
    cy.selectRadioButton('extension-study', extensionStudy)
    cy.selectRadioButton('adaptive-design', adaptiveDesign)
    cy.contains('.v-checkbox', 'NONE').find('input').uncheck()
    cy.fillInput('stop-rule', stopRules)
    cy.setDuration('confirmed-resp-min-dur',confirmedResponseMinValue, confirmedResponseUnit)
    cy.selectRadioButton('post-auth-safety-indicator', postAuthSafetyIndicator)
})

Then('The study type data is reflected in the table', () => {
    cy.tableContains(studyType)
    cy.tableContains(trialType)
    cy.tableContains(phaseClassification)
    cy.tableContains(stopRules)
    cy.tableContains(postAuthSafetyIndicator)
})

Then('The Study Stop Rule field is disabled', () => cy.get('[data-cy="stop-rule"] input').should('be.disabled'))

When('The Confirmed response minimum duration NA option is selected', () => {
    cy.get('[data-cy="not-applicable-checkbox"] input').check()
})

Then('The Confirmed response minimum duration field is disabled', () => {
    cy.get('[data-cy="duration-value"] input').should('be.disabled')
    cy.get('[data-cy="duration-unit"] input').should('be.disabled')
})

When('The study type is partially defined', () => {
    cy.selectAutoComplete('study-type', studyType)
    cy.setDuration('confirmed-resp-min-dur', confirmedResponseMinValue, confirmedResponseUnit)
    cy.selectRadioButton('post-auth-safety-indicator', type.post_auth_safety_indicator)
})

When('The study type is copied from another study without overwriting', () => {
    cy.clickButton('copy-from-study')
    cy.selectVSelect('study-id', 'CDISC DEV-1234')
    cy.clickButton('overwrite-no', true)
    cy.clickButton('ok-form')
})

Then('Only the missing information is filled from another study in the study type form', () => {
    cy.get('@copyData').then(request => {
        cy.tableContains(studyType)
        if (request.body.current_metadata.high_level_study_design.trial_type_codes[0] !== undefined) {
            cy.tableContains(request.body.current_metadata.high_level_study_design.trial_type_codes[0].name);
        }
        cy.tableContains(stringToBoolean(request.body.current_metadata.high_level_study_design.is_extension_trial))
        cy.tableContains(stringToBoolean(request.body.current_metadata.high_level_study_design.is_adaptive_design))
        cy.tableContains(request.body.current_metadata.high_level_study_design.study_stop_rules)
    })
})

When('The study type is copied from another study with overwriting', () => {
    cy.clickButton('copy-from-study')
    cy.selectVSelect('study-id', 'CDISC DEV-1234')
    cy.clickButton('overwrite-yes', true)
    cy.clickButton('ok-form')
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

When('The user sets study development stage to {string}', (stage) => cy.selectVSelect('development_stage', stage))

When('The study development stage is {string}', (stage) => {
    cy.wait('@studyDesignRequest').then((request) => {
        expect(request.response.body.current_metadata.high_level_study_design.development_stage_code.sponsor_preferred_name).to.eq(stage)
    })
})
