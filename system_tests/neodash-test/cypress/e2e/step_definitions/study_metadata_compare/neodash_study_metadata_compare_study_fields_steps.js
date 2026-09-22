const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Then("The following selection displayed in the Selected Studies panel", (dataTable) =>{
    dataTable.hashes().forEach((element,k) => {
          const i=k+1
          cy.get('main .react-grid-item:eq(3) [data-field="Study_0"]').eq(i).should('have.text',element.row)
          cy.get('main .react-grid-item:eq(3) [data-field="Base_1"]').eq(i).should('have.text',element.base)
          cy.get('main .react-grid-item:eq(3) [data-field="Compare_2"]').eq(i).should('have.text',element.compare)
    })      
  })

  Then('The differences are shown in the Study field comparison panel with following differences',(dataTable)=>{
    dataTable.hashes().forEach((element,k) => {
      const i=k+1
          cy.get('main .react-grid-item:eq(0) [data-field="Study Field"]').eq(i).should('have.text',element.StudyField)
          cy.get('main .react-grid-item:eq(0) [data-field="Base"]').eq(i).should('have.text',element.Base)
          cy.get('main .react-grid-item:eq(0) [data-field="Compare"]').eq(i).should('have.text',element.Compare)
          cy.get('main .react-grid-item:eq(0) [data-field="Diff"]').eq(i).should('have.text',element.Diff)

    
    })
  })

Then('The Current Study Selection table shows values for the selected studies', () => {
  cy.get('[role="gridcell"][data-field="Study_0"]').should('have.length.greaterThan', 0)
})

Then('The Study Field Comparison table returns comparison values', () => {
  cy.get('[role="gridcell"][data-field="Study Field"]').should('have.length.greaterThan', 0)
})
