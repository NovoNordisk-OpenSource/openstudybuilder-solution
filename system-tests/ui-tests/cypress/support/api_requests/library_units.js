
let unit_uid, unitSubet_uid, ctUnit_uid
const unitsUrl = '/concepts/unit-definitions'
const unitsInfoUrl = (unit_uid) => `${unitsUrl}/${unit_uid}`
const activateUnitUrl = (unit_uid) => `${unitsUrl}/${unit_uid}/activations`
const approveUnitUrl = (unit_uid) => `${unitsUrl}/${unit_uid}/approvals`
const codelistUrl = (name) => `/ct/terms?page_size=100&sort_by={"name.sponsor_preferred_name":true}&codelist_name=${name}`
const ctUnitUrl = '/ct/terms?page_size=0&sort_by={"name.sponsor_preferred_name":true}&codelist_uid=C71620'

Cypress.Commands.add('createUnit', (customName = '') => {
  cy.sendPostRequest(unitsUrl, createUnitBody(customName)).then(response => unit_uid = response.body.uid)
})

Cypress.Commands.add('getUnitSubsetUid', () => cy.getTemplateData(codelistUrl('Unit+Subset')).then(uid => unitSubet_uid = uid))

Cypress.Commands.add('getCtUnitUid', () => cy.getTemplateData(ctUnitUrl).then(uid => ctUnit_uid = uid))

Cypress.Commands.add('approveUnit', () => cy.sendPostRequest(approveUnitUrl(unit_uid), {}))

Cypress.Commands.add('inactivateUnit', () => cy.sendDeleteRequest(activateUnitUrl(unit_uid), {}))

Cypress.Commands.add('getUnitName', () => cy.sendGetRequest(unitsInfoUrl(unit_uid)).then((response) => { return response.body.name }))

Cypress.Commands.add('getTemplateData', (url) => {
  cy.sendGetRequest(url).then((response) => { return response.body.items[0].term_uid })
})

const createUnitBody = (customName = '') => {
  const name = customName === '' ? `API_Unit${Date.now()}` : customName
  return {
    convertible_unit: false,
    display_unit: false,
    master_unit: false,
    si_unit: false,
    us_conventional_unit: false,
    use_molecular_weight: false,
    use_complex_unit_conversion: false,
    library_name: "Sponsor",
    name: name,
    ct_units: [
        ctUnit_uid
    ],
    unit_subsets: [
      unitSubet_uid
    ]
  }
}
