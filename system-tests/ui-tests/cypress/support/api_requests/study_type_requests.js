Cypress.Commands.add('nullStudyType', (study_uid) => {
    cy.request({
        method: 'PATCH',
        url: Cypress.env('API') + '/studies/' + study_uid,
        body: {
            current_metadata: {
                high_level_study_design: {
                    confirmed_response_minimum_duration: null,
                    confirmed_response_minimum_duration_null_value_code: null,
                    is_adaptive_design: null,
                    is_adaptive_design_null_value_code: null,
                    is_extension_trial: null,
                    is_extension_trial_null_value_code: null,
                    post_auth_indicator: null,
                    post_auth_indicator_null_value_code: null,
                    study_stop_rules: "NONE",
                    study_stop_rules_null_value_code: null,
                    study_type_code: null,
                    study_type_null_value_code: null,
                    trial_intent_types_codes: null,
                    trial_phase_code: null,
                    trial_phase_null_value_code: null,
                    trial_type_codes: [],
                    trial_type_null_value_code: null,
                }
            }
        }
    })
})