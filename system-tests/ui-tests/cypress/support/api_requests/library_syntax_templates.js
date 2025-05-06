
let objective_uid, endpoint_uid, indication_uid, objective_category_uid, endpoint_category_uid, endpoint_sub_category_uid
const activateEndpointUrl = (endpoint_uid) => `${endpointTemplateUrl}/${endpoint_uid}/activations`
const activateObjectiveUrl = (objective_uid) => `${objectiveTemplateUrl}/${objective_uid}/activations`
const approveEndpointUrl = (endpoint_uid) => `${endpointTemplateUrl}/${endpoint_uid}/approvals`
const approveObjectiveUrl = (objective_uid) => `${objectiveTemplateUrl}/${objective_uid}/approvals`
const codelistUrl = (name) => `/ct/terms?page_size=100&sort_by={"name.sponsor_preferred_name":true}&codelist_name=${name}`
const objectiveInfoUrl = (objective_uid) => `${objectiveTemplateUrl}/${objective_uid}`
const endpointInfoUrl = (endpoint_uid) => `${endpointTemplateUrl}/${endpoint_uid}`
const objectiveTemplateUrl = '/objective-templates'
const endpointTemplateUrl = '/endpoint-templates'
const indicationUrl = '/dictionaries/terms?codelist_uid=DictionaryCodelist_000001&page_size=0'

Cypress.Commands.add('createObjective', (customName = '') => {
  cy.sendPostRequest(objectiveTemplateUrl, createObjectiveBody(customName)).then(response => objective_uid = response.body.uid)
})

Cypress.Commands.add('createEndpoint', (customName = '') => {
  cy.sendPostRequest(endpointTemplateUrl, createEndpointBody(customName)).then(response => endpoint_uid = response.body.uid)
})

Cypress.Commands.add('getInidicationUid', () => cy.getTemplateData(indicationUrl).then(uid => indication_uid = uid))

Cypress.Commands.add('getObjectiveCategoryUid', () => cy.getTemplateData(codelistUrl('Objective+Category')).then(uid => objective_category_uid = uid))

Cypress.Commands.add('getEndpointCategoryUid', () => cy.getTemplateData(codelistUrl('Endpoint+Category')).then(uid => endpoint_category_uid = uid))

Cypress.Commands.add('getEndpointSubCategoryUid', () => cy.getTemplateData(codelistUrl('Endpoint+Sub+Category')).then(uid => endpoint_sub_category_uid = uid))

Cypress.Commands.add('approveObjective', () => cy.sendPostRequest(approveObjectiveUrl(objective_uid), {}))

Cypress.Commands.add('approveEndpoint', () => cy.sendPostRequest(approveEndpointUrl(endpoint_uid), {}))

Cypress.Commands.add('inactivateObjective', () => cy.sendDeleteRequest(activateObjectiveUrl(objective_uid), {}))

Cypress.Commands.add('inactivateEndpoint', () => cy.sendDeleteRequest(activateEndpointUrl(endpoint_uid), {}))

Cypress.Commands.add('getObjectiveName', () => cy.getTemplateName(objectiveInfoUrl(objective_uid)))

Cypress.Commands.add('getEndpointName', () => cy.getTemplateName(endpointInfoUrl(endpoint_uid)))

Cypress.Commands.add('getTemplateName', (url) => cy.sendGetRequest(url).then((response) => { return response.body.name }))

Cypress.Commands.add('getTemplateData', (url) => {
  cy.sendGetRequest(url).then((response) => { return response.body.items[0].term_uid })
})

const createObjectiveBody = (customName = '') => {
  const name = customName === '' ? `API_ObjectiveTemplate${Date.now()}` : customName
  return {
      "name": `<p>${name}</p>`,
      "indication_uids": [
        `${indication_uid}`
      ],
      "category_uids": [
        `${objective_category_uid}`
      ]
  }
}

const createEndpointBody = (customName = '') => {
  const name = customName === '' ? `API_EndpointTemplate${Date.now()}` : customName
  return {
      "name": `<p>${name}</p>`,
      "indication_uids": [
        `${indication_uid}`
      ],
      "category_uids": [
        `${endpoint_category_uid}`
      ],
      "sub_category_uids": [
        `${endpoint_sub_category_uid}`
      ]
  }
}
