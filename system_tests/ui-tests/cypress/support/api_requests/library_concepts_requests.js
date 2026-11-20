let unitDefinitionsUrl = '/concepts/unit-definitions?page_size=0'
let dataSetsUrl = '/activity-instance-classes/model-mappings/datasets?ig_uid=SDTMIG'
let categoriesUrl = '/ct/codelists/terms?page_size=0&sort_by={"sponsor_preferred_name":true}&codelist_submission_value=FINDCAT'
let subCategoriesUrl = '/ct/codelists/terms?page_size=0&sort_by={"sponsor_preferred_name":true}&codelist_submission_value=FINDSCAT'
let insanceActivityItemClassesUrl = (instanceClassUid) => `/activity-instance-classes/${instanceClassUid}/activity-item-classes`
let itemClassesUrl = (instanceClassUid, dataset) => `/activity-instance-classes/${instanceClassUid}/activity-item-classes?dataset_uid=${dataset}&ig_uid=SDTMIG`
let itemClassMetadataUrl = (itemClassUid, dataset) => `/activity-item-classes/${itemClassUid}/datasets/${dataset}/codelists?page_size=0&ct_catalogue_name=SDTM+CT`
let termsConnectedToClassUid = (classTermUid) => `/ct/codelists/${classTermUid}/terms?page_size=0&sort_by={"sponsor_preferred_name":true}`

let instanceClassUid, testNameUid, testCodeUid, testNameTermUid, testCodeTermUid

Cypress.Commands.add('getTestNameAndCodeUids', (dataset) => {
    cy.sendGetRequest(itemClassesUrl(instanceClassUid, dataset)).then(response => {
        testNameUid = response.body.find(item => item.name == 'test_name').uid
        testCodeUid = response.body.find(item => item.name == 'test_code').uid
    })
})

Cypress.Commands.add('getTestNameAndCodeTermUids', (dataset) => {
    cy.sendGetRequest(itemClassMetadataUrl(testNameUid, dataset)).then(response => {
        testNameTermUid = response.body.items[0].codelist_uid
    })
    cy.sendGetRequest(itemClassMetadataUrl(testCodeUid, dataset)).then(response => {
        testCodeTermUid = response.body.items[0].codelist_uid
    })
})

Cypress.Commands.add('getTermNameBySubmissionValue', (submissionValue, itemClass) => {
    let uid = itemClass == 'test_code' ?  testCodeTermUid : testNameTermUid
    cy.sendGetRequest(termsConnectedToClassUid(uid)).then(response => {
        return response.body.items.find(item => item.submission_value == submissionValue).sponsor_preferred_name
    })
})

Cypress.Commands.add('getUnitDefinitionName', (submissionValue) => {
    cy.sendGetRequest(unitDefinitionsUrl).then(response => {
        let unitData = response.body.items.find(item => JSON.stringify(item.unit_dimension).includes(`"submission_value":"${submissionValue}"`))
        return unitData.unit_dimension.term_name
    })
})

Cypress.Commands.add('getCategoryName', (submissionValue) => {
    cy.sendGetRequest(categoriesUrl).then(response => {
        return response.body.items.find(item => item.submission_value == submissionValue).sponsor_preferred_name
    })
})

Cypress.Commands.add('getSubCategoryName', (submissionValue) => {
    cy.sendGetRequest(subCategoriesUrl).then(response => {
        return response.body.items.find(item => item.submission_value == submissionValue).sponsor_preferred_name
    })
})

Cypress.Commands.add('getInstanceClassUid', (name) => {
    cy.sendGetRequest(dataSetsUrl).then(response => {
        instanceClassUid = response.body.find(item => item.name == name).uid
    })
})

Cypress.Commands.add('getItemClassType', (name) => {
    cy.sendGetRequest(insanceActivityItemClassesUrl(instanceClassUid)).then(response => {
        return response.body.find(item => item.name == name).data_type_name
    })
})