//Probably redundant after the fixes - 29-02 will be the week worked on.
Cypress.Commands.add('checkStudyExists', () => {
  cy.request(Cypress.env('API') + '/studies').then((response) => {
    if (response.body.items == '') {
      cy.log('Studies not exisitng - critical error')
    } else {
      cy.log('Study - found')
    }
  })
})

Cypress.Commands.add('nullRegistryIdentifiersForStudy', () => {
  cy.request({
    method: 'PATCH',
    url: Cypress.env('API') + '/studies/Study_000001',
    body: {
      current_metadata: {
        identification_metadata: {
          registry_identifiers: {
            ct_gov_id: '',
            ct_gov_id_null_value_code: null,
            eudract_id: '',
            eudract_id_null_value_code: null,
            universal_trial_number_utn: '',
            universal_trial_number_utn_null_value_code: null,
            japanese_trial_registry_id_japic: '',
            japanese_trial_registry_id_japic_null_value_code: null,
            investigational_new_drug_application_number_ind: '',
            investigational_new_drug_application_number_ind_null_value_code: null,
          },
        },
      },
    },
  })
})

Cypress.Commands.add('testCompound', () => {
  cy.get(JSON.parse(window.localStorage.getItem('selectedStudy'))).then((current_study) => {
    cy.request(Cypress.env('API') + '/studies/' + current_study[0].uid + '/study-compounds').then((response) => {
      if (response.body == '') {
        cy.log('Compound - not found - creating')
        cy.request('POST', Cypress.env('API') + '/studies/' + current_study[0].uid + '/study-compounds/select', {
          compound_uid: null,
          device: null,
          dispensedIn: null,
          dosage_form: null,
          formulation: null,
          other_info: null,
          reason_for_missing_null_value_code: { term_uid: 'CTTerm_000143', name: 'Derived' },
          route_of_administration: null,
          type_of_treatment_uid: 'CTTerm_000159',
        }).then((response) => {
          expect(response.status).to.eq(201)
          cy.log('Compound - created - revisiting the page')
          cy.visit('studies/study_structure/epochs')
        })
      } else {
        cy.log('Compound - found')
      }
    })
  })
})

Cypress.Commands.add('createAndOpenCodelist', () => {
  let number = Date.now()
  cy.request('POST', Cypress.env('API') + '/ct/codelists', {
    catalogue_name: 'SEND CT',
    definition: `Definition${number}`,
    extensible: true,
    library_name: 'Sponsor',
    name: `Name${number}`,
    nci_preferred_name: `NCI${number}`,
    sponsor_preferred_name: `SponsorName${number}`,
    submission_value: `Submission${number}`,
    template_parameter: false,
    terms: [],
  }).then((created_response) => {
    cy.log('Codelist - created - visiting')
    cy.visit('/library/ct_catalogues/All/' + created_response.body.codelist_uid)
    cy.wait(3000)
  })
})

Cypress.Commands.add('approveCodelist', (codelist_uid, name_status, attributes_status) => {
  if (name_status == 'Draft') {
    cy.log('Codelist - names approved')
    cy.request('POST', Cypress.env('API') + '/ct/codelists/' + codelist_uid + '/names/approvals')
  }
  if (attributes_status == 'Draft') {
    cy.log('Codelist - attributes approved')
    cy.request('POST', Cypress.env('API') + '/ct/codelists/' + codelist_uid + '/attributes/approvals')
  }
})

Cypress.Commands.add('createAndOpenTerm', () => {
  let number = Date.now()
  cy.request('POST', Cypress.env('API') + '/ct/terms', {
    catalogue_name: 'SEND CT',
    code_submission_value: `SubmissionCode${number}`,
    codelist_uid: 'C100129',
    definition: `Definition${number}`,
    library_name: 'Sponsor',
    name_submission_value: `SubmissionName${number}`,
    nci_preferred_name: `NCI${number}`,
    order: '1',
    sponsor_preferred_name: `SponsorName${number}`,
    sponsor_preferred_name_sentence_case: `SentanceName${number}`,
    synonyms: `Synonyms${number}`,
  }).then((created_response) => {
    cy.log('Term - created - visiting')
    cy.visit('/library/ct_catalogues/All/C100129/terms/' + created_response.body.term_uid)
    cy.wait(3000)
  })
})


Cypress.Commands.add('createCTPackage', (packageName) => {
  cy.request({
    url: `${Cypress.env('API')}/ct/packages/sponsor`,
    method: 'POST',
    body: {
      extends_package: `${packageName}`,
      effective_date: `${new Date().toISOString().split('T')[0]}`
    },
    failOnStatusCode: false
  }).then((response) => {
    expect(response.status).to.be.oneOf([201, 409])
    cy.log(`${packageName} exists`)
  })
})