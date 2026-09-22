const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Then('The Parent Syntax Templates using selected Template Parameter and\\/or Value table should display the following',(dataTable) => {
    dataTable.hashes().forEach((element,k) => {
      const i=k+1
      cy.get('main .react-grid-item:eq(0) [data-field="Library"]').eq(i).should('have.text',element.Library)
      cy.get('main .react-grid-item:eq(0) [data-field="Seq Num"]').eq(i).should('have.text',element.Seq_Num)
      cy.get('main .react-grid-item:eq(0) [data-field="Type"]').eq(i).should('have.text',element.Type)
      cy.get('main .react-grid-item:eq(0) [data-field="Subtype"]').eq(i).should('have.text',element.SubType)
      cy.get('main .react-grid-item:eq(0) [data-field="Template Parameter"]').eq(i).should('have.text',element.TemplateParameter)
      cy.get('main .react-grid-item:eq(0) [data-field="Template Root UID"]').eq(i).should('have.text',element.struid)
    })
  })