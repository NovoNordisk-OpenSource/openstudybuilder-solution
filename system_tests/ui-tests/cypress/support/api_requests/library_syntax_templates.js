const { getShortUniqueId } = require("../../support/helper_functions");
let indication_uid, activity_instruction_uid, timeframe_uid, objective_uid, objective_category_uid
let endpoint_uid, endpoint_category_uid, endpoint_sub_category_uid
let criteria_uid, type_uid, criteria_category_uid, criteria_sub_category_uid

const activateActivityInstructionUrl = (activity_instruction_uid) => `${activityInstructionTemplateUrl}/${activity_instruction_uid}/activations`
const activateCriteriaUrl = (criteria_uid) => `${criteriaTemplateUrl}/${criteria_uid}/activations`
const activateEndpointUrl = (endpoint_uid) => `${endpointTemplateUrl}/${endpoint_uid}/activations`
const activateObjectiveUrl = (objective_uid) => `${objectiveTemplateUrl}/${objective_uid}/activations`
const activateTimeframeUrl = (timeframe_uid) => `${timeframeTemplateUrl}/${timeframe_uid}/activations`
const approveActivityInstructionUrl = (activity_instruction_uid) => `${activityInstructionTemplateUrl}/${activity_instruction_uid}/approvals`
const approveCriteriaUrl = (criteria_uid) => `${criteriaTemplateUrl}/${criteria_uid}/approvals`
const approveEndpointUrl = (endpoint_uid) => `${endpointTemplateUrl}/${endpoint_uid}/approvals`
const approveObjectiveUrl = (objective_uid) => `${objectiveTemplateUrl}/${objective_uid}/approvals`
const approveTimeframeUrl = (timeframe_uid) => `${timeframeTemplateUrl}/${timeframe_uid}/approvals`
const newVersionTimeframeUrl = (timeframe_uid) => `${timeframeTemplateUrl}/${timeframe_uid}/versions`
const codelistUrl = (name) => `/ct/terms?page_size=100&sort_by={"name.sponsor_preferred_name":true}&codelist_name=${name}`
const activityInstructionInfoUrl = (activity_instruction_uid) => `${activityInstructionTemplateUrl}/${activity_instruction_uid}`
const criteriaInfoUrl = (criteria_uid) => `${criteriaTemplateUrl}/${criteria_uid}`
const objectiveInfoUrl = (objective_uid) => `${objectiveTemplateUrl}/${objective_uid}`
const endpointInfoUrl = (endpoint_uid) => `${endpointTemplateUrl}/${endpoint_uid}`
const timeframeTemplateInfoUrl = (timeframe_uid) => `${timeframeTemplateUrl}/${timeframe_uid}`
const criteriaTemplateTypeUrl = '/ct/terms?page_size=100&codelist_name=Criteria+Type'
const activityInstructionTemplateUrl = '/activity-instruction-templates'
const criteriaTemplateUrl = '/criteria-templates'
const objectiveTemplateUrl = '/objective-templates'
const endpointTemplateUrl = '/endpoint-templates'
const timeframeTemplateUrl = '/timeframe-templates'
const indicationUrl = '/dictionaries/terms?codelist_uid=DictionaryCodelist_000001&page_size=0'

Cypress.Commands.add('createActivityInstruction', (group_uid, subgroup_uid, activity_uid, customName = '') => {
  cy.sendPostRequest(activityInstructionTemplateUrl, createActivityInstructionBody(group_uid, subgroup_uid, activity_uid, customName))
        .then(response => activity_instruction_uid = response.body.uid)
})

Cypress.Commands.add('createObjective', (customName = '') => {
  cy.sendPostRequest(objectiveTemplateUrl, createObjectiveBody(customName)).then(response => objective_uid = response.body.uid)
})

Cypress.Commands.add('createEndpoint', (customName = '') => {
  cy.sendPostRequest(endpointTemplateUrl, createEndpointBody(customName)).then(response => endpoint_uid = response.body.uid)
})

Cypress.Commands.add('createCriteria', (customName = '') => {
  cy.sendPostRequest(criteriaTemplateUrl, createCriteriaBody(customName)).then(response => criteria_uid = response.body.uid)
})

Cypress.Commands.add('createTimeframe', (customName = '') => {
  cy.sendPostRequest(timeframeTemplateUrl, createTimeframeBody(customName)).then(response => timeframe_uid = response.body.uid)
})

Cypress.Commands.add('getInclusionCriteriaUid', () => cy.getCriteriaTypeUid('Inclusion Criteria'))

Cypress.Commands.add('getExclusionCriteriaUid', () => cy.getCriteriaTypeUid('Exclusion Criteria'))

Cypress.Commands.add('getDosingCriteriaUid', () => cy.getCriteriaTypeUid('Dosing Criteria'))

Cypress.Commands.add('getRunInCriteriaUid', () => cy.getCriteriaTypeUid('Run-in Criteria'))

Cypress.Commands.add('getRandomizationCriteriaUid', () => cy.getCriteriaTypeUid('Randomisation Criteria'))

Cypress.Commands.add('getWithdrawalCriteriaUid', () => cy.getCriteriaTypeUid('Withdrawal Criteria'))

Cypress.Commands.add('getInidicationUid', () => {if (!indication_uid) cy.getTemplateData(indicationUrl).then(uid => indication_uid = uid)})

Cypress.Commands.add('getObjectiveCategoryUid', () => {if (!objective_category_uid) cy.getTemplateData(codelistUrl('Objective+Category')).then(uid => objective_category_uid = uid)})

Cypress.Commands.add('getEndpointCategoryUid', () => {if (!endpoint_category_uid) cy.getTemplateData(codelistUrl('Endpoint+Category')).then(uid => endpoint_category_uid = uid)})

Cypress.Commands.add('getEndpointSubCategoryUid', () => {if (!endpoint_sub_category_uid) cy.getTemplateData(codelistUrl('Endpoint+Sub+Category')).then(uid => endpoint_sub_category_uid = uid)})

Cypress.Commands.add('getCriteriaCategoryUid', () => {if (!criteria_category_uid) cy.getTemplateData(codelistUrl('Criteria+Category')).then(uid => criteria_category_uid = uid)})

Cypress.Commands.add('getCriteriaSubCategoryUid', () => {if (!criteria_sub_category_uid) cy.getTemplateData(codelistUrl('Criteria+Sub+Category')).then(uid => criteria_sub_category_uid = uid)})

Cypress.Commands.add('approveActivityInstruction', () => cy.sendPostRequest(approveActivityInstructionUrl(activity_instruction_uid), {}))

Cypress.Commands.add('approveCriteria', () => cy.sendPostRequest(approveCriteriaUrl(criteria_uid), {}))

Cypress.Commands.add('approveObjective', () => cy.sendPostRequest(approveObjectiveUrl(objective_uid), {}))

Cypress.Commands.add('approveEndpoint', () => cy.sendPostRequest(approveEndpointUrl(endpoint_uid), {}))

Cypress.Commands.add('approveTimeframe', () => cy.sendPostRequest(approveTimeframeUrl(timeframe_uid), {}))

Cypress.Commands.add('inactivateActivityInstruction', () => cy.sendDeleteRequest(activateActivityInstructionUrl(activity_instruction_uid), {}))

Cypress.Commands.add('inactivateCriteria', () => cy.sendDeleteRequest(activateCriteriaUrl(criteria_uid), {}))

Cypress.Commands.add('inactivateObjective', () => cy.sendDeleteRequest(activateObjectiveUrl(objective_uid), {}))

Cypress.Commands.add('inactivateEndpoint', () => cy.sendDeleteRequest(activateEndpointUrl(endpoint_uid), {}))

Cypress.Commands.add('inactivateTimeframe', () => cy.sendDeleteRequest(activateTimeframeUrl(timeframe_uid), {}))

Cypress.Commands.add('newVersionOfTimeframe', (name) => cy.sendPostRequest(newVersionTimeframeUrl(timeframe_uid), timeframeTemplateNewVersionBody(name)))

Cypress.Commands.add('getActivityInstructionName', () => cy.getTemplateName(activityInstructionInfoUrl(activity_instruction_uid)))

Cypress.Commands.add('getCriteriaName', () => cy.getTemplateName(criteriaInfoUrl(criteria_uid)))

Cypress.Commands.add('getObjectiveName', () => cy.getTemplateName(objectiveInfoUrl(objective_uid)))

Cypress.Commands.add('getEndpointName', () => cy.getTemplateName(endpointInfoUrl(endpoint_uid)))

Cypress.Commands.add('getTimeframeName', () => cy.getTemplateName(timeframeTemplateInfoUrl(timeframe_uid)))

Cypress.Commands.add('getTemplateName', (url) => cy.sendGetRequest(url).then((response) => { return response.body.name }))

Cypress.Commands.add('getTemplateData', (url) => {
  cy.sendGetRequest(url).then((response) => { return response.body.items[0].term_uid })
})

Cypress.Commands.add('getCriteriaTypeUid', (typeName) => {
  cy.sendGetRequest(criteriaTemplateTypeUrl).then((response) => {
    type_uid = response.body.items.find(criteria => criteria.name.sponsor_preferred_name == typeName).term_uid
  })
})

const createActivityInstructionBody = (group_uid, subgroup_uid, activity_uid, customName = '') => {
  const name = customName === '' ? `API_ActivityInstructionTemplate${getShortUniqueId()}` : customName
  return {
    "name": `<p>${name}</p>`,
    "indication_uids": [
      `${indication_uid}`
    ],
    "activity_group_uids": [
      `${group_uid}`
    ],
    "activity_subgroup_uids": [
      `${subgroup_uid}`
    ],
    "activity_uids": [
      `${activity_uid}`
    ]
  }
}

const createCriteriaBody = (customName = '') => {
  const name = customName === '' ? `API_CriteriaTemplate${getShortUniqueId()}` : customName
  return {
    "name": `<p>${name}</p>`,
    "type_uid": `${type_uid}`,
    "indication_uids": [
      `${indication_uid}`
    ],
    "category_uids": [
      `${criteria_category_uid}`
    ],
    "sub_category_uids": [
      `${criteria_sub_category_uid}`
    ]
  }
}

const createObjectiveBody = (customName = '') => {
  const name = customName === '' ? `API_ObjectiveTemplate${getShortUniqueId()}` : customName
  return {
      "name": `<p>${name}</p>`,
      "indication_uids": [
        `${indication_uid}`
      ],
      "category_uids": []
  }
}

const createEndpointBody = (customName = '') => {
  const name = customName === '' ? `API_EndpointTemplate${getShortUniqueId()}` : customName
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

const createTimeframeBody = (customName = '') => {
  const name = customName === '' ? `API_TimeframeTemplate${getShortUniqueId()}` : customName
  return {
    "name": `<p>${name}</p>`,
  }
}

const timeframeTemplateNewVersionBody = (name) => {
  return {
    "name": `<p>${name}</p>`,
    "change_description": "New version"
  }
}