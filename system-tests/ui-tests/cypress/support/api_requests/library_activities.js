let activity_uid, activityInstance_uid, class_uid, group_uid, subgroup_uid, requestedActivity_uid
const activityInstanceClassUrl = '/activity-instance-classes'
const baseUrl = '/concepts/activities'
const activityUrl = `${baseUrl}/activities`
const activityInstanceUrl = `${baseUrl}/activity-instances`
const activityGroupUrl = `${baseUrl}/activity-groups`
const activitySubGroupUrl = `${baseUrl}/activity-sub-groups`
const finalActivityGroupUrl = `${activityGroupUrl}?page_size=0&filters={"status":{"v":["Final"]}}`
const finalActivitySubGroupUrl = `${activitySubGroupUrl}?page_size=0&filters={"status":{"v":["Final"]}}`
const activityInfoUrl = (activity_uid) => `${activityUrl}/${activity_uid}`
const activityInstanceInfoUrl = (activityInstance_uid) => `${activityInstanceUrl}/${activityInstance_uid}`
const activityGroupInfoUrl = (group_uid) => `${activityGroupUrl}/${group_uid}`
const activitySubGroupInfoUrl = (subgroup_uid) => `${activitySubGroupUrl}/${subgroup_uid}`
const approveActivityUrl = (activity_uid) => `${activityUrl}/${activity_uid}/approvals`
const approveActivityInstanceUrl = (activityInstance_uid) => `${activityInstanceUrl}/${activityInstance_uid}/approvals`
const approveActivityGroupUrl = (group_uid) => `${activityGroupUrl}/${group_uid}/approvals`
const approveActivitySubGroupUrl = (subgroup_uid) => `${activitySubGroupUrl}/${subgroup_uid}/approvals`
const activateActivityUrl = (activity_uid) => `${activityUrl}/${activity_uid}/activations`
const activateActivityInstanceUrl = (activityInstance_uid) => `${activityInstanceUrl}/${activityInstance_uid}/activations`
const activateActivityGroupUrl = (group_uid) => `${activityGroupUrl}/${group_uid}/activations`
const activateActivitySubGroupUrl = (subgroup_uid) =>`${activitySubGroupUrl}/${subgroup_uid}/activations`
const newVersionActivityGroupUrl = (group_uid) =>`${activityGroupUrl}/${group_uid}/versions`
const newVersionActivitySubGroupUrl = (subgroup_uid) =>`${activitySubGroupUrl}/${subgroup_uid}/versions`

Cypress.Commands.add('createActivity', (customName = '') => {
    cy.sendPostRequest(activityUrl, createActivityBody(customName)).then(response => activity_uid = response.body.uid)
})

Cypress.Commands.add('createActivityInstance', (customName = '') => {
    cy.sendPostRequest(activityInstanceUrl, createActivityInstanceBody(customName)).then(response => activityInstance_uid = response.body.uid)
})

Cypress.Commands.add('createGroup', (customName = '') => {
    cy.sendPostRequest(activityGroupUrl, createGroupBody(customName)).then(response => group_uid = response.body.uid)
})

Cypress.Commands.add('createSubGroup', (customName = '') => {
    cy.sendPostRequest(activitySubGroupUrl, createSubGroupBody(customName, group_uid)).then(response => subgroup_uid = response.body.uid)
})

Cypress.Commands.add('createRequestedActivity', (customName = '') => {
    cy.sendPostRequest(activityUrl, createRequestedActivityBody(customName)).then(response => requestedActivity_uid = response.body.uid)
})

Cypress.Commands.add('approveActivity', () => cy.sendPostRequest(approveActivityUrl(activity_uid), {}))

Cypress.Commands.add('approveActivityInstance', () => cy.sendPostRequest(approveActivityInstanceUrl(activityInstance_uid), {}))

Cypress.Commands.add('approveGroup', () => cy.sendPostRequest(approveActivityGroupUrl(group_uid), {}))

Cypress.Commands.add('approveSubGroup', () => cy.sendPostRequest(approveActivitySubGroupUrl(subgroup_uid), {}))

Cypress.Commands.add('approveRequestedActivity', () => cy.sendPostRequest(approveActivityUrl(requestedActivity_uid), {}))

Cypress.Commands.add('groupNewVersion', () => cy.sendPostRequest(newVersionActivityGroupUrl(group_uid), {}))

Cypress.Commands.add('subGroupNewVersion', () => cy.sendPostRequest(newVersionActivitySubGroupUrl(subgroup_uid), {}))

Cypress.Commands.add('inactivateActivity', () => cy.sendDeleteRequest(activateActivityUrl(activity_uid), {}))

Cypress.Commands.add('inactivateActivityInstance', () => cy.sendDeleteRequest(activateActivityInstanceUrl(activityInstance_uid), {}))

Cypress.Commands.add('inactivateGroup', () => cy.sendDeleteRequest(activateActivityGroupUrl(group_uid), {}))

Cypress.Commands.add('inactivateSubGroup', () => cy.sendDeleteRequest(activateActivitySubGroupUrl(subgroup_uid), {}))

Cypress.Commands.add('inactivateRequestedActivity', () => cy.sendDeleteRequest(activateActivityUrl(requestedActivity_uid), {}))

Cypress.Commands.add('reactivateActivity', () => cy.sendPostRequest(activateActivityUrl(activity_uid), {}))

Cypress.Commands.add('reactivateGroup', () => cy.sendPostRequest(activateActivityGroupUrl(group_uid), {}))

Cypress.Commands.add('reactivateSubGroup', () => cy.sendPostRequest(activateActivitySubGroupUrl(subgroup_uid), {}))

Cypress.Commands.add('getActivitySynonymByUid', () => cy.sendGetRequest(activityInfoUrl(activity_uid)).then(response => { return response.body.synonyms[0] }))

Cypress.Commands.add('getActivityInstanceTopicCodeByUid', () => cy.sendGetRequest(activityInstanceInfoUrl(activityInstance_uid)).then(response => { return response.body.topic_code }))

Cypress.Commands.add('getClassUid', () => cy.sendGetRequest(activityInstanceClassUrl).then((response) => { class_uid = response.body.items[0].uid }))

Cypress.Commands.add('getActivityNameByUid', () => cy.getName(activityInfoUrl(activity_uid)))

Cypress.Commands.add('getActivityInstanceNameByUid', () => cy.getName(activityInstanceInfoUrl(activityInstance_uid)))

Cypress.Commands.add('getGroupNameByUid', () => cy.getName(activityGroupInfoUrl(group_uid)))

Cypress.Commands.add('getSubGroupNameByUid', () => cy.getName(activitySubGroupInfoUrl(subgroup_uid)))

Cypress.Commands.add('getRequestedActivityNameByUid', () => cy.getName(activityInfoUrl(requestedActivity_uid)))

Cypress.Commands.add('getName', (url) => cy.sendGetRequest(url).then((response) => { return response.body.name }))

Cypress.Commands.add('getFinalGroupUid', () => cy.sendGetRequest(finalActivityGroupUrl).then((response) => { group_uid = response.body.items[0].uid }))

Cypress.Commands.add('getFinalSubGroupUid', () => {
    cy.sendGetRequest(finalActivitySubGroupUrl).then((response) => {
        subgroup_uid = response.body.items
            .find(subgroup => subgroup.activity_groups
            .find(group => group.uid == group_uid))
            .uid
    })
})


const createActivityBody = (customName = '') => {
    const name = customName === '' ? `API_Activity${Date.now()}` : customName
    return {
        abbreviation: "abb",
        activity_groupings: [
            {
                activity_group_uid: group_uid,
                activity_subgroup_uid: subgroup_uid
            }
        ],
        definition: "def",
        is_data_collected: true,
        library_name: "Sponsor",
        name: name,
        name_sentence_case: name.toLowerCase(),
        synonyms: [`${Date.now()}`],
    }
}

const createActivityInstanceBody = (customName = '') => {
    const name = customName === '' ? `API_ActivityInstance${Date.now()}` : customName
    return {
        activity_groupings: [
          {
            activity_uid: activity_uid,
            activity_group_uid: group_uid,
            activity_subgroup_uid: subgroup_uid
          }
        ],
        activity_instance_class_uid: class_uid,
        name: name,
        name_sentence_case: name.toLowerCase(),
        topic_code: `${Date.now()}`,
        definition: "api",
        library_name: "Sponsor",
        activities: [null]
      }
}

const createGroupBody = (customName = '') => {
    const name = customName === '' ? `API_Group${Date.now()}` : customName
    return {
        abbreviation: "abb",
        definition: "def",
        library_name: "Sponsor",
        name: name,
        name_sentence_case: name.toLowerCase()
    }
}

const createSubGroupBody = (customName = '', group_uid) => {
    const name = customName === '' ? `API_SubGroup${Date.now()}` : customName
    return {
        definition: "def",
        library_name: "Sponsor",
        name: name,
        name_sentence_case: name.toLowerCase(),
        activity_groups: [group_uid]
    }
}

const createRequestedActivityBody = (customName = '') => {
    const name = customName === '' ? `API_RequestedActivity${Date.now()}` : customName
    return {
        activity_groupings: [
          {
            activity_group_uid: group_uid,
            activity_subgroup_uid: subgroup_uid
          }
        ],
        name: name,
        name_sentence_case: name.toLowerCase(),
        request_rationale: "test",
        library_name: "Requested",
        is_request_final: true
    }
}