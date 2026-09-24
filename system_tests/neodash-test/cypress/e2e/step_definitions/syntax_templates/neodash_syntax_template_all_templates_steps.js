const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Then('The All Templates using selected Template Parameter and\\/or Value table should display the following', (dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(0) [data-field="Library"]').eq(i).should('have.text',element.Library)
        cy.get('main .react-grid-item:eq(0) [data-field="Seq Num"]').eq(i).should('have.text',element.SeqNum)
        cy.get('main .react-grid-item:eq(0) [data-field="Type"]').eq(i).should('have.text',element.Type)
        cy.get('main .react-grid-item:eq(0) [data-field="Template"]').eq(i).should('have.text',element.Template)
        cy.get('main .react-grid-item:eq(0) [data-field="Template Parameter"]').eq(i).should('have.text',element.TemplateParameter)
        cy.get('main .react-grid-item:eq(0) [data-field="Template Type"]').eq(i).should('have.text',element.TemplateType)
      })
})