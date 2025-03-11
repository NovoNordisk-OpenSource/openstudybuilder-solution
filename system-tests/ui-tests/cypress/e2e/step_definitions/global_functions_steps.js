const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The first column is selected from Select Columns option for table with actions', () => {
    const columnVisibilityCheckbox = '[data-cy="show-columns-form"] [type="checkbox"]'
    cy.clickButton('columns-layout-button')
    cy.wait(500)
    cy.get(columnVisibilityCheckbox).each((item) => cy.wrap(item).uncheck( {force: true} ))
    cy.get(columnVisibilityCheckbox).eq(0).click( {force: true} )
    cy.get(columnVisibilityCheckbox).each((item, index) => {if (index != 0) cy.wrap(item).uncheck( {force: true} )})
    cy.get('[data-cy="show-columns-form"] label').eq(0).as('selectedColumn')
})

When('The study title form is filled with UTF-8 charset', () => {
  cy.wait(500)
  cy.fillInput("study-title", '±≥≤~≠∞°−ü®©™αβγδμτλπφψ')
  cy.fillInput('short-study-title', 'Test')
  cy.clickButton('save-button')
})

Then('The UI is showing the UTF-8 charset correctly', () => {
  cy.get('[data-cy="study-title-field"]').eq(0).should('contain', '±≥≤~≠∞°−ü®©™αβγδμτλπφψ')
})

Then('The pop up displays {string}', (message) => {
  cy.checkSnackbarMessage(message)
})

Then('The table contain only selected column', () => {
    checkTableHeaders(false)
})

Then('The table contain only selected column and actions column', () => {
    checkTableHeaders(true)
})

Then('The {string} form is opened', (formTitle) => {
    cy.elementContain('form-body', formTitle)
})

Given('The user is logged out', () => {
    cy.window().then((win) => {
        win.sessionStorage.clear()
    });
})

Given('The user is logged in', () => {
    cy.loginUser()
    window.localStorage.setItem('userData', '{"darkTheme":false,"rows":0,"studyNumberLength":4}')

})

Given('The user is logged in with all.in profile', () => {
    cy.loginUser()
    window.localStorage.setItem('userData', '{"darkTheme":false,"rows":0,"studyNumberLength":4}')

})

When('The top bar button has logout option available', () => {
    cy.clickButton('topbar-user-name')
    cy.get('[data-cy="topbar-logout"]').should('have.attr', 'href', '/logout')
})

Then('The user can navigate to authentication provider via top bar login button', () => {
    cy.get('[data-cy="topbar-login"]').should('have.attr', 'href', '/login')
})

Then('The username is visible in the navigation bar', () => {
    cy.get('[data-cy="topbar-user-name"]').should('contain', Cypress.env('TESTUSER_NAME'))
})

function checkTableHeaders(actionsAvailable) {
    let expectedLength = actionsAvailable ? 2 : 1
    cy.get('@selectedColumn').invoke('text').then(column => {
        cy.get('table thead').contains((column))
        cy.get('table thead th').should('have.length', expectedLength)
    })
}