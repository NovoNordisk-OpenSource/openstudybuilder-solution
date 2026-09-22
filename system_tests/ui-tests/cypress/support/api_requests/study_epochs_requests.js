import { getShortUniqueId } from "../helper_functions"

const availableEpochsUrl = '/epochs/allowed-configs'
const studyEpochsUrl = (study_uid) =>  `/studies/${study_uid}/study-epochs`
const studyEpochUrl = (study_uid, epoch_uid) =>  `/studies/${study_uid}/study-epochs/${epoch_uid}`
const studyEpochsPreviewUrl = (study_uid) =>  `/studies/${study_uid}/study-epochs/preview`
const timeUnitUrl = '/concepts/unit-definitions?subset=Study+Time&sort_by[conversion_factor_to_master]=true&page_size=0'
let epochType, epochSubType, epochTerm, study_epochs_uids
export let epoch_uid

Cypress.Commands.add('getEpochTypeAndSubType', (epoch_type_name, epoch_subtype_name) => {
    cy.sendGetRequest(availableEpochsUrl).then((response) => {
          epochSubType = response.body
            .find(epoch => epoch.type_name == epoch_type_name && epoch.subtype_name == epoch_subtype_name).subtype
          epochType = response.body
            .find(epoch => epoch.type_name == epoch_type_name && epoch.subtype_name == epoch_subtype_name).type
    })
})

Cypress.Commands.add('createEpoch', (study_uid) => {
  cy.sendGetRequest(studyEpochsUrl(study_uid)).then((response) => {
    if (!response.body.items.find(item => item.epoch_subtype_ctterm.term_uid == epochSubType)) {
        cy.sendPostRequest(studyEpochsPreviewUrl(study_uid), epochPreviewBody(study_uid))
          .then(response => epochTerm = response.body.epoch)
            .then(() => cy.sendPostRequest(studyEpochsUrl(study_uid), createEpochBody(study_uid))
                .then(response => epoch_uid = response.body.uid))
    } else {
      epoch_uid = response.body.items[0].uid
    }
  })
})

Cypress.Commands.add('createEpochWithLagTimes', (study_uid, description) => {
    cy.getEpochTypeAndSubType('Post Treatment', 'Elimination')
    cy.sendGetRequest(timeUnitUrl).then((response) => {
        const daysUnitUid = response.body.items.find(term => term.name == 'days').uid
        const weeksUnitUid = response.body.items.find(term => term.name == 'weeks').uid
        cy.sendPostRequest(studyEpochsPreviewUrl(study_uid), epochPreviewBody(study_uid))
          .then(response => epochTerm = response.body.epoch)
          .then(() => cy.sendPostRequest(studyEpochsUrl(study_uid), {
            ...createEpochBody(study_uid, description),
            ae_lag_time: 5,
            ae_lag_time_unit_uid: daysUnitUid,
            hypo_lag_time: 2,
            hypo_lag_time_unit_uid: weeksUnitUid,
            ce_lag_time: 7,
            ce_lag_time_unit_uid: daysUnitUid,
          }))
    })
})

Cypress.Commands.add('getEpochsUids', (studyUid) => {
    study_epochs_uids = []
    cy.sendGetRequest(studyEpochsUrl(studyUid)).then(response => response.body.items.forEach(item => study_epochs_uids.push(item.uid)))
})

Cypress.Commands.add('deleteEpochs', (studyUid) => study_epochs_uids.forEach(uid => cy.sendDeleteRequest(studyEpochUrl(studyUid, uid))))

const createEpochBody = (study_uid, description = `DESC${getShortUniqueId()}`) => {
  return {
    "epoch_type": epochType,
    "epoch": epochTerm,
    "epoch_subtype": epochSubType,
    "start_rule": "C1",
    "end_rule": "C5",
    "description": description,
    "color_hash": "#1B5E20",
    "study_uid": study_uid
  }
}

const epochPreviewBody = (study_uid) => {
  return {
    "study_uid": study_uid,
    "epoch_subtype": epochSubType
  }
}