const elementSubTypesUrl = `/study-elements/allowed-element-configs`
const createElementUrl = (study_uid) => `/studies/${study_uid}/study-elements`
const deleteElementUrl = (study_uid, element_uid) => `/studies/${study_uid}/study-elements/${element_uid}`
const studyElementsUrl = (study_uid) => `/studies/${study_uid}/study-elements?page_number=1&page_size=0&total_count=true&study_uid=${study_uid}`

export let element_uid
let type_uid, subType_uid, elements_uids

Cypress.Commands.add('getElementsUids', (studyUid) => {
    elements_uids = []
    cy.sendGetRequest(studyElementsUrl(studyUid)).then(response => response.body.items.forEach(item => elements_uids.push(item.element_uid)))
})

Cypress.Commands.add('deleteElements', (studyUid) => elements_uids.forEach(uid => cy.sendDeleteRequest(deleteElementUrl(studyUid, uid))))

Cypress.Commands.add('getElementTypeAndSubType', (subTypeName) => {
  cy.sendGetRequest(elementSubTypesUrl).then((response) => {
      subType_uid = response.body.find(item => item.subtype_name == subTypeName).subtype
      type_uid = response.body.find(item => item.subtype_name == subTypeName).type
  })
})

Cypress.Commands.add('addElementToStudy', (study_uid, element_name) => {
  cy.sendPostRequest(createElementUrl(study_uid), addElementBody(element_name)).then(response => element_uid = response.body.element_uid)
})

const addElementBody = (name) => {
  return {
        "planned_duration": null,
        "code": `${type_uid}`,
        "element_subtype_uid": `${subType_uid}`,
        "name": `${name}`,
        "short_name": `${name}`.substring(0, 4),
        "element_colour": "#BDBDBD"
    }
}