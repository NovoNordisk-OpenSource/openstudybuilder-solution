import { activity_activity } from "./study_define_activities_activities_steps";

const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The Operational SoA table is loaded', () => cy.get('table tbody tr').should('be.visible'))

When('Row containing submitted placeholder is highlighted with yellow color in Operational SoA', () => cy.contains('tr.bg-yellow', activity_activity).should('be.visible'))

When('Row containing unsubmitted placeholder is highlighted with orange color in Operational SoA', () => cy.contains('tr.bg-warning', activity_activity).should('be.visible'))

When('User waits Operational SoA table', () => cy.get('table tbody tr').should('be.visible'))

When('Expand table and Show SoA groups is available on the page', () => {
    cy.get('.mb-4').should('contain', 'Expand table')
    cy.get('.mb-4').should('contain', 'Show SoA groups')
})

When('User checks {string} option in the Operational SoA', (value) => cy.contains('.mb-4', value).find('input').check())

When('Activity {string} is visible in the Operational SoA with Instance {string} underneath it', (activity, instance) => {
    cy.contains('table tbody tr', activity).next().should('contain.text', instance)
})

When('Activity with multible groupings - soa {string}, group {string}, subgroup {string}, activity {string} is visible in the Operational SoA with Instance {string} underneath it', (soa, group, subgroup, activity, instance) => {
    cy.contains('table tbody tr', soa)
        .nextAll('.group').contains(group).parent().parent()
            .nextAll().contains(subgroup).parent().parent()
                .next().should('contain.text', activity)
                    .next().should('contain.text', instance)
})

When('Activity {string} in the Operational SoA does not have Instance underneath it', (activity) => {
    cy.get('table tbody tr').then(el => {
        const length = el.length
        cy.contains('table tbody tr', activity).invoke('index').then(index => {
            index == length - 1
                ? cy.contains('table tbody tr', activity).next().should('not.exist')
                : cy.contains('table tbody tr', activity).next().find('td.activityInstance').should('not.exist')
        })
    })
})

When('The Activity Instance {string} is marked on visit {string} in the Operational SoA', (instance, visit) => {
    cy.contains('table thead tr', 'Visit').contains('th', visit).invoke('index').then(index => {
        cy.contains('table tbody tr', instance).find('td').eq(index + 2).should('contain.text', 'X')
    })
})