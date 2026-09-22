const studyDiseaseMilestonesUrl = (study_uid) => `/studies/${study_uid}/study-disease-milestones?page_number=1&page_size=10&total_count=true`
const studyDiseaseMilestoneUrl = (study_uid) => `/studies/${study_uid}/study-disease-milestones`

Cypress.Commands.add('checkAndCreateDiseaseMilestone', (study_uid) => {
    cy.sendGetRequest(studyDiseaseMilestonesUrl(study_uid)).then((resp) => {
        if (resp.body.total == 0) {
            cy.sendPostRequest(studyDiseaseMilestoneUrl(study_uid), createDiseaseMilestoneBody(study_uid))
            cy.reload()
        }
    })
})

const createDiseaseMilestoneBody = (study_uid) => {
    return {
        "disease_milestone_type": "CTTerm_000215",
        "study_uid": study_uid,
        "repetition_indicator": false
    }
}