const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getCurrStudyUid, truncateTableValue, getCurrentDateFormatted } = require("../../support/helper_functions");

let device
let deviceAttributes

Given("[API] The selected study Auxiliary Devices are cleared", () => {
    return cy.clearStudyAuxiliaryDevices(getCurrStudyUid())
})

Given("[API] The auxiliary device exists for current study", () => {
    return cy.ensureStudyAuxiliaryDeviceExisits(getCurrStudyUid())
})

When('The user selects Auxiliary Device', () => {
    cy.getAuxiliaryDeviceTerms().then(response => {
        device = response.body.items[0]
        cy.getAuxiliaryDeviceAttributes(response.body.items[0].term_uid).then((attrResponse) => {
            deviceAttributes = attrResponse.body
            cy.selectVSelect('auxiliary-device-term', device.sponsor_preferred_name)
        })
    })
})

Then('The form contains auxiliary device details', () => {
    cy.get('[data-cy="auxiliary-device-submission-value"]').should('contain', device.sponsor_preferred_name)
    cy.get('[data-cy="auxiliary-device-sponsor-preferred-name"]').should('contain', device.sponsor_preferred_name)
    cy.get('[data-cy="auxiliary-device-nci-preferred-name"]').should('contain', device.nci_preferred_name)
    cy.get('[data-cy="auxiliary-device-definition"]').should('contain', device.definition)
    cy.get('[data-cy="auxiliary-device-algorithm"]').should('contain', deviceAttributes.algorithm)

})

Then('The auxiliary device is added to the table', () => {
    cy.checkRowByIndex(0, 'Device', device.sponsor_preferred_name)
    cy.checkRowByIndex(0, 'Submission value', device.submission_value)
    cy.checkRowByIndex(0, 'NCI preferred name', device.nci_preferred_name)
    cy.checkRowByIndex(0, 'Definition', device.definition)
    cy.checkRowByIndex(0, 'Algorithm', truncateTableValue(deviceAttributes.algorithm))

})

When('The user intercepts the auxiliary device delete request', () => {
    cy.intercept('DELETE', `**/study-auxiliary-devices/*`).as('auxDeviceDeleteRequest')
})

Then('The auxiliary device is removed from the table', () => {
    cy.wait('@auxDeviceDeleteRequest').then(request => expect(request.response.statusCode).to.eq(204))
    cy.get('table').should('contain', 'No data available')
})

When('The user intercepts audit trail request', () => {
    cy.intercept('GET', `**/audit-trail`).as('auditTrail')
})

Then('The audit trail panel for auxiliary devices is displaying relevant audit information', () => {
    cy.wait('@auditTrail').then(request => {
        cy.get('[data-cy="version-history-window"]').within(() => {
        request.response.body.slice(0, 5).forEach((item, index) => {
            cy.checkRowByIndex(index, '#', item.order)
            cy.checkRowByIndex(index, 'Device', item.auxiliary_device_name)
            cy.checkRowByIndex(index, 'Submission value', item.auxiliary_device_submission_value)
            cy.checkRowByIndex(index, 'NCI preferred name', item.auxiliary_device_nci_preferred_name)
            cy.checkRowByIndex(index, 'Definition', item.auxiliary_device_definition)
            cy.checkRowByIndex(index, 'Algorithm', item.auxiliary_device_algorithm)
            cy.checkRowByIndex(index, 'Change type', item.change_type)
            cy.checkRowByIndex(index, 'User', item.author_username)
            cy.checkRowByIndex(index, 'From', getCurrentDateFormatted(item.start_date))
            cy.checkRowByIndex(index, 'To', getCurrentDateFormatted(item.end_date))
        })
        })
    })
})
