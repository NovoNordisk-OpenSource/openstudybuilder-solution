import { selectedSupplierValue } from "./study_manage_data_suppliers_steps";
import { activity_activity } from "./study_define_activities_activities_steps";

const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

export let studyActivityInstance
let originType, originSource

Then('Important is set to {string} in the Study Activity Instance table', (expectedValue) => cy.checkRowByIndex(0, 'Important', expectedValue))

Then('Important is set to empty string in the Study Activity Instance table', () => cy.checkRowByIndex(0, 'Important', null))

When('Library Instance Status is set to {string} in the edition form', (status) => {
    cy.get('.v-overlay table thead th').each((header, index) => {
        if (header.text() == 'Library Instance Status') {
            cy.get('.v-overlay table tbody tr td').eq(index).should('not.be.empty').invoke('text').then(text => status = text)
        }
    })
})

When('Origin Type and Origin Source are automatically populated in the edition form', () => {
    cy.get('.v-overlay table thead th').each((header, index) => {
        if (header.text() == 'Origin Source') {
            cy.get('.v-overlay table tbody tr td').eq(index).should('not.be.empty').invoke('text').then(text => originSource = text)
        }
        if (header.text() == 'Origin Type') {
            cy.get('.v-overlay table tbody tr td').eq(index).should('not.be.empty').invoke('text').then(text => originType = text)
        }
    })
})

When('Origin Type and Origin Source are automatically populated in the edition mode', () => {
    cy.get('table thead th').each((header, index) => {
        if (header.text() == 'Origin Source') {
            cy.get('table tbody tr td').eq(index).should('not.be.empty').invoke('text').then(text => originSource = text)
        }
        if (header.text() == 'Origin Type') {
            cy.get('table tbody tr td').eq(index).should('not.be.empty').invoke('text').then(text => originType = text)
        }
    })
})

When('{string} dropdown is activated in the edition form', (headerName) => {
    cy.get('.v-overlay table thead th').each((header, index) => {
        if (header.text() == headerName) {
            cy.get('.v-overlay table tbody tr td').eq(index).find('[role="combobox"] .v-field__input').click()
            return false
        }
    })
})

When('{string} dropdown is activated in the edition mode', (headerName) => {
    cy.get('table thead th').each((header, index) => {
        if (header.text() == headerName) {
            cy.get('table tbody tr td').eq(index).find('[role="combobox"] .v-field__input').click()
            return false
        }
    })
})

When('Important checkbox is checked in the edition form', () => {
    cy.get('.v-overlay table thead th').each((header, index) => {
        if (header.text() == 'Important') {
            cy.get('.v-overlay table tbody tr td').eq(index).find('input[type="checkbox"]').check()
            return false
        }
    })
})

When('Important checkbox is checked in the edition mode', () => {
    cy.get('table thead th').each((header, index) => {
        if (header.text() == 'Important') {
            cy.get('table tbody tr td').eq(index).find('input[type="checkbox"]').check()
            return false
        }
    })
})

When('Important checkbox is unchecked in the edition form', () => {
    cy.get('.v-overlay table thead th').each((header, index) => {
        if (header.text() == 'Important') {
            cy.get('.v-overlay table tbody tr td').eq(index).find('input[type="checkbox"]').uncheck()
            return false
        }
    })
})

When('Important checkbox is unchecked in the edition mode', () => {
    cy.get('table thead th').each((header, index) => {
        if (header.text() == 'Important') {
            cy.get('table tbody tr td').eq(index).find('input[type="checkbox"]').uncheck()
            return false
        }
    })
})

When('The Edition mode is enabled', () => cy.get('button .mdi-pencil').click())

When('The Edition mode is saved and closed', () => cy.contains('button', 'Save and Close').click())

When('The Edition mode is canceled and closed', () => cy.contains('button', 'Cancel').click())

When('Data is not available available for Instance Relationship', () => cy.contains('.v-overlay table tbody tr', 'No data available').should('be.visible'))

When('{string} visit is clicked from the dropdown', (visitName) => cy.contains('.v-overlay .v-list-item', visitName).click())

When('{string} visit is clicked from the dropdown in the edition mode', (visitName) => cy.contains('.v-list-item', visitName).click())

When('Previously added Data Supplier is clicked from the dropdown', () => cy.contains('.v-overlay .v-list-item', selectedSupplierValue).click())

When('Previously added Data Supplier is clicked from the dropdown in the edition mode', () => cy.contains('.v-list-item', selectedSupplierValue).click())

When('Baseline flag value is set to {string} in the table', (value) => cy.checkRowByIndex(0, 'Baseline visits', value))

When('Selected data supplier is visible in the table', () => cy.checkRowByIndex(0, 'Data Supplier', selectedSupplierValue))

When('Automatically populated Origin Type is visible in the table', () => cy.checkRowByIndex(0, 'Origin Type', originType))

When('Automatically populated Origin Source is visible in the table', () => cy.checkRowByIndex(0, 'Origin Source', originSource))

When('The activity instance with data-sharing set to {string}, required for activity set to {string} and default for activity set to {string} exists', (isDataSharing, isRequiredForActivity, isDefaultForActivity) => {
    createAndApproveParametrizedInstance(isDataSharing, isRequiredForActivity, isDefaultForActivity)
})

When('[API] The activity instance with name {string} and isRequriedForActivity set to true is created and approved', (name) => createAndApproveParametrizedInstance(false, true, false, `${name}_${getShortUniqueId()}`))

When('[API] The activity instance with isRequriedForActivity set to true is created and approved', () => createAndApproveParametrizedInstance(false, true, false))

When('[API] The activity instance with isDefaultForActivity set to true is created and approved', () => createAndApproveParametrizedInstance(false, false, true))

When('The user selects activity instance', () => {
    cy.get('[data-cy="form-body"]').within(() => {
        cy.get('tbody').within(() => {
            cy.get('.v-selection-control').first().click()
        })
    })

})

When('The user deselects one of activity instances', () => {
    cy.get('[data-cy="form-body"]').within(() => {
        cy.get('tbody').within(() => {
            cy.get('.v-selection-control').first().click()
        })
    })

})

When('The user selects multiple activity instances', () => [
    cy.get('[data-cy="form-body"]').within(() => {
        cy.get('tbody').within(() => {
            cy.get('.v-selection-control').click({multiple: true})
        })
    })
])

Then('The activity state is {string}', (state) => {
    cy.checkRowByIndex(0, 'State/Actions', state)

})

When('The {string} is clicked during review', (button) => {
    cy.contains(button).click()
})

Then('The reviewed checkbox is disabled', () => cy.get('tbody td .v-checkbox.v-input--disabled').should('exist'))

Then('The reviewed checkbox is enabled', () => cy.get('tbody td .v-checkbox').should('not.have.class', '.v-input--disabled'))

Then('The user checks the reviewed checkbox', () => cy.get('tbody td .v-checkbox input').check())

Then('The user unchecks the reviewed checkbox', () => cy.get('tbody td .v-checkbox input').uncheck())

Then('The reviewed checkbox is displayed as checked', () => cy.get('tbody td .v-checkbox input').should('be.checked'))

Then('The reviewed checkbox is displayed as unchecked', () => cy.get('tbody td .v-checkbox input').should('not.be.checked'))

When('The user removes the additional activities', () => { 
        cy.get('[data-cy="data-table"]').within(() => {
        cy.get('.mdi-dots-vertical').filter(':visible').eq(2).click()
    })
    cy.contains('Delete Activity - Instance relationship').click()
    cy.contains('Delete').click()
})

Then('The button {string} is not present', (button) => {
    cy.contains(button).should('not.be.visible')
})

Then('The button {string} is disabled', (button) => cy.contains(button).should('be.disabled'))

When('The activity instace class is updated', () => cy.selectVSelect('instanceform-instanceclass-dropdown', 'Event'))

When('The activity instace topic code is updated', () => cy.fillInput('instanceform-topiccode-field', getShortUniqueId()))

When('The user declines the activity instance changes', () => {
    cy.get('[data-cy="data-table"]').within(() => {
        cy.get('.mdi-dots-vertical').filter(':visible').click()
    })
    cy.clickButton('Update Instance to new version')
    cy.contains('button', 'Decline and keep').click()
})

When('The user accepts the activity instance changes', () => {
    cy.get('[data-cy="data-table"]').within(() => {
        cy.get('.mdi-dots-vertical').filter(':visible').click()
    })
    cy.clickButton('Update Instance to new version')
    cy.contains('button', 'Decline and keep').click()
})

Then('Activity instance column is empty', () => cy.checkRowByIndex(0, 'Activity instance', ''))

Then('Activity instance column contains value {string}', (value) => cy.checkRowByIndex(0, 'Activity instance', value))

Then('Activity name column contains value {string}', (value) => cy.checkRowByIndex(0, 'Activity', value))

Then('SoA Group is set to {string}', (value) => cy.checkRowByIndex(0, 'SoA group', value))

Then('Data collection column is set to {string}', (value) => cy.checkRowByIndex(0, 'Data collection', value))

When('User gets full activity instance name starting with {string}', (name) => cy.contains('table tbody td', name).invoke('text').then(text => studyActivityInstance = text))

When('User clicks Review Activity Instance Updates button', () => cy.contains('.actions-container button', 'Review activity instance updates').click())

When('For Activity Instance {string} name change to {string} is displayed in the Bulk Review window', (oldName, newName) => {
    cy.contains('.v-overlay tbody tr', oldName).within(() => {
        cy.contains('td .text-red.crossed-out', oldName).should('be.visible')
        cy.contains('td .text-green', newName).should('be.visible')
    })
})

When('Activity Instance {string} status change to Retired is displayed in the Bulk Review window', (name) => {
    cy.contains('.v-overlay tbody tr', name).within(() => {
        cy.contains('td .text-red.crossed-out', 'Final').should('be.visible')
        cy.contains('td .text-green', name).should('be.visible')
        cy.contains('td .text-green', 'Retired').should('be.visible')
    })
})

When('For Activity Instance {string} name change both Accept and Decline options are available in the Bulk Review window', (name) => {
    cy.contains('.v-overlay tbody tr', name).within(() => {
        cy.contains('button', 'Accept').should('be.visible')
        cy.contains('button', 'Decline').should('be.visible')
    })
})

When('For Activity Instance {string} status change to Retired only Decline option is available in the Bulk Review window', (name) => {
    cy.contains('.v-overlay tbody tr', name).within(() => {
        cy.contains('button', 'Accept').should('not.exist')
        cy.contains('button', 'Decline').should('be.visible')
    })
})

When('Activity Instance {string} status change is Declined in the Bulk Review window', (name) => {
    cy.contains('.v-overlay tbody tr', name).within(() => cy.contains('button', 'Decline').click())
})

When('Activity Instance {string} name change is Accepted in the Bulk Review window', (name) => {
    cy.contains('.v-overlay tbody tr', name).within(() => cy.contains('button', 'Accept').click())
})

When('User saves changes in the Bulk Review window', () => cy.contains('.v-overlay .v-card-actions button', 'Save').click())

When('User is presented with confirmation window regarding removal of activity-instance relationship', () => {
    cy.get('.v-card .dialogText').should('contain.text', 'The study activity instance')
    cy.get('.v-card .dialogText').should('contain.text', 'will be deleted')
})

function createAndApproveParametrizedInstance(isDataSharing, isRequiredForActivity, isDefaultForActivity, customName = '') {
    cy.getClassUid()
    cy.createActivityInstance(customName, isDataSharing, isRequiredForActivity, isDefaultForActivity)
    cy.approveActivityInstance()
}