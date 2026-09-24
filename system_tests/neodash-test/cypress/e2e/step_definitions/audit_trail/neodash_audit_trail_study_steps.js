const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The user types {string} in the Select Start Date field',(startdate) => {
    cy.get('main .react-grid-item:eq(3) .MuiCardContent-root .ndl-input-wrapper').clear().type(startdate)
    cy.wait(200)
})

When('The user selects the first Study UID on version page',() => {
  cy.get('input[value^="Select Study UID"]').first().parents('.react-grid-item').first()
    .find('.MuiCardContent-root input').should('not.be.disabled').click()
  cy.wait(500)
  cy.get('[id^=autocomplete-option]').first().click()
  cy.wait(300)
})

When('The user selects the first Study Min Date Version',() => {
  cy.get('.MuiDataGrid-row [data-field="Study Min Date"] button', { timeout: 15000 })
    .first().click()
  cy.wait(300)
})

When('The user selects the first Study Max Date Version',() => {
  cy.get('.MuiDataGrid-row [data-field="Study Max Date"] button', { timeout: 15000 })
    .first().click()
  cy.wait(300)
})

When('The user selects the Action ID',() => {
  cy.get('.MuiDataGrid-row [data-field="Action ID"] button', { timeout: 15000 })
    .first().click()
  cy.wait(300)
})

Then('The Study Action ID card should not be empty',() => {
  cy.get('.react-grid-item').should(($items) => {
    const card = $items.filter(':has(input[value^="Action ID"])')
    expect(card.length, 'Action ID card should exist').to.be.greaterThan(0)
    const content = card.find('.MuiCardContent-root')
    expect(content.text().trim()).to.not.be.empty
  })
})

Then('The panel {string} should not contain errors', (panelName) => {
  cy.get('.react-grid-item').should(($items) => {
    const card = $items.filter(`:has(input[value^="${panelName}"])`)
    expect(card.length, `Card "${panelName}" should exist`).to.be.greaterThan(0)
    const content = card.find('.MuiCardContent-root')
    expect(content.length, `Card "${panelName}" should have content`).to.be.greaterThan(0)
    const text = content.text()
    expect(text).to.not.contain('Invalid input for function')
    expect(text).to.not.contain('Query returned no data')
  })
})
