const { getShortUniqueId } = require("../../support/helper_functions");

const ctPackageUrl = '/ct/packages/sponsor'
const ctTermUrl = '/ct/terms'
const ctCodelistUrl = '/ct/codelists'

Cypress.Commands.add('createAndOpenCodelist', () => {
  cy.sendPostRequest(ctCodelistUrl, createCodeListBody()).then((response) => {
    cy.visit('/library/ct_catalogues/All/' + response.body.codelist_uid)
    cy.wait(3000)
  })
})

Cypress.Commands.add('createAndOpenTerm', () => {
  cy.sendPostRequest(ctTermUrl, createTermBody()).then((response) => {
    cy.visit('/terms/' + response.body.term_uid)
    cy.wait(3000)
  })
})

Cypress.Commands.add('getAvailablePackageName', (catalogueName) => cy.sendGetRequest(`/ct/packages?catalogue_name=${catalogueName}`).then(response => { return response.body[0].uid }))

Cypress.Commands.add('createCTPackage', (packageName) => {
  cy.sendPostRequest(ctPackageUrl, createCTPackageBody(packageName), false, [201, 409])
})

const createCodeListBody = () => {
  const number = getShortUniqueId()
  return {
    "extensible": true,
    "is_ordinal": true,
    "library_name": "Sponsor",
    "template_parameter": false,
    "catalogue_names": ['SEND CT'],
    "sponsor_preferred_name":  `SponsorName${number}`,
    "name": `Name${number}`,
    "terms": [],
    "definition": `Definition${number}`,
    "submission_value": `Submission${number}`
  }
}

const createTermBody = () => {
  const number = getShortUniqueId()
  return {
      "catalogue_names": ['SEND CT'],
      "codelists": [{codelist_uid: 'C100129', submission_value: `SubmissionCode${number}`, order: '1'}],
      "definition": `Definition${number}`,
      "library_name": 'Sponsor',
      "name_submission_value": `SubmissionName${number}`,
      "nci_preferred_name": `NCI${number}`,
      "order": '1',
      "sponsor_preferred_name": `SponsorName${number}`,
      "sponsor_preferred_name_sentence_case": `SentanceName${number}`,
      "synonyms": `Synonyms${number}`,
      "is_ordinal": false
  }
}

const createCTPackageBody = (packageName) => {
  return {
      "extends_package": `${packageName}`,
      "effective_date": `${new Date().toISOString().split('T')[0]}`,
  }
}