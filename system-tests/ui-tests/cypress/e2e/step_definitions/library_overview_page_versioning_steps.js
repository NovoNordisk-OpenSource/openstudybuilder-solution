const { When, Then } = require('@badeball/cypress-cucumber-preprocessor');

Then('I verify that at least one Activity Instance is linked to the test Activity', () => {
    cy.get('table tbody tr').should('have.length.gt', 0).each(($row) => {
        cy.wrap($row).find('td').each(($cell) => cy.wrap($cell).should('not.be.empty'));
    }); 
})

When('I click {string} button', (title) => cy.get(`button.v-btn[title="${title}"]`).click())

When('I make changes to the activity, enter a reason for change and save', () => {
    cy.get('[data-cy="activityform-activity-name-field"] input').type('Update');
    cy.contains('.v-col', 'Reason for change').find('textarea').not('.v-textarea__sizer').type('Test purpose');
    cy.clickFormActionButton('save')
})

Then('I verify that the Activity version is {string} and status is {string}', (version, status) => {
    cy.contains('.v-col', 'Version').next().find('input').should('have.value', version)
    cy.contains('.v-col', 'Status').next().should('have.text', status)
})

Then('I verify that the linked Activity Instances list contains all the instances that were linked to the Activity version 1.0', () => {
    cy.contains('.v-row', 'Activity instances').find('table tbody').should('not.be.empty');
})

Then('I verify that the Activity does not have any linked Activity Instances', () => {
    cy.contains('.v-row', 'Activity instances').find('table tbody').should('be.empty');
})

Then('I verify that each instance is listed as version 1.2 in status Draft and version 2.0 in status Final', () => {
    cy.contains('.v-row', 'Activity instances').find('table tbody').within(() => {
        cy.contains('tr', 'Final').should('contain', '2.0')
        cy.contains('tr', 'Draft').should('contain', '1.2')
    })
})

Then('I verify that the linked instances are version 1.0 and status Final', () => {
    cy.contains('.v-row', 'Activity instances').find('table tbody').within(() => {
        cy.contains('tr', 'Final').should('contain', '1.0')
    })
})
