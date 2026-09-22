const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Given('The neoDash {string} tab is selected', (string) => {
  cy.get('[data-testid="modal-wrapper"]').should('not.exist')
  cy.contains('[role="tab"]', string).click()
  cy.get('input#standard-outlined', { timeout: 15000 }).should('exist')
});

Given('The {string} page is opened', (page) => {
  cy.get('[data-testid="side-nav-expand-btn"]').click()
  cy.contains('button', page).click()
  cy.get('[data-testid="modal-wrapper"]').should('not.exist')
  cy.wait(500)
})

When('The user navigates to the {string} page',(string)=>{
  cy.contains('[role="tab"]', string).click()
})


Then('The following set of neoDash reports are displayed', (dataTable) => {
    dataTable.hashes().forEach((element) => {
        cy.get('[value*="' + element.report + '"]').should('exist')
        })
    })   

Then('The {string} report returns a value', (reportName) => {
    cy.get(`input[value^="${reportName}"]`, { timeout: 20000 })
        .first()
        .parents('.react-grid-item')
        .first()
        .find('.MuiCardContent-root')
        .first()
        .should(($content) => {
            const text = ($content.text() || '').replace(/\u00a0/g, ' ').trim()
            expect(text, `'${reportName}' returned no data (Query returned no data) - possible bug`).to.not.contain('Query returned no data')
            const gridcells = $content.find('[role="gridcell"]')
            if (gridcells.length) {
                const hasValue = [...gridcells].some((c) => (c.innerText || '').replace(/\u00a0/g, ' ').trim() !== '')
                expect(hasValue, `'${reportName}' grid returned no values (empty) - possible bug`).to.be.true
            } else {
                expect(text, `'${reportName}' returned no value (empty) - possible bug`).to.not.equal('')
            }
        })
})