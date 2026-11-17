const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
import { getCurrStudyUid } from '../../support/helper_functions'

let ageAtBaselineRuleCode, ageGroupRuleCode

When('[API] User gets rule code for Age At Baseline with name {string}', (name) =>
    cy.getRuleCode('AGE_AT_BASELINE_RL', name).then(value => ageAtBaselineRuleCode = value ))

When('[API] User gets rule code for Age Rule with name {string}', (name) =>
    cy.getRuleCode('AGE_GRP_RL', name).then(value => ageGroupRuleCode = value ))

When('[API] The age rules are defined for current study', () => {
    cy.setStudyAgeRules(getCurrStudyUid(), ageAtBaselineRuleCode, ageGroupRuleCode)
})

Given('[API] The selected study age rules are cleared', () => {
    cy.setStudyAgeRules(getCurrStudyUid(), null, null)
})

When('The user defines age rules', () => {
    cy.selectVSelect('age_at_baseline_rule', 'Age at Baseline Rule 2')
    cy.selectVSelect('age_group_rule', 'Age with 1 decimal digit')
})

When('The age rules are cleared', () => {
    cy.clearDropdown('age_at_baseline_rule')
    cy.clearDropdown('age_group_rule')
})