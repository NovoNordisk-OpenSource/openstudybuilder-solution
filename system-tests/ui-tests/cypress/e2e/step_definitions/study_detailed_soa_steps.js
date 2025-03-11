const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let current_activity
let new_activity_name

When('At least {string} activites are present in {string} study', (number_of_activities, study_id) => {
    prepareActivites(number_of_activities, study_id)
})

When('The user click on {string} action for an Activity', (action) => {
    cy.request('api/studies/Study_000001/study-activities?total_count=true').then((req) => {
        current_activity = req.body.items[0].activity.name.substring(0, 40)
        cy.wait(1000)
        cy.contains('.v-selection-control', 'Expand table').click()
        cy.contains('table tbody tr.bg-white', current_activity).within(() => cy.clickButton('table-item-action-button'))
        cy.clickButton(action)
    })
})

When('The user goes through selection from library form', () => {
    cy.clickFormActionButton('continue')
    cy.get('[data-cy="select-activity"]').not('.v-selection-control--disabled').parentsUntil('tr').siblings().eq(4).invoke('text').then((activity_name) => {
        new_activity_name = activity_name.substring(0, 40)
    })
    cy.get('[data-cy="select-activity"]').not('.v-selection-control--disabled').first().click()
    cy.get('[data-cy="flowchart-group"]').not('.v-input--disabled').first().click()
    cy.get('.v-list-item').filter(':visible').first().click()
    cy.clickFormActionButton('save')
})

Then('The newly selected activity replaces previous activity in study', () => {
    cy.reload()
    cy.contains('.v-selection-control', 'Expand table').click()
    cy.contains('table tbody tr.bg-white', new RegExp(current_activity, "g")).should('not.exist')
    cy.contains('table tbody tr.bg-white', new RegExp(new_activity_name, "g")).should('exist')
})

Then('The newly created activity is present in SoA', () => {
    cy.reload()
    cy.contains('.v-selection-control', 'Expand table').click()
    cy.contains(new_activity_name).should('exist')

})

When('The user confirms the deletion pop-up', () => {
    cy.clickButton('continue-popup')
})

Then('The Activity is no longer visible in the SoA', () => {
    cy.reload()
    cy.contains('.v-selection-control', 'Expand table').click()
    cy.contains(current_activity).should('not.exist')
})

When('The user selects rows in SoA table', () => {
    cy.request('api/studies/Study_000001/study-activities?total_count=true').then((req) => {
        current_activity = req.body.items[0].activity.name.substring(0, 40)
        cy.wait(1000)
        cy.contains('.v-selection-control', 'Expand table').click()
        cy.contains('.bg-white', current_activity).within(() => {
            cy.get('[id^="checkbox"]').first().click()
        })
    })
})

When('The user clicks on Bulk Edit action on SoA table options', () => {
    cy.get('[title="Bulk actions"]').click()
    cy.contains('.v-list-item', 'Bulk Edit Activities').click()
})

Then('The bulk edit view is presented to user allowing to update Activity Group and Visits for selected activities', () => {
    cy.elementContain('form-body', 'Batch edit study activities')
    cy.elementContain('form-body', 'Note: The entire row of existing selections will be overwritten with the selection(s) done here')
    cy.elementContain('form-body', 'Batch editing will overwrite existing choices. Only activities expected to have same schedule should be batch-edited together.')
    cy.elementContain('form-body', 'Batch edit study activities')
    cy.elementContain('form-body', current_activity)
})

When('The user edits activities in bulk', () => {
    cy.slectFirstVSelect('bulk-edit-soa-group')
    cy.slectFirstVSelect('bulk-edit-visit')
    cy.intercept('**/soa-edits/batch').as('editRequest')
    cy.clickButton('save-button')

})

Then('The data for bulk edited activities is updated', () => {
    cy.wait('@editRequest').its('response.statusCode').should('equal', 207)

})

When('The user edits activities in bulk without selecting Activity Group and Visit', () => {
    bulkAction('Bulk Edit Activities')
    cy.clickButton('save-button')

})

Then('The validation appears for Activity Group field in bulk edit form', () => {
    cy.get('[data-cy="form-body"]').within(()=> {
        cy.get('.v-input').eq(1).should('contain', 'This field is required')
        cy.get('.v-input').eq(2).should('contain', 'This field is required')
    })
})

When('The user delete activities in bulk', ()=> {
    bulkAction('Bulk Remove Activities')
    cy.intercept('**/study-activities/batch').as('deleteRequest')
    cy.clickButton('continue-popup')
    
})

Then('The activities are removed from the study', () => {
    cy.wait('@deleteRequest').its('response.statusCode').should('equal', 207)

})


function bulkAction(action) {
    cy.request('api/studies/Study_000001/study-activities?total_count=true').then((req) => {
        current_activity = req.body.items[0].activity.name.substring(0, 40)
        cy.wait(1000)
        cy.contains('.v-selection-control', 'Expand table').click()
        cy.contains('.bg-white', current_activity).within(() => {
            cy.get('[id^="checkbox"]').first().click()
        })
    })
    cy.get('[title="Bulk actions"]').click()
    cy.contains('.v-list-item', action).click()
}
function prepareActivites(number_of_activities, study_id) {
    cy.request('api/studies/' + study_id + '/study-activities?total_count=true').then((req) => {
        if (req.body.total < parseInt(number_of_activities)) {
            cy.log('No activity')
            cy.visit('studies/' + study_id + '/activities/list')
            cy.clickButton('add-study-activity')
            cy.clickFormActionButton('continue')
            cy.get('[data-cy="select-activity"]').not('.v-selection-control--disabled').first().click()
            cy.get('[data-cy="flowchart-group"]').not('.v-input--disabled').first().click()
            cy.get('.v-list-item').filter(':visible').first().click()
            cy.clickFormActionButton('save')
            prepareActivites(number_of_activities, study_id)
        } else {
            cy.log('Activity exists')
        }
    })
}
