const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getCurrStudyUid } = require("../../support/helper_functions");

Then('The {string} page is shown', (pageTitle) => cy.get('.page-title').should('contain.text', pageTitle))

Then('User clicks button {string}', (value) => cy.get(`.v-card [data-cy="${value}"]`).click())

Then('User defocus from field', () => cy.get('body').click())

Then('The current URL is {string}', (url) => cy.url().should('contain', url))

When('The page {string} is opened for current study', (page) => goToPageAndForItToLoad(`/studies/${getCurrStudyUid()}/${page}`))
Given('The {string} page is opened', (url) => goToPageAndForItToLoad(url))

Given('The homepage is opened', () => cy.visit('/'))

Given('The page is reloaded', () => cy.reload())

Given('User selects study with id {string}', (studyId) => {
    cy.getStudyUidById(studyId).then(uid => {
        cy.sendGetRequest(`/studies/${uid}`).then((response) => {
            window.localStorage.setItem("selectedStudy", JSON.stringify(response.body))
        })
    })
})

function goToPageAndForItToLoad(url) {
    cy.visit(url)
    cy.waitForPage()
}