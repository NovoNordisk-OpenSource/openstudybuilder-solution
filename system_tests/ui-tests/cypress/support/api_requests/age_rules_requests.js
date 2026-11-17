Cypress.Commands.add('getRuleCode', (codelist, name) => {
    const sortBy = encodeURIComponent(JSON.stringify({ sponsor_preferred_name: true }))
    cy.sendGetRequest(`/ct/codelists/terms?page_size=0&sort_by=${sortBy}&codelist_submission_value=${encodeURIComponent(codelist)}`)
        .then(response => {
            const matches = response.body.items.filter(term => term.sponsor_preferred_name === name)
            return { term_uid: matches[0].term_uid, name: matches[0].sponsor_preferred_name }
        })
})

Cypress.Commands.add('setStudyAgeRules', (studyUid, ageAtBaselineRuleCode, ageGroupRuleCode) => {
    cy.sendUpdateRequest('PATCH', `/studies/${studyUid}`, {
        current_metadata: {
            high_level_study_design: {
                age_group_rule_code: ageGroupRuleCode,
                age_at_baseline_rule_code: ageAtBaselineRuleCode,
            },
        },
    })
})
