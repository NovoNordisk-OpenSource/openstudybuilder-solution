Cypress.Commands.add('createCriteriaTemplate', (criteria_type) => {
    cy.fixture('criteriaTemplates.js').then((criteria) => {
        cy.request({
            method: 'POST',
            url: Cypress.env('API') + '/criteria-templates',
            body: JSON.stringify(criteria[criteria_type]),
        }).then((response) => {
            cy.request({
                    method: 'POST',
                    url: Cypress.env('API') + '/criteria-templates/' + response.body.uid + '/approvals',
                })
        })
    })
    cy.reload()
})