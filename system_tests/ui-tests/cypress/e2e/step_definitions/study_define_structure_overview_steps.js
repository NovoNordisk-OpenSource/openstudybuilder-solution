const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The value {string} is displayed for {string} in the study overview', (value, name) => {
    cy.contains('.v-col', name).should('contain.text', value)
})

When('The row {int} in the study structure overview page displays value of subjects {int} for arm {string}', (index, value, name) => {
    valueChecker(index, 'Arms', name, `${value} subjects`)
})

When('The row {int} in the study structure overview page displays value of subjects {int} for branch {string}', (index, value, name) => {
    valueChecker(index, 'Branch arms', name, `${value} subjects`)
})

When('The row {int} in the study structure overview page displays value of subjects {int} for cohort {string}', (index, value, name) => {
    valueChecker(index, 'Cohorts', name, `${value} subjects in total per cohort`)
})

When('The row {int} in the study structure overview page displays value {string} for epoch {string}', (index, value, epochName) => {
    valueChecker(index, epochName, null, value)
})

function valueChecker(index, columnName, name, value) {
    const tableLocator = '[aria-label="Study structure overview table"]'
    cy.get(`${tableLocator} thead tr`).eq(1).contains(columnName).invoke('index').then(columnIndex => {
        cy.get(`${tableLocator} tbody tr`).eq(index).within(row => {
            if (columnIndex != 0 && index != 0 && index != 3) columnIndex -= 1
            name ? cy.wrap(row).find('td').eq(columnIndex).contains(name).next().should('have.text', value)
                 : cy.wrap(row).find('td').eq(columnIndex).should('have.text', value)
        })
    })
}