import { generateShortUniqueName } from "../helper_functions"
import { arm_uid } from "./study_arm_requests"
import { branch_uid } from "./study_branch_requests"
const { getShortUniqueId } = require("../../support/helper_functions");

let study_cohorts_uids
const createCohortUrl = (studyUid) => `/studies/${studyUid}/study-cohorts`
const studyCohortsUrl = (studyUid) => `/studies/${studyUid}/study-cohorts?page_number=1&page_size=0&total_count=true&study_uid=${studyUid}`
const studyCohortUrl = (studyUid, cohortUid) => `/studies/${studyUid}/study-cohorts/${cohortUid}`

Cypress.Commands.add('createCohort', (study_uid) => cy.sendPostRequest(createCohortUrl(study_uid), createCohortBody(arm_uid, branch_uid)))

Cypress.Commands.add('getCohortsUids', (studyUid) => {
    study_cohorts_uids = []
    cy.sendGetRequest(studyCohortsUrl(studyUid)).then(response => response.body.items.forEach(item => study_cohorts_uids.push(item.cohort_uid)))
})

Cypress.Commands.add('deleteCohorts', (studyUid) => study_cohorts_uids.forEach(uid => cy.sendDeleteRequest(studyCohortUrl(studyUid, uid))))

const createCohortBody = (armUid, branchUid) => {
    let cohortName = `${generateShortUniqueName('Cohort')}`
    return {
        "arm_uids": [
            armUid
        ],
        "branch_arm_uids": [
            branchUid
        ],
        "name": cohortName,
        "short_name": cohortName,
        "code": `Code${getShortUniqueId()}`,
        "number_of_subjects": 1,
        "description": 'TestCohort'
    }
}
