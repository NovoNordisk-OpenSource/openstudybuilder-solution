const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The user filter the Visit Name column to {string}',(str)=> {
  cy.log(cy.get('main .react-grid-item:eq(2) [data-field="Visit Name"]'))
  cy.get('main .react-grid-item:eq(2) [data-field="Visit Name"]').find('button[title="Menu"]').click({ force : true })
  cy.get('.MuiButtonBase-root').contains('Filter').wait(50).click()
  cy.get('.MuiDataGrid-filterFormValueInput .MuiInputBase-input').type(str)
  cy.wait(500)
})   


Then('The differences are shown in the Visit attribute changes panel with following differences',(dataTable)=>{
    dataTable.hashes().forEach((element,k) => {
      const i=k+1
          cy.get('main .react-grid-item:eq(2) [data-field="Visit Name"]').eq(i).invoke('text').then((text) => {
              expect(text.replace(/\u00a0/g, ' ')).contains(element.visitName)
          })
          cy.get('main .react-grid-item:eq(2) [data-field="Visit Number"]').eq(i).invoke('text').then((text) => {
            cy.log(text)
              expect(text.replace(/\u00a0/g, ' ')).contains(element.visitNumber)
          })
          cy.get('main .react-grid-item:eq(2) [data-field="Visit Property Type"]').eq(i).invoke('text').then((text) => {
            cy.log(text)
              expect(text.replace(/\u00a0/g, ' ')).contains(element.visitPropType)
          })
          cy.get('main .react-grid-item:eq(2) [data-field="Base"]').eq(i).invoke('text').then((text) => {
            cy.log(text)
              expect(text.replace(/\u00a0/g, ' ')).contains(element.base)
          })
          cy.get('main .react-grid-item:eq(2) [data-field="Compare"]').eq(i).invoke('text').then((text) => {
            cy.log(text)          
              expect(text.replace(/\u00a0/g, ' ')).contains(element.comp)
          })
          cy.get('main .react-grid-item:eq(2) [data-field="Diff"]').eq(i).invoke('text').then((text) => {
            cy.log(text)
              expect(text.replace(/\u00a0/g, ' ')).contains(element.diff)
          })
  })
})

Then('The Change Type table returns values', () => {
  cy.get('[role="gridcell"][data-field="Status"]')
    .should(($cells) => {
      const hasValue = [...$cells].some((c) => (c.innerText || '').replace(/\u00a0/g, ' ').trim() !== '')
      expect(hasValue, 'Change Type table returned no values (empty) - possible bug').to.be.true
    })
})

Then('The Visit Attribute Changes table returns values', () => {
  cy.get('[role="gridcell"][data-field="Visit Property Type"]')
    .should(($cells) => {
      const hasValue = [...$cells].some((c) => (c.innerText || '').replace(/\u00a0/g, ' ').trim() !== '')
      expect(hasValue, 'Visit Attribute Changes table returned no values (empty) - possible bug').to.be.true
    })
})
