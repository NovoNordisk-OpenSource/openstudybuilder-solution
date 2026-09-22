import { getCurrStudyUid, getShortUniqueId } from "../helper_functions"

let soaGroup_uid, footnotes_uid
const studyActivityUrl = (study_uid, study_activity_uid) => `/studies/${study_uid}/study-activities/${study_activity_uid}`
const studyActivitiesUrl = (study_uid) => `/studies/${study_uid}/study-activities?page_number=1&page_size=0`
const studyActivityBatchUrl = (study_uid) => `/studies/${study_uid}/study-activities/batch`
const flowchartGroupUrl = () => '/ct/codelists/terms?page_size=100&codelist_submission_value=FLWCRTGRP'
const activityWithActivityGroupFilterUrl = (activity_group_name) => `/concepts/activities/activities?library_name=Sponsor&activity_group_names%5B%5D=${activity_group_name}&filters=%7B%22status%22:%7B%22v%22:%5B%22Final%22%5D%7D%7D`
const studyFootnotesUrl = (study_uid) => `/studies/${study_uid}/study-soa-footnotes?page_number=1&page_size=0`
const studyFootnoteUrl = (study_uid, footnote_uid) => `/studies/${study_uid}/study-soa-footnotes/${footnote_uid}`
const studyFootnoteTermUrl = () => '/ct/codelists/terms?page_size=100&sort_by={"sponsor_preferred_name":true}&codelist_submission_value=FTNTTP'
const addFootnoteToStudyUrl = (study_uid) => `/studies/${study_uid}/study-soa-footnotes?create_footnote=true`
const addFootnoteTemplateUrl = () => '/footnote-templates'
const approveFootnoteTemplateUrl = (foonote_uid) => `/footnote-templates/${foonote_uid}/approvals`

Cypress.Commands.add('deleteAllFootnotesFromStudy', (study_uid) => footnotes_uid.forEach(uid => cy.sendDeleteRequest(studyFootnoteUrl(study_uid, uid))))

Cypress.Commands.add('deleteActivityFromStudy', (study_uid, activity_uid) => cy.sendDeleteRequest(studyActivityUrl(study_uid, activity_uid)))

Cypress.Commands.add('getExistingStudyActivities', (study_uid) => {
  cy.sendGetRequest(studyActivitiesUrl(study_uid)).then((response) => {
    let uid_array = []
    response.body.items.forEach(item => uid_array.push(item.study_activity_uid))
    return uid_array
  })
})

Cypress.Commands.add('getExistingStudyFootnotes', (study_uid) => {
  cy.sendGetRequest(studyFootnotesUrl(study_uid)).then((response) => {
    footnotes_uid = []
    response.body.items.forEach(item => footnotes_uid.push(item.uid))
  })
})

Cypress.Commands.add('addActivityToStudy', (study_uid, activity_uid, activityGroup_uid, activitySubgroup_uid) => {
  cy.sendPostRequest(studyActivityBatchUrl(study_uid), addActivityToStudyBody(soaGroup_uid, activity_uid, activityGroup_uid, activitySubgroup_uid))
})

Cypress.Commands.add('getSoaGroupUid', (soaGroup_name) => {
  cy.sendGetRequest(flowchartGroupUrl()).then((response) => {
    soaGroup_uid = response.body.items.find(item => item.sponsor_preferred_name == soaGroup_name).term_uid
  })
})

Cypress.Commands.add('addActivityToCurrentStudyFromActivityGroup', (soa_group, group_name) => {
  let activity_uid
  cy.getSoaGroupUid(soa_group)
  cy.sendGetRequest(activityWithActivityGroupFilterUrl(group_name)).then((response) => {
    activity_uid = response.body.items[0].uid
    let activityGroup_uid = response.body.items[0].activity_groupings[0].activity_group_uid
    let activitySubgroup_uid = response.body.items[0].activity_groupings[0].activity_subgroup_uid
    cy.addActivityToStudy(getCurrStudyUid(), activity_uid, activityGroup_uid, activitySubgroup_uid)
  })
  return activity_uid
})

Cypress.Commands.add('addFootnoteToStudy', (study_uid, footnoteText) => {
  cy.sendGetRequest(studyFootnoteTermUrl()).then(termResponse => {
    cy.sendPostRequest(addFootnoteTemplateUrl(), addFootnoteTemplateBody(study_uid, footnoteText, termResponse.body.items[0].term_uid)).then(response => {
      let footnote_uid = response.body.uid
      cy.sendPostRequest(approveFootnoteTemplateUrl(footnote_uid), {}).then(() => {
        cy.sendPostRequest(addFootnoteToStudyUrl(study_uid), addFootnoteToStudyBody(footnote_uid))
      })
    })
  })
})

const addActivityToStudyBody = (soaGroup_uid, activity_uid, activityGroup_uid, activitySubgroup_uid) => {
  return [
    {
      "method": "POST",
      "content": {
        "soa_group_term_uid": soaGroup_uid,
        "activity_uid": activity_uid,
        "order": null,
        "activity_group_uid": activityGroup_uid,
        "activity_subgroup_uid": activitySubgroup_uid
      }
    }
  ]
}

const addFootnoteToStudyBody = (footnote_template_uid) => {
  return {
      "footnote_data": {
          "footnote_template_uid": footnote_template_uid,
          "parameter_terms": [],
          "library_name": "User Defined"
      },
      "referenced_items": []
  }
}

const addFootnoteTemplateBody = (studyUid, text, term) => {
  return {
    "name": `<p>${text} ${getShortUniqueId()}</p>`,
    "studyUid": studyUid,
    "library_name": "User Defined",
    "type_uid": term
  }
}