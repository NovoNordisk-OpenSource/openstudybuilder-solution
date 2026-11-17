const auxiliaryDevicesUrl = studyUid => `/studies/${studyUid}/study-auxiliary-devices`
const deviceTermsUrl = '/ct/codelists/terms?page_size=0&sort_by=%7B%22sponsor_preferred_name%22%3Atrue%7D&codelist_submission_value=AUXDEV'

Cypress.Commands.add('getAuxiliaryDeviceTerms', () => {
    cy.sendGetRequest(deviceTermsUrl)
})

Cypress.Commands.add('getAuxiliaryDeviceAttributes', termUid => {
    cy.sendGetRequest(`/ct/terms/${encodeURIComponent(termUid)}/attributes?status=Final`)
})

Cypress.Commands.add('clearStudyAuxiliaryDevices', studyUid => {
    cy.sendGetRequest(`${auxiliaryDevicesUrl(studyUid)}?page_size=0`).then(response => {
        response.body.items.forEach(device => cy.sendDeleteRequest(`${auxiliaryDevicesUrl(studyUid)}/${encodeURIComponent(device.uid)}`))

    })
})

Cypress.Commands.add('ensureStudyAuxiliaryDeviceExisits', studyUid => {
    cy.sendGetRequest(`${auxiliaryDevicesUrl(studyUid)}?page_size=0`).then(response => {
        if (response.body.items.length === 0) {
            cy.getAuxiliaryDeviceTerms().then(terms => {
                cy.sendPostRequest(auxiliaryDevicesUrl(studyUid), { auxiliary_device_term_uid: terms.body.items[0].term_uid })
            })
        }
    })
})
