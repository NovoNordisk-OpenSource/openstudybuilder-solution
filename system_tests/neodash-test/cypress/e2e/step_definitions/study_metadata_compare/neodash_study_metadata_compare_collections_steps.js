const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The user filter the Change Type column to {string}',(str)=> {
  cy.log(cy.get('main .react-grid-item:eq(0) [data-field="Change Type"]'))
  cy.get('main .react-grid-item:eq(0) [data-field="Change Type"]').find('button[title="Menu"]').click({ force : true })
  cy.get('.MuiButtonBase-root').contains('Filter').click()
  cy.get('.MuiDataGrid-filterFormValueInput .MuiInputBase-input').type(str)
  cy.wait(500)
})   

Then('The Planned collections at visits panel displays the following rows',(dataTable)=>{
    dataTable.hashes().forEach((element,k) => {
      const i=k+1
          cy.get('main .react-grid-item:eq(0) [data-field="Visit ID"]').eq(i).invoke('text').then((text) => {
              expect(text.replace(/\u00a0/g, ' ')).contains(element.VisitID)
          })
          cy.get('main .react-grid-item:eq(0) [data-field="Visit Short Label"]').eq(i).invoke('text').then((text) => {
              expect(text.replace(/\u00a0/g, ' ')).contains(element.VisitShortLabel)
          })
          cy.get('main .react-grid-item:eq(0) [data-field="Activity"]').eq(i).invoke('text').then((text) => {
              expect(text.replace(/\u00a0/g, ' ')).contains(element.Activity)
          })
          cy.get('main .react-grid-item:eq(0) [data-field="Base - collection"]').eq(i).invoke('text').then((text) => {
              expect(text.replace(/\u00a0/g, ' ')).contains(element.Base)
          })
          cy.get('main .react-grid-item:eq(0) [data-field="Compare - collection"]').eq(i).invoke('text').then((text) => {       
              expect(text.replace(/\u00a0/g, ' ')).contains(element.Compare)
          })
          cy.get('main .react-grid-item:eq(0) [data-field="Change Type"]').eq(i).invoke('text').then((text) => {
              expect(text.replace(/\u00a0/g, ' ')).contains(element.ChangeType)
          })
   
    })
  })

Then('The Planned Collections at Visits table returns values', () => {
  cy.get('[role="gridcell"][data-field="Activity"]')
    .should(($cells) => {
      const hasValue = [...$cells].some((c) => (c.innerText || '').replace(/\u00a0/g, ' ').trim() !== '')
      expect(hasValue, 'Planned Collections at Visits table returned no values (empty) - possible bug').to.be.true
    })
})

  