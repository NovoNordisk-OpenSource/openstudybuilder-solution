const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Then('The differences are shown in the Objectives comparison panel with following differences',(dataTable)=>{
    dataTable.hashes().forEach((element,k) => {
      const i=k+1
          cy.get('main .react-grid-item:eq(2) [data-field="Number"]').eq(i).invoke('text').then((text) => {
            // remove the space char :&nbsp;
            expect(text.replace(/\u00a0/g, ' ')).equal(element.number)
          })
          cy.get('main .react-grid-item:eq(2) [data-field="Base - Objective"]').eq(i).invoke('text').then((text) => {
            // remove the space char :&nbsp;
            expect(text.replace(/\u00a0/g, ' ')).equal(element.baseObjective)
          })
          
          cy.get('main .react-grid-item:eq(2) [data-field="Compare - Objective"]').eq(i).invoke('text').then((text) => {
            // remove the space char :&nbsp;
            expect(text.replace(/\u00a0/g, ' ')).equal(element.compareObjective)
          })
          cy.get('main .react-grid-item:eq(2) [data-field="Diff"]').eq(i).invoke('text').then((text) => {
            // remove the space char :&nbsp;
            expect(text.replace(/\u00a0/g, ' ')).equal(element.diff)
          })
   
    })
  })

  Then('The differences are shown in the Endpoints \\(by Objective\\) comparison panel with following differences',(dataTable)=>{
    dataTable.hashes().forEach((element,k) => {
      const i=k+1
          cy.get('main .react-grid-item:eq(1) [data-field="Number"]').eq(i).invoke('text').then((text) => {
            expect(text.replace(/\u00a0/g, ' ')).equal(element.number)
          })
          cy.get('main .react-grid-item:eq(1) [data-field="Objective"]').eq(i).invoke('text').then((text) => {
            expect(text.replace(/\u00a0/g, ' ')).equal(element.objective)
          })
          cy.get('main .react-grid-item:eq(1) [data-field="Base - Endpoint"]').eq(i).invoke('text').then((text) => {
            expect(text.replace(/\u00a0/g, ' ')).equal(element.baseEndpoint)
          })
          cy.get('main .react-grid-item:eq(1) [data-field="Compare - Endpoint"]').eq(i).invoke('text').then((text) => {
            expect(text.replace(/\u00a0/g, ' ')).equal(element.compareEndpoint)
          })
          cy.get('main .react-grid-item:eq(1) [data-field="Diff"]').eq(i).invoke('text').then((text) => {
            expect(text.replace(/\u00a0/g, ' ')).equal(element.diff)
          })

    
    })
  })

Then('The Objectives table returns comparison values', () => {
  cy.get('[role="gridcell"][data-field="Base - Objective"], [role="gridcell"][data-field="Compare - Objective"]')
    .should(($cells) => {
      const hasValue = [...$cells].some((c) => (c.innerText || '').replace(/\u00a0/g, ' ').trim() !== '')
      expect(hasValue, 'Objectives table returned no values (empty) - possible bug').to.be.true
    })
})

Then('The Endpoints \\(by Objective\\) table returns comparison values', () => {
  cy.get('[role="gridcell"][data-field="Base - Endpoint"]').should('have.length.greaterThan', 0)
})
