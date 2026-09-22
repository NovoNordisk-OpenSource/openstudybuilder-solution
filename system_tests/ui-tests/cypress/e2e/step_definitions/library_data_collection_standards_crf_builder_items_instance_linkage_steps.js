import { formName, itemName } from "./library_data_collection_standards_crf_builder_tree_versioning_steps";

const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { generateShortUniqueName } = require("../../support/helper_functions");

export let linkedInstance

Given('The linked instances list is cleared', () => linkedInstance = [])

When('Created test CRF Item is found', () => cy.searchAndCheckPresence(itemName, true))

Then('User switch to table view of CRF Item instance linkage', () => cy.get('[data-cy="switch-view"] input').uncheck())

Then('User switch to Form view of CRF Item instance linkage', () => cy.get('[data-cy="switch-view"] input').check())

Then('By default the Form view of CRF Item instance linkage is selected', () => cy.get('[data-cy="switch-view"] input').should('be.checked'))

Then('By default the Table view of CRF Item instance linkage is selected', () => cy.get('[data-cy="switch-view"] input').should('not.be.checked'))

Then('Activity Instance Item {int} table is visible', (tableNumber) => {
    cy.get('.v-card-title').contains(`Activity Instance Item ${tableNumber}`).should('be.visible');
});

When('I click the Activity Instance Link plus button', () => cy.clickButton('add-activity-instances'))

When('I click the Delete button', () => cy.clickButton('remove-activity-instance'))

When('I click the RESET button', () => cy.clickButton('reset-activity-instances'))

Then('The Delete button is visible', () => cy.get('[data-cy="remove-activity-instance"]').should('be.visible'))

Then('The RESET button is enabled', () => cy.get('[data-cy="reset-activity-instances"]').should('be.visible').and('not.be.disabled'))

Then('The RESET button is disabled', () => cy.get('[data-cy="reset-activity-instances"]').should('be.disabled'))

When('Selected Activity Instance name is saved for Activity Instance Item {int}', (index) => getInstanceName(index))

When('Selected Activity Instance name in the table view is saved', (index) => getSelectedInstanceName(index))

When('Activity Instance for Activity Instance Item {int} is selected', (index) => {
    activateDropdown(index, 'activity-instance', false)
    cy.get('.v-overlay__content .v-list-item').eq(index).click()    
})

When('Activity Item Class for Activity Instance Item {int} is selected', (index) => {
    activateDropdown(index, 'activity-item-class', true)
    cy.get('.v-overlay__content .v-list-item').first().click()
})

When('User selects first value for linked Activity Instance', () => cy.selectFirstVSelect('select-activity-instance'))

When('User selects last value for linked Activity Instance', () => cy.selectLastVSelect('select-activity-instance'))

When('I select an Activity Item Class from the table', () => cy.get('.v-overlay table tbody tr input[type="checkbox"]').first().check())

When('I select created Form from the Form Name dropdown list', () => {
    cy.get('.v-label').contains('Form Name').parent().parent().find('.v-field__input').click();
    cy.get('.v-overlay__content .v-list', { timeout: 10000 }).should('be.visible');
    cy.get('.v-overlay__content .v-list-item').contains(formName).scrollIntoView().click();
});

When('User waits for CRF Viewer data to load', () => {
    cy.intercept('/api/odms/metadata/report?*').as('getCrfViewerData');
    cy.wait('@getCrfViewerData', { timeout: 60000 });
});

When('I click the Activity Instance option from the right top corner', () => {
    cy.get('iframe.frame').its('0.contentDocument.body').should('not.be.empty')
        .then(cy.wrap).contains('button', 'Activity Instance').click()
});

Then('The added Activity Instance Link is displayed under the test item name', () => {
    cy.get('iframe.frame').its('0.contentDocument.body').should('not.be.empty')
        .then(cy.wrap)
        .then($body => {
            cy.wrap($body).contains('h4', itemName).should('exist')
            cy.wrap($body).contains('tr', itemName).within(() => {
                cy.get('.activity-instance-container').should('be.visible');
                linkedInstance.forEach(instance => cy.get('.activity-instance-container').should('contain', instance))
            })
        })
})

Then('I should see alert messages for both Activity Instance and Activity Item Class fields', () => {
    cy.get('.v-alert.bg-error').should('contain', 'Activity Instance UID of Activity Instances #1 must be at least 1 character(s)');
    cy.get('.v-alert.bg-error').should('contain', 'Activity Item Class UID of Activity Instances #1 must be at least 1 character(s)');
});

When('Activity Item Class dropdown is activivated without selecting any value', () => {
    activateDropdown(1, 'activity-item-class', true)
    cy.get('body').click();
});

Then('I should see a field validation message for the Activity Item Class dropdown list', () => {
    cy.checkIfValidationAppears('activity-item-class');
});

Then('I should see an alert message for the Activity Item Class field', () => {
    cy.get('.v-alert.bg-error').should('contain', 'Activity Item Class UID of Activity Instances #1 must be at least 1 character(s)');
});

Then('I am not able to select a value from the Activity Item Class dropdown list before I have selected a value from the Activity Instance dropdown list', () => {
    cy.get('[data-cy="activity-item-class"]').should('have.class', 'v-input--readonly');
});

Then('Saved linked Activity Instance Item table is visible', () => {
    cy.contains('.v-card-title', 'Activity Instance Item 1').parent('.v-card').within(() => {
        cy.get('[data-cy="activity-instance"] .v-autocomplete__selection-text').should('not.be.empty')
    })
})

Then('I can see no linked Activity Item Class in the Form View', () => {
    cy.contains('.v-card-title', 'Activity Instance Item 1').parent('.v-card').within(() => {
        cy.get('[data-cy="activity-item-class"] input').should('have.value', '')
    })
})

Then('The Edit Item page does not show any linked Activity Instances', () => {
    cy.contains('.v-card-title', 'Activity Instance Item 1').should('not.exist')
    cy.get('.v-col').contains('No Activity Instance Links').should('be.visible')
})

Then('I can see the CRF Item in the CRF Tree', () => cy.contains('.crf-tree-node .node-content', itemName))

When('The Manage Activity Instance Links action is selected for CRF Item in the CRF Tree', () => {
    cy.contains('.crf-tree-node .node-content', itemName).find('[data-cy="table-item-action-button"]').click()
    cy.get('[data-cy="Manage Activity Instances"]').click()
})

Then('The Edit Item page is opened', () => cy.get('.dialog-title').should('contain', 'Edit Item'))

function getSelectedInstanceName() {
    cy.get('[data-cy="select-activity-instance"] .v-autocomplete__selection').invoke('text').then(text => linkedInstance.push(text.trim()))
}

function getInstanceName(index) {
    cy.contains('.v-card-title', `Activity Instance Item ${index}`).parent('.v-card').within(() => {
        cy.get('[data-cy="activity-instance"] .v-autocomplete__selection-text').invoke('text').then(text => linkedInstance.push(text.trim()))
    })
}

function activateDropdown(index, selectorValue, force = false) {
    cy.contains('.v-card-title', `Activity Instance Item ${index}`).parent('.v-card').then(parent => {
        cy.wrap(parent).find(`[data-cy="${selectorValue}"] input`).click({force: force});
    })    
}