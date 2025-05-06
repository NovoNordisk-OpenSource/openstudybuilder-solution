const {Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { closeSync } = require("fs");

let current_activity
let new_activity_name
let first_in_order
let last_in_order
When('At least {string} activites are present in {string} study', (number_of_activities, study_id) => {
    prepareActivites(number_of_activities, study_id)
})

Given('At least {string} activities are present in {string} in the same {string} flowchart subgroup and {string} group', (number_of_activities, study_id, group, subgroup) => {
    prepareActivitesInSameGroup(number_of_activities, subgroup, study_id, group)
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
    cy.contains('table tbody tr.bg-white', new RegExp(`^(${current_activity})$`, "g")).should('not.exist')
    cy.contains('table tbody tr.bg-white', new RegExp(`^(${new_activity_name})$`, "g")).should('exist')
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

When('The user enables the Reorder Activities function for acitivities in the same {string} flowchart subgroup and {string} group', (subgroup, group) => {
    cy.get('[aria-label="Expand table"]').click()
            cy.contains('tr[class="bg-white"]', subgroup).within(() => {
                cy.clickButton('table-item-action-button')
            })
    cy.clickButton('Reorder')

})

When('The user updates the order of activities', () => {
    cy.intercept('**/order').as('orderRequest')
    cy.wait(1500)
    cy.get('.mdi-sort').first().parentsUntil('td').invoke('text').then((text) => {last_in_order = text})
    cy.get('.mdi-sort').last().parentsUntil('td').invoke('text').then((text) => {first_in_order = text})

    cy.get('.mdi-sort').last().parentsUntil('td').drag('.sticky-column > .d-flex', {
        source: { x: 100, y: 100 }, // applies to the element being dragged
        target: { position: 'left' }, // applies to the drop target
        force: true, // applied to both the source and target element)
        })
    cy.contains('.v-btn', 'Finish reordering').click()
    
})
Then('The new order of activites is visible', () => {
    cy.get('[aria-label="Expand table"]').click()
    cy.contains('tr[class="bg-white"]', 'Acute Kidney Injury').within(() => {
        cy.clickButton('table-item-action-button')
    })
    cy.clickButton('Reorder')
    cy.get('.mdi-sort').first().parentsUntil('td').should('contain', first_in_order)
    
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
            cy.log('Skipping activity creation')
        }
    })
}
function countGroupsAndSubgroupsInStudy(data, subgroup, group) {
    let group_subgroup_count = 0

    data.body.items.forEach(element => {

        if (element.study_activity_subgroup.activity_subgroup_name === subgroup && element.study_soa_group.soa_group_term_name === group) {
            group_subgroup_count++
        }
    });
    return group_subgroup_count

}
function prepareActivitesInSameGroup(number_of_activities, subgroup, study_id, group) {
    cy.request('api/studies/' + study_id + '/study-activities?total_count=true').then((req) => {
        cy.log(`found: ${countGroupsAndSubgroupsInStudy(req, group, subgroup)}`)
        if ( countGroupsAndSubgroupsInStudy(req, group, subgroup) < parseInt(number_of_activities)) {
            cy.visit('studies/' + study_id + '/activities/list')
            cy.clickButton('add-study-activity')
            cy.clickFormActionButton('continue')
            cy.contains('Use the same SoA group for all').click()
            cy.get('.v-card-title > .v-autocomplete > .v-input__control > .v-field').first().click()
            cy.contains('.v-list-item__content', 'BIOMARKERS').click()
            cy.get('[data-cy="form-body"]').within(() => {
                selectFirstNRowsContainingValue(subgroup, number_of_activities)

            })
            cy.clickFormActionButton('save')
            prepareActivites(number_of_activities, study_id, subgroup)
        } else {
            cy.log('Skipping activity creation')
        }
    })
}

function selectFirstNRowsContainingValue(value, numberOfRows) {
    let selectedCount = 0

    cy.get('tbody.v-data-table__tbody tr').each(($row) => {
        if (selectedCount < numberOfRows) {
            cy.wrap($row).find(':nth-child(5)').each(($cell) => {
                cy.wrap($cell).invoke('text').then((cellText) => {
                    if (selectedCount < numberOfRows) {
                    if (cellText.includes(value)) {
                        cy.wrap($row).find('input[type="checkbox"]').check(); // Checking the checkbox
                        selectedCount++
                    }
                }
                })
            })
        } else {
            return false
        }
    })
}