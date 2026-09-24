const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Then('The differences are shown in the Study criteria comparison panel with following differences',(dataTable)=>{
    dataTable.hashes().forEach((element,k) => {
      const i=k+1
          cy.get('main .react-grid-item:eq(1) [data-field="Base - Criteria"]').eq(i).invoke('text').then((text) => {
            expect(text.replace(/\u00a0/g, ' ')).equal(element.baseCriteria)
          })
          cy.get('main .react-grid-item:eq(1) [data-field="Compare - Criteria"]').eq(i).invoke('text').then((text) => {
            expect(text.replace(/\u00a0/g, ' ')).equal(element.compareCriteria)
          })
          cy.get('main .react-grid-item:eq(1) [data-field="Diff"]').eq(i).invoke('text').then((text) => {
            expect(text.replace(/\u00a0/g, ' ')).equal(element.diff)
          })
   
    })
  })

Then('The Study Criteria table returns comparison values', () => {
  cy.get('[role="gridcell"][data-field="Base - Criteria"], [role="gridcell"][data-field="Compare - Criteria"]')
    .should(($cells) => {
      const hasValue = [...$cells].some((c) => (c.innerText || '').replace(/\u00a0/g, ' ').trim() !== '')
      expect(hasValue, 'Study Criteria table returned no values (empty) - possible bug').to.be.true
    })
})

  