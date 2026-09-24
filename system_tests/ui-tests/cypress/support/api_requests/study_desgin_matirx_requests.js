import { arm_uid } from "./study_arm_requests"
import { branch_uid } from "./study_branch_requests"
import { epoch_uid } from "./study_epochs_requests"

const createDesignMatrixRequest = (studyUid) => `/studies/${studyUid}/study-design-cells/batch` 

Cypress.Commands.add('createDesignMatrix', (study_uid, element_uid) => {
    cy.sendPostRequest(createDesignMatrixRequest(study_uid), createDesignMatrixBody(element_uid))
})

const createDesignMatrixBody = (element_uid) => {
    return [
        {
            "method": "POST",
            "content": {
                "study_element_uid": element_uid,
                "study_arm_uid": null,
                "study_epoch_uid": epoch_uid,
                "study_branch_arm_uid": branch_uid,
                "transition_rule": "e2e transition"
            }
        }
    ]
}
