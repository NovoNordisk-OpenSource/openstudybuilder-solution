const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The user selects version {float} in the Select Base panel', (version) => {
    cy.get('main .react-grid-item:eq(1) .MuiDataGrid-row [data-field="Version"]').each((item,index) => {
    const inst=item.text()
    const i = index
    if (inst==version){
      cy.get('main .react-grid-item:eq(1) .MuiDataGrid-row [data-field="Select"]').eq(i).click()
     }
    })
    cy.wait(300)
}) 

When('The user selects date: {string} in the Select Base panel', (date) => {
  cy.get('main .react-grid-item:eq(1) .MuiDataGrid-row [data-field="Date"]').each((item,index) => {
  const inst=item.text()
  const i = index
  if (inst==date){
    cy.get('main .react-grid-item:eq(1) .MuiDataGrid-row [data-field="Select"]').eq(i).click()
   }
  })
  cy.wait(300)
}) 

When('The user selects version {float} in the Select Compare panel', (version) => {
    cy.get('main .react-grid-item:eq(2) [data-field="Version"]').each((item,index) => {
        const inst=item.text()
        const i = index
        if (inst==version){
          cy.get('main .react-grid-item:eq(2) [data-field="Select"]').eq(i).click()
         }
        })
    cy.wait(300)
  })

  When('The user selects date: {string} in the Select Compare panel', (date) => {
    cy.get('main .react-grid-item:eq(2) [data-field="Date"]').each((item,index) => {
        const inst=item.text()
        const i = index
        if (inst==date){
          cy.get('main .react-grid-item:eq(2) [data-field="Select"]').eq(i).click()
         }
        })
    cy.wait(300)
  })

When('The the Show only differences is set to {string}', (diff_only) => {
  cy.get('main .react-grid-item:eq(4) .MuiCardContent-root .MuiInputBase-input').should('not.be.disabled').click()
      cy.get('.MuiAutocomplete-listbox .MuiAutocomplete-option').contains(diff_only).click()
      cy.wait(300)
}
)

When('The user selects the following project in Select Projects panel',(dataTable)=>{
  dataTable.hashes().forEach((element) => {
    cy.get('main .react-grid-item:eq(0) .MuiCardContent-root .MuiInputBase-input').should('not.be.disabled').click().type(element.project)
    cy.get('.MuiAutocomplete-listbox .MuiAutocomplete-option').contains(element.project).click()
    
  }) 
    cy.wait(200)
  cy.get('main .react-grid-item:eq(0)').click()
  
})

Then("The following selection is displayed in the Selected Studies panel", (dataTable) =>{
    dataTable.hashes().forEach((element,k) => {
          const i=k+1
          cy.get('main .react-grid-item:eq(3) [data-field="Study_0"]').eq(i).should('have.text',element.row)
          cy.get('main .react-grid-item:eq(3) [data-field="Base_1"]').eq(i).should('have.text',element.base)
          cy.get('main .react-grid-item:eq(3) [data-field="Compare_2"]').eq(i).should('have.text',element.compare)
    })      
  })

When('The user selects the first project in the Select Projects panel', () => {
  cy.get('main .react-grid-item:eq(0) .MuiCardContent-root .MuiInputBase-input').should('not.be.disabled').click()
  cy.wait(500)
  cy.get('.MuiAutocomplete-listbox .MuiAutocomplete-option').eq(0).click()
  cy.get('main .react-grid-item:eq(0) .MuiCardContent-root .MuiInputBase-input').type('{esc}')
  cy.wait(300)
})

When('The user selects the first study in the Select Base table', () => {
  cy.get('main .react-grid-item:eq(1) .MuiDataGrid-row').eq(0).within(() => {
    cy.get('[data-field="Trial ID"]').invoke('text').as('baseTrialId')
    cy.get('[data-field="Date"]').invoke('text').as('baseDate')
    cy.get('[data-field="Version"]').invoke('text').as('baseVersion')
    cy.get('[data-field="Latest"]').invoke('text').as('baseLatest')
    cy.get('[data-field="Status"]').invoke('text').as('baseStatus')
  })
  cy.get('main .react-grid-item:eq(1) .MuiDataGrid-row [data-field="Select"]').eq(0).click()
  cy.wait(300)
})

When('The user selects a different study in the Select Compare table', () => {
  cy.get('main .react-grid-item:eq(2) .MuiDataGrid-row').eq(1).within(() => {
    cy.get('[data-field="Trial ID"]').invoke('text').as('compareTrialId')
    cy.get('[data-field="Date"]').invoke('text').as('compareDate')
    cy.get('[data-field="Version"]').invoke('text').as('compareVersion')
    cy.get('[data-field="Latest"]').invoke('text').as('compareLatest')
    cy.get('[data-field="Status"]').invoke('text').as('compareStatus')
  })
  cy.get('main .react-grid-item:eq(2) .MuiDataGrid-row [data-field="Select"]').eq(1).click()
  cy.wait(300)
})

Then('The Selected Studies panel displays two different studies', function () {
  const normalise = (text) => text.replace(/\s/g, '').toLowerCase()
  const base = {
    trialid: this.baseTrialId,
    date: this.baseDate,
    version: this.baseVersion,
    latest: this.baseLatest,
    status: this.baseStatus,
  }
  const compare = {
    trialid: this.compareTrialId,
    date: this.compareDate,
    version: this.compareVersion,
    latest: this.compareLatest,
    status: this.compareStatus,
  }
  cy.get('main .react-grid-item:eq(3) [data-field="Study_0"]').each(($label, index) => {
    const key = normalise($label.text())
    if (base[key] !== undefined) {
      cy.get('main .react-grid-item:eq(3) [data-field="Base_1"]').eq(index).should('have.text', base[key])
      cy.get('main .react-grid-item:eq(3) [data-field="Compare_2"]').eq(index).should('have.text', compare[key])
    }
  })
})

Given('Two studies are selected for comparison', () => {
  cy.get('[data-testid="modal-wrapper"]').should('not.exist')
  cy.contains('[role="tab"]', 'Select studies').click()
  cy.get('input#standard-outlined', { timeout: 15000 }).should('exist')
  // pick the first available project so the Base/Compare tables are populated
  cy.get('main .react-grid-item:eq(0) .MuiCardContent-root .MuiInputBase-input').should('not.be.disabled').click()
  cy.wait(500)
  cy.get('.MuiAutocomplete-listbox .MuiAutocomplete-option').eq(0).click()
  cy.get('main .react-grid-item:eq(0) .MuiCardContent-root .MuiInputBase-input').type('{esc}')
  cy.wait(300)
  cy.get('main .react-grid-item:eq(1) .MuiDataGrid-row [data-field="Select"]').eq(0).click()
  cy.wait(300)
  cy.get('main .react-grid-item:eq(2) .MuiDataGrid-row [data-field="Select"]').eq(1).click()
  cy.wait(300)
})