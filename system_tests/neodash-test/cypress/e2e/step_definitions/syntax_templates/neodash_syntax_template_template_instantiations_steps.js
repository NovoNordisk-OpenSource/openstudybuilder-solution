const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Then('The Template Instantiations using selected Template Parameter and\\/or Value table should display the following', (dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(0) [data-field="Library"]').eq(i).should('have.text',element.Library)
        cy.get('main .react-grid-item:eq(0) [data-field="SequenceNumber"]').eq(i).should('have.text',element.SequenceNumber)
        cy.get('main .react-grid-item:eq(0) [data-field="Type"]').eq(i).should('have.text',element.Type)
        cy.get('main .react-grid-item:eq(0) [data-field="SubType"]').eq(i).should('have.text',element.SubType)
        cy.get('main .react-grid-item:eq(0) [data-field="InstanceTemplate"]').eq(i).should('have.text',element.InstanceTemplate)
        cy.get('main .react-grid-item:eq(0) [data-field="ParentTemplate"]').eq(i).should('have.text',element.ParentTemplate)
        cy.get('main .react-grid-item:eq(0) [data-field="TemplateParameter"]').eq(i).should('have.text',element.TemplateParameter)
        cy.get('main .react-grid-item:eq(0) [data-field="ParameterValues"]').eq(i).should('have.text',element.ParameterValues)
      })
})