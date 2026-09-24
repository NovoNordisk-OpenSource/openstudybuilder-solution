const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('User selects first value from CRF Collection dropdown', () => {
  cy.contains('.v-input', 'CRF Collection').click()
  cy.get('.v-overlay__content:visible .v-list').find('.v-list-item').should('have.length.at.least', 2)
  cy.get('.v-overlay__content:visible .v-list').find('.v-list-item').eq(1).click()
  cy.contains('.v-input', 'CRF Collection').find('input').click({ force: true }) //defocus
})

When('User selects last value from CRF Forms dropdown', () => {
  cy.contains('.v-input', 'Form(s)').click()
  cy.get('.v-overlay__content:visible .v-list').find('.v-list-item').last().click()
  cy.contains('.v-input', 'Form(s)').find('.mdi-menu-down').click() //defocus
})

When('User selects first value from the Form Name dropdown', () => {
  cy.contains('.v-input', 'Form Name').click()
  cy.get('.v-overlay__content:visible .v-list').find('.v-list-item').should('have.length.at.least', 2)
  cy.get('.v-overlay__content:visible .v-list').find('.v-list-item').first().click({ force: true })
})

When ('User clicks the GENERATE button', () => cy.contains('button', 'Generate').click())

Then('User opens stylesheets dropdown', () => cy.contains('.v-input', 'Stylesheet').find('input').click({ force: true }))

Then("CRF with annotations and Downloadable Falcon are available in the Stylesheet dropdown list", () => {
    cy.get('.v-overlay__content:visible .v-list').within(() => {
      cy.contains('.v-list-item__content', 'CRF with annotations').should('be.visible')
      cy.contains('.v-list-item__content', 'Downloadable Falcon').should('be.visible')
    })
})

When("User selects Downloadable Falcon in the Stylesheet dropdown list", () => {
  cy.get('.v-list-item__content').contains('Downloadable Falcon').click({ force: true })
})

When("User selects HTML option from the Stylesheet dropdown list", () => {
  cy.get('.v-list-item__content').contains('HTML').click({ force: true })
})

Then('The iframe containing generated data is displayed', () => cy.get('iframe.frame').should('be.visible'))

When('User intercepts ODM document generation request', () => cy.intercept('/api/odms/metadata/report?targets=OdmForm*').as('generateReportDocument'))

When('User intercepts ODM XMLS document generation request', () => cy.intercept('/api/odms/metadata/xmls/export?targets=OdmForm*').as('generateXmlsDocument'))

When('User waits for ODM document generation request', () => cy.wait('@generateReportDocument').then(request => expect(request.response.statusCode).to.eq(200)))

When('User waits for ODM XMLS document generation request', () => cy.wait('@generateXmlsDocument').then(request => expect(request.response.statusCode).to.eq(200)))
