const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let studySubpartAcronym

When('User deletes all existing subparts', () => {
    cy.get('table tbody').then($tbody => {
        if ($tbody.text().includes('No data available')) return
        cy.get('table tbody tr:visible').its('length').then(count => {
            for (let i = count - 1; i >= 0; i--) {
                cy.get('table tbody tr:visible').eq(i).within(() => cy.clickButton('table-item-action-button', true))
                cy.clickButton('Remove', true)
                cy.checkSnackbarMessage('Study subpart removed')
            }
         })
    })
})

When('User is presented with main study acronym {string} during subpart creation', (mainStudyAcronym) => {
    cy.contains('.v-overlay .v-input', 'Study acronym').find('input').should('have.value', mainStudyAcronym)
})

When('User is presented with warnig that study subpart acronym is required filed', () => {
    cy.contains('.v-overlay .v-input', 'Study subpart acronym').find('[role="alert"]').should('contain.text', 'This field is required')
})

When('User is presented with warnig that study subpart acronym cannot exceed 10 characters', () => {
    cy.contains('.v-overlay .v-input', 'Study subpart acronym').find('[role="alert"]').should('contain.text', 'This field must not exceed 10 characters')
})

When('User sets study subpart acronym', () => {
    cy.contains('.v-overlay .v-input', 'Study subpart acronym').type(studySubpartAcronym = 'subpart')
})

When('User sets study subpart for removal test', () => {
    cy.contains('.v-overlay .v-input', 'Study subpart acronym').type(studySubpartAcronym = 'dsubpart')
})

When('User updates study subpart acronym', () => {
    cy.contains('.v-overlay .v-input', 'Study subpart acronym').clear().type(studySubpartAcronym = 'newSubpart')
})

When('User sets study subpart acronym to value exceeding characters limit', () => {
    cy.contains('.v-overlay .v-input', 'Study subpart acronym').type('a'.repeat(11))
})

When('Study subpart is searched for and found', () => cy.searchAndCheckPresence(studySubpartAcronym.toUpperCase(), true))

When('Study subpart is searched for and not found', () => cy.get('table tbody tr').filter(':visible').should('contain.text', 'No data available'))

When('Study subpart is searched for and found in the study list', () => cy.searchAndCheckPresence(`CDISC DEV-9876-${studySubpartAcronym}`.toUpperCase(), true))

When('Study subpart data is correctly displayed in the table', () => {
    cy.checkRowByIndex(0, 'Study ID', `CDISC DEV-9876-${studySubpartAcronym.toUpperCase()}`)
    cy.checkRowByIndex(0, 'Study acronym', 'E2E Main Test Study')
    cy.checkRowByIndex(0, 'Subpart ID', 'a')
    cy.checkRowByIndex(0, 'Subpart acronym', studySubpartAcronym.toUpperCase())
})

When('Study subpart data is correctly displayed in the study list table', () => {
    cy.checkRowByIndex(0, 'Project ID', `CDISC DEV`)
    cy.checkRowByIndex(0, 'Study number', '9876')
    cy.checkRowByIndex(0, 'Study ID', `CDISC DEV-9876-${studySubpartAcronym.toUpperCase()}`)
    cy.checkRowByIndex(0, 'Main study ID', `CDISC DEV-9876`)
    cy.checkRowByIndex(0, 'Subpart ID', 'a')
    cy.checkRowByIndex(0, 'Study acronym', 'E2E Main Test Study')
    cy.checkRowByIndex(0, 'Subpart ID', 'a')
    cy.checkRowByIndex(0, 'Study subpart acronym', studySubpartAcronym.toUpperCase())
})