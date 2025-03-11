Cypress.Commands.add('createTestObjective', (study_uid) => {
    cy.fixture('studyObjective.js').then((objective) => {
        cy.request({
            method: 'POST',
            url: Cypress.env('API') + '/objective-templates',
            body: {
                name: objective.objective_template,
                study_uid: study_uid,
                library_name: "User Defined"
            },
        }).then((response) => {
            if (response.status == 201) {
                cy.request({
                    method: 'POST',
                    url: Cypress.env('API') + '/objective-templates/' + response.body.uid + '/approvals',
                })
            } else {
                cy.log('approval skipped')
            }
            cy.request('POST', Cypress.env('API') + '/studies/' + study_uid + '/study-objectives', {
                objective_level_uid: "C85826_OBJPRIM",
                objective_data: {
                    objective_template_uid: response.body.uid,
                    parameter_values: [],
                    library_name: "User Defined"
                }
            })
        })
    })
})