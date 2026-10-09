
let testCodeCodeListUid, testNameCodeListUid
const trialSummaryParameterCodeListUrl = '/ct/codelists?page_number=1&page_size=10&total_count=true&filters={"*":{"v":["trial+summary+parameter"]}}&match_whole_words=false'
const createTermUrl = '/ct/terms'

Cypress.Commands.add('createTrialSummaryParameter', (name, testCodeSubmissionValue, testNameSubmissionValue, definition) => {
    cy.getTrialSummaryParametersCodeLists().then(() => cy.sendPostRequest(createTermUrl, createTrialSummaryParameterBody(name, testCodeSubmissionValue, testNameSubmissionValue, definition)))
})
    
Cypress.Commands.add('getTrialSummaryParametersCodeLists', () => {
    cy.sendGetRequest(trialSummaryParameterCodeListUrl).then(response => {
        testCodeCodeListUid = response.body.items.filter(item => item.name.name == 'Trial Summary Parameter Test Code')[0].codelist_uid
        testNameCodeListUid = response.body.items.filter(item => item.name.name == 'Trial Summary Parameter Test Name')[0].codelist_uid
    })
})

const createTrialSummaryParameterBody = (name, testCodeSubmissionValue, testNameSubmissionValue, definition) => {
  return {
    "ts_parameter":
    {
        "required_level": "Required",
        "response_codelist_uid": null,
        "semantic_data_type_uid": null,
        "valid_null_flavor_term_uids": []
    },
    "library_name": "Sponsor",
    "sponsor_preferred_name": name,
    "sponsor_preferred_name_sentence_case": name.toLowerCase(),
    "submission_value": testCodeSubmissionValue,
    "submission_value_test_name": testNameSubmissionValue,
    "definition": definition,
    "catalogue_names": [
        "SDTM CT"
    ],
    "codelists":[
        {
            "codelist_uid": testCodeCodeListUid,
            "submission_value": testCodeSubmissionValue
        },
        {
            "codelist_uid": testNameCodeListUid,
            "submission_value": testNameSubmissionValue
        }
    ]}
}
