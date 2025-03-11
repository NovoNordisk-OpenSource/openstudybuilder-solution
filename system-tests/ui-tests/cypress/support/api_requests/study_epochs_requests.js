Cypress.Commands.add('createTestEpoch', (study_uid) => {
  cy.request(Cypress.env('API') + '/studies/' + study_uid + '/study-epochs').then((response) => {
    if (Object.keys(response.body.items).length === 0) {
        cy.request({
          method: 'POST',
          url: Cypress.env('API') + '/studies/' + study_uid + '/study-epochs',
          body: { 
            epoch_type: 'C101526_TREATMENT', 
            epoch: 'C101526_TREATMENT', 
            epoch_subtype: 'C101526_TREATMENT', 
            start_rule: 'D1', 
            end_rule: 'D2', 
            description: `DESC${Date.now()}`,
            color_hash: '#FF0000FF', 
            study_uid: study_uid 
        },
      })
      cy.reload()
    } else {
      cy.log('Epoch already exist')
    }
  })
})
