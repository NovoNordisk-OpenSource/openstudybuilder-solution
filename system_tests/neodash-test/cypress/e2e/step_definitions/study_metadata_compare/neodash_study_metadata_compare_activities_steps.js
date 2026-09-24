const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
Cypress.env()
  
Then('The Detailed Flowchart compare between base and compare study panel displays the following rows',(dataTable)=>{
    dataTable.hashes().forEach((element,k) => {
      const i=k+1
          cy.get('main .react-grid-item:eq(0) [data-field="Change Type"]').eq(i).invoke('text').then((text) => {
              expect(text.replace(/\u00a0/g, ' ')).contains(element.ChangeType)
          })
          cy.get('main .react-grid-item:eq(0) [data-field="Flowchart Group (Base)"]').eq(i).invoke('text').then((text) => {
              expect(text.replace(/\u00a0/g, ' ')).contains(element.FlowchartGroupBase)
          })
          cy.get('main .react-grid-item:eq(0) [data-field="Activity Group (Base)"]').eq(i).invoke('text').then((text) => {
              expect(text.replace(/\u00a0/g, ' ')).contains(element.ActivityGroupBase)
          })
          cy.get('main .react-grid-item:eq(0) [data-field="Activity Subgroup (Base)"]').eq(i).invoke('text').then((text) => {
              expect(text.replace(/\u00a0/g, ' ')).contains(element.ActivitySubgroupBase)
          })
          cy.get('main .react-grid-item:eq(0) [data-field="Flowchart Group (Compare)"]').eq(i).invoke('text').then((text) => {      
              expect(text.replace(/\u00a0/g, ' ')).contains(element.FlowchartGroupCompare)
          })
          cy.get('main .react-grid-item:eq(0) [data-field="Activity Group (Compare)"]').eq(i).invoke('text').then((text) => {
              expect(text.replace(/\u00a0/g, ' ')).contains(element.ActivityGroupCompare)
          })
          cy.get('main .react-grid-item:eq(0) [data-field="Activity Subgroup (Compare)"]').eq(i).invoke('text').then((text) => {
              expect(text.replace(/\u00a0/g, ' ')).contains(element.ActivitySubgroupCompare)
          })
          cy.get('main .react-grid-item:eq(0) [data-field="Activity Detail"]').eq(i).invoke('text').then((text) => {
              expect(text.replace(/\u00a0/g, ' ')).contains(element.ActivityDetail)
          })
    })
  })

Then('The Detailed Flowchart Compare table returns values', () => {
  cy.get('[role="gridcell"][data-field="Activity Detail"]')
    .should(($cells) => {
      const hasValue = [...$cells].some((c) => (c.innerText || '').replace(/\u00a0/g, ' ').trim() !== '')
      expect(hasValue, 'Detailed Flowchart Compare table returned no values (empty) - possible bug').to.be.true
    })
})

  