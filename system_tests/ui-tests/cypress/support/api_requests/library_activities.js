export let group_uid, subgroup_uid, activity_uid, activityInstance_uid, group_name, requestedActivity_uid
const { getShortUniqueId } = require("../../support/helper_functions");
let groups_uids = []
let topicCode, adamParamCode, class_uid
const activityInstanceClassUrl = '/activity-instance-classes'
const baseUrl = '/concepts/activities'
const activityUrl = `${baseUrl}/activities`
const activityInstanceUrl = `${baseUrl}/activity-instances`
const activityGroupUrl = `${baseUrl}/activity-groups`
const activitySubGroupUrl = `${baseUrl}/activity-sub-groups`
const finalActivityGroupUrl = `${activityGroupUrl}?page_size=0&filters={"status":{"v":["Final"]}}`
const finalActivitySubGroupUrl = `${activitySubGroupUrl}?page_size=0&filters={"status":{"v":["Final"]}}`
const finalActivityInstacesUrl = '/concepts/activities/activity-instances?page_number=1&page_size=0&sort_by={"name":true}&filters={"status":{"v":["Final"]}}'
const finalActivitiesUrl = '/concepts/activities/activities?page_number=1&page_size=0&sort_by={"name":true}&filters={"status":{"v":["Final"]}}'
const activityInfoUrl = (activity_uid) => `${activityUrl}/${activity_uid}`
const activityInstanceInfoUrl = (activityInstance_uid) => `${activityInstanceUrl}/${activityInstance_uid}`
const activityInstanceAttributesUrl = (activityInstance_uid) => `${activityInstanceUrl}/${activityInstance_uid}/attributes`
const activityInstanceGroupingsUrl = (activityInstance_uid) => `${activityInstanceUrl}/${activityInstance_uid}/groupings`
const activityGroupInfoUrl = (group_uid) => `${activityGroupUrl}/${group_uid}`
const activitySubGroupInfoUrl = (subgroup_uid) => `${activitySubGroupUrl}/${subgroup_uid}`
const archiveActivityUrl = (activity_uid) => `${activityUrl}/${activity_uid}/archive`
const approveActivityUrl = (activity_uid) => `${activityUrl}/${activity_uid}/approvals`
const approveActivityInstanceAttributesUrl = (activityInstance_uid) => `${activityInstanceUrl}/${activityInstance_uid}/attributes/approvals`
const approveActivityInstanceGroupingsUrl = (activityInstance_uid) => `${activityInstanceUrl}/${activityInstance_uid}/groupings/approvals`
const approveActivityGroupUrl = (group_uid) => `${activityGroupUrl}/${group_uid}/approvals`
const approveActivitySubGroupUrl = (subgroup_uid) => `${activitySubGroupUrl}/${subgroup_uid}/approvals`
const activateActivityUrl = (activity_uid) => `${activityUrl}/${activity_uid}/activations`
const activateActivityInstanceUrl = (activityInstance_uid) => `${activityInstanceUrl}/${activityInstance_uid}/activations`
const activateActivityGroupUrl = (group_uid) => `${activityGroupUrl}/${group_uid}/activations`
const activateActivitySubGroupUrl = (subgroup_uid) => `${activitySubGroupUrl}/${subgroup_uid}/activations`
const newVersionActivityUrl = (activity_uid) => `${activityUrl}/${activity_uid}/versions`
const newVersionActivityInstanceAttributesUrl = (activityInstance_uid) => `${activityInstanceUrl}/${activityInstance_uid}/attributes/versions`
const newVersionActivityInstanceGroupingsUrl = (activityInstance_uid) => `${activityInstanceUrl}/${activityInstance_uid}/groupings/versions`
const newVersionActivityGroupUrl = (group_uid) => `${activityGroupUrl}/${group_uid}/versions`
const newVersionActivitySubGroupUrl = (subgroup_uid) => `${activitySubGroupUrl}/${subgroup_uid}/versions`

Cypress.Commands.add('getActivityDataByName', (name, group, subgroup) => {
    cy.sendGetRequest(finalActivitiesUrl).then(response => {
        let activityList = response.body.items.filter(item => item.name == name)
        let activityGroupings = activityList[0].activity_groupings.filter(item => item.activity_group_name == group)
        activityGroupings = activityGroupings.filter(item => item.activity_subgroup_name == subgroup)
        group_uid = activityGroupings[0].activity_group_uid
        subgroup_uid = activityGroupings[0].activity_subgroup_uid
        activity_uid = activityList[0].uid
    })
})

Cypress.Commands.add('getInstanceUidByName', (name) => {
    cy.sendGetRequest(finalActivityInstacesUrl).then(response => {
        activityInstance_uid = response.body.items.find(item => item.name == name).uid
    })
})

Cypress.Commands.add('createActivity', (customName = '', isDataCollected = true, isMultipleSelectionAllowed = true) => {
    cy.sendPostRequest(activityUrl, createActivityBody(customName, isDataCollected, isMultipleSelectionAllowed)).then(response => activity_uid = response.body.uid)
})

Cypress.Commands.add('updateActivity', (name) => cy.sendUpdateRequest('PUT', activityInfoUrl(activity_uid), updateActivityBody(name)))

Cypress.Commands.add('archiveRequestedActivity', () => cy.sendPostRequest(archiveActivityUrl(requestedActivity_uid), {}))

Cypress.Commands.add('createActivityInstance', (customName = '', isDataSharing = false, isRequiredForActivity = false, isDefaultForActivity = false) => {
    cy.sendPostRequest(activityInstanceUrl, createActivityInstanceBody(customName, isDataSharing, isRequiredForActivity, isDefaultForActivity)).then((response) => {
        activityInstance_uid = response.body.uid
    })
})

Cypress.Commands.add('updateActivityInstanceAttributes', (name) => cy.sendUpdateRequest('PATCH', activityInstanceAttributesUrl(activityInstance_uid), updateActivityInstanceNameBody(name)))

Cypress.Commands.add('createGroup', (customName = '') => {
    cy.sendPostRequest(activityGroupUrl, createGroupBody(customName)).then((response) => {
        group_uid = response.body.uid
        group_name = response.body.name
    })
})

Cypress.Commands.add('createTwoGroups', () => {
    cy.sendPostRequest(activityGroupUrl, createGroupBody()).then(response => groups_uids.push(response.body.uid)).then(() => {
        cy.sendPostRequest(activityGroupUrl, createGroupBody()).then(response => groups_uids.push(response.body.uid))
    })
})

Cypress.Commands.add('createSubGroup', (customName = '') => {
    cy.sendPostRequest(activitySubGroupUrl, createSubGroupBody(customName)).then(response => subgroup_uid = response.body.uid)
})

Cypress.Commands.add('createSubGroupWithTwoGroups', () => {
    cy.sendPostRequest(activitySubGroupUrl, createSubGroupWithGrouBody()).then(response => subgroup_uid = response.body.uid)
})

Cypress.Commands.add('createRequestedActivity', (submitted, customName = '') => {
    cy.sendPostRequest(activityUrl, createRequestedActivityBody(submitted, customName)).then(response => requestedActivity_uid = response.body.uid)
})

Cypress.Commands.add('approveActivity', () => cy.sendPostRequest(approveActivityUrl(activity_uid), {}))

Cypress.Commands.add('approveRequestedActivity', () => cy.sendPostRequest(approveActivityUrl(requestedActivity_uid), {}))

Cypress.Commands.add('approveActivityInstance', () => {
    cy.sendPostRequest(approveActivityInstanceAttributesUrl(activityInstance_uid), {})
    cy.sendPostRequest(approveActivityInstanceGroupingsUrl(activityInstance_uid), {})
})

Cypress.Commands.add('approveGroup', () => cy.sendPostRequest(approveActivityGroupUrl(group_uid), {}))

Cypress.Commands.add('approveTwoGroups', () => groups_uids.forEach(uid => cy.sendPostRequest(approveActivityGroupUrl(uid, {}))))

Cypress.Commands.add('approveSubGroup', () => cy.sendPostRequest(approveActivitySubGroupUrl(subgroup_uid), {}))

Cypress.Commands.add('activityNewVersion', () => cy.sendPostRequest(newVersionActivityUrl(activity_uid), {}))

Cypress.Commands.add('activityInstanceNewVersion', () => {
    cy.sendPostRequest(newVersionActivityInstanceAttributesUrl(activityInstance_uid), {})
    cy.sendPostRequest(newVersionActivityInstanceGroupingsUrl(activityInstance_uid), {})
})

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

Cypress.Commands.add('getGroupNameFromListByUid', () => cy.getName(activityGroupInfoUrl(groups_uids[0])))

Cypress.Commands.add('getSubGroupNameByUid', () => cy.getName(activitySubGroupInfoUrl(subgroup_uid)))

Cypress.Commands.add('getRequestedActivityNameByUid', () => cy.getName(activityInfoUrl(requestedActivity_uid)))

Cypress.Commands.add('getName', (url) => cy.sendGetRequest(url).then((response) => { return response.body.name }))

Cypress.Commands.add('getFinalGroupUid', () => cy.sendGetRequest(finalActivityGroupUrl).then((response) => { group_uid = response.body.items[0].uid }))

Cypress.Commands.add('getFinalSubGroupUid', () => cy.sendGetRequest(finalActivitySubGroupUrl).then(response => subgroup_uid = response.body.items[0].uid))

const createActivityBody = (customName = '', isDataCollected = true, isMultipleSelectionAllowed = true) => {
    const name = customName === '' ? `API_Activity${getShortUniqueId()}` : customName
    return {
        abbreviation: "abb",
        activity_groupings: [
            {
                activity_group_uid: group_uid,
                activity_subgroup_uid: subgroup_uid
            }
        ],
        definition: "def",
        nci_concept_id: "nci id",
        nci_concept_name: "nci name",
        is_data_collected: isDataCollected,
        is_multiple_selection_allowed: isMultipleSelectionAllowed,
        library_name: "Sponsor",
        name: name,
        name_sentence_case: name.toLowerCase(),
        synonyms: [`${getShortUniqueId()}`],
    }
}

const updateActivityBody = (name) => {
    return {
        abbreviation: "abb",
        activity_groupings: [
            {
                activity_group_uid: group_uid,
                activity_subgroup_uid: subgroup_uid
            }
        ],
        change_description: "testing",
        definition: "def",
        nci_concept_id: "nci id",
        nci_concept_name: "nci name",
        is_data_collected: true,
        is_multiple_selection_allowed: true,
        library_name: "Sponsor",
        name: name,
        name_sentence_case: name.toLowerCase(),
        synonyms: [`${getShortUniqueId()}`],
    }
}

const createActivityInstanceBody = (customName = '', isDataSharing = false, isRequiredForActivity = false, isDefaultForActivity = false) => {
    const name = customName === '' ? `API_ActivityInstance${getShortUniqueId()}` : customName
    topicCode = `${getShortUniqueId()}`
    adamParamCode = `${getShortUniqueId()}`

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
        topic_code: topicCode,
        adam_param_code: adamParamCode,
        is_data_sharing: isDataSharing,
        is_default_selected_for_activity: isDefaultForActivity,
        is_required_for_activity: isRequiredForActivity,
        definition: "api",
        library_name: "Sponsor",
        activities: [null]
    }
}

const updateActivityInstanceNameBody = (name) => {
    return {
        change_description: "testing",
        name: name,
        name_sentence_case: name.toLowerCase(),
    }
}

const updateActivityInstanceGroupingsBody = () => {
    return {
        activity_groupings: [
            {
                activity_uid: activity_uid,
                activity_group_uid: group_uid,
                activity_subgroup_uid: subgroup_uid
            }
        ],
        change_description: "testing",
    }
}

const createGroupBody = (customName = '') => {
    const name = customName === '' ? `API_Group${getShortUniqueId()}` : customName
    return {
        abbreviation: "abb",
        definition: "def",
        library_name: "Sponsor",
        name: name,
        name_sentence_case: name.toLowerCase()
    }
}

const createSubGroupBody = (customName = '') => {
    const name = customName === '' ? `API_SubGroup${getShortUniqueId()}` : customName
    return {
        definition: "def",
        library_name: "Sponsor",
        name: name,
        name_sentence_case: name.toLowerCase(),
    }
}

const createSubGroupWithGrouBody = () => {
    const name = `API_SubGroup${getShortUniqueId()}`
    return {
        definition: "def",
        library_name: "Sponsor",
        name: name,
        name_sentence_case: name.toLowerCase(),
        activity_groups: groups_uids
    }
}

const createRequestedActivityBody = (isRequestFinal, customName = '') => {
    const name = customName === '' ? `API_RequestedActivity${getShortUniqueId()}` : customName
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
        is_request_final: isRequestFinal
    }
}
