Cypress.Commands.add('createTestArm', (study_uid) => {
    cy.request('GET', Cypress.env('API') + '/studies/' + study_uid + '/study-arms?page_number=1&page_size=10&total_count=true&study_uid=' + study_uid).then((response) => {
        if (response.body.total == 0) {
            cy.request('POST', Cypress.env('API') + '/studies/' + study_uid + '/study-arms', {
                arm_colour: '#FF0000FF',
                arm_type_uid: 'CTTerm_000083',
                code: `Code${Date.now()}`,
                description: 'TestDescForArm',
                name: `Test arm${Date.now()}`,
                short_name: `Test arm${Date.now()}`,
                number_of_subjects: '100',
                randomization_group: `Random${Date.now()}`,
            }).then((created_response) => {
                cy.log('Test arm created with status code' + created_response.status)
            })
        }
    })
})

Cypress.Commands.add('deleteStudyArm', () => {
    cy.request('DELETE', Cypress.env('API') + 'studies/Study_000001/study-arms/StudyArm_000155').then((response) => cy.log('Test arm deleted' + response.status))
})