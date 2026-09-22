const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
import { formatDateToMMMDDYYYY, getCurrentStudyId, getCurrStudyUid } from '../../support/helper_functions'

When("Click the View Listings side-menu", () => cy.get('.v-list-item-title').contains('View Listings').click())

Then("The sub-menu Analysis Study Metadata should exist", () => cy.get(`[data-cy="Analysis Study Metadata (New)"]`).should('be.visible'))

Then("The sub-menu Analysis Study Metadata should not exist", () => cy.get(`[data-cy="Analysis Study Metadata (New)"]`).should('not.exist'))

When('User clicks table export button', () => cy.clickButton('table-export-button'))

When('User clicks export button', () => cy.get('button .mdi-download-outline').click())

When('User selects {string} format to export the table content', (format) => cy.contains('.v-list-item', format).click({force: true}))

When('User waits for {int} seconds', (waitTime) => cy.wait(waitTime * 1000))

When('The first column is selected from Select Columns option for table with actions', () => {
    const columnVisibilityCheckbox = '[data-cy="show-columns-form"] [type="checkbox"]'
    cy.clickButton('columns-layout-button')
    cy.wait(500)
    cy.get(columnVisibilityCheckbox).each((item) => cy.wrap(item).uncheck( {force: true} ))
    cy.get(columnVisibilityCheckbox).eq(0).click( {force: true} )
    cy.get(columnVisibilityCheckbox).each((item, index) => {if (index != 0) cy.wrap(item).uncheck( {force: true} )})
    cy.get('[data-cy="show-columns-form"] label').eq(0).as('selectedColumn')
})

When('Column {string} is made visible', (name) => {
    cy.clickButton('columns-layout-button')
    cy.contains('.v-selection-control', name).find('input').check()
    cy.clickButton('columns-layout-button')
})

When('The study title form is filled with UTF-8 charset', () => {
  cy.wait(500)
  cy.fillInput("study-title", '±≥≤~≠∞°−ü®©™αβγδμτλπφψ')
  cy.fillInput('short-study-title', 'Test')
})

Then('The UI is showing the UTF-8 charset correctly', () => {
  cy.get('[data-cy="study-title-field"]').eq(0).should('contain', '±≥≤~≠∞°−ü®©™αβγδμτλπφψ')
})

Then('The pop up displays {string}', (message) => {
  cy.checkSnackbarMessage(message)
})

Then('Validation message {string} is displayed', (message) => cy.contains('.v-messages', message))

Then('The table contain only selected column', () => {
    checkTableHeaders(false)
})

Then('The table contain only selected column and actions column', () => {
    checkTableHeaders(true)
})

Then('The {string} form is opened', (formTitle) => cy.get('.dialog-title').should('contain.text', formTitle))

Given('The user is logged out', () => {
    cy.window().then((win) => {
        win.sessionStorage.clear()
    });
})

Given('The user is logged in', () => {
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

When('I click the {string} download button', (title) => {
    cy.get([`"title=${title}"`])
})

Then('The study specific {string} file without date timestamp is downloaded in {string} format', (filename, format) => {
    const filePath = `cypress/downloads/Study ${getCurrStudyUid()} ${filename}.${format}`
    cy.readFile(filePath).then((file ) => {cy.log(file)})
})

Then('The study specific {string} file is downloaded in {string} format', (filename, format) => {
    let currentDate1 = formatDateToMMMDDYYYY()
    let currentStudy = getCurrentStudyId()
    const filePath = `cypress/downloads/${currentStudy} ${filename} ${currentDate1}.${format}`
    cy.readFile(filePath).then((file ) => {cy.log(file)})
})

Then('The {string} file is downloaded in {string} format', (filename, format) => {
    let currentDate1 = formatDateToMMMDDYYYY()
    const filePath = `cypress/downloads/${filename} ${currentDate1}.${format}`
    cy.readFile(filePath).then((file ) => {cy.log(file)})
})

Then('The {string} file without timestamp is downloaded in {string} format', (filename, format) => {
    const filePath = `cypress/downloads/${filename}.${format}`
    cy.readFile(filePath).then((file ) => {cy.log(file)})
})

Then('The study specific {string} file without timestamp is downloaded in {string} format', (filename, format) => {
    let currentStudy = getCurrentStudyId()
    const filePath = `cypress/downloads/${currentStudy} ${filename}.${format}`
    cy.readFile(filePath).then((file ) => {cy.log(file)})
})

function checkTableHeaders(actionsAvailable) {
    let expectedLength = actionsAvailable ? 2 : 1
    cy.get('@selectedColumn').invoke('text').then(column => {
        cy.get('table thead').contains((column))
        cy.get('table thead th').should('have.length', expectedLength)
    })
}