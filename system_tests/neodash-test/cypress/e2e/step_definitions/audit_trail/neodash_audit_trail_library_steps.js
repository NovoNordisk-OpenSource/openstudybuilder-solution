const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The user types {string} in the Select Start Date field on lib page',(startdate) =>{
    cy.get('main .react-grid-item:eq(1) .MuiCardContent-root .ndl-input-wrapper').clear().type(startdate)
    cy.wait(200)
})

When('The user types {string} in the Select End Date field on lib page',(enddate) =>{
  cy.get('main .react-grid-item:eq(2) .MuiCardContent-root .ndl-input-wrapper').clear().type(enddate)
    cy.wait(200)
})

When('The user types {string} in the Select User selector on lib page',(user) =>{
  cy.get('main .react-grid-item:eq(0) .MuiCardContent-root .MuiInputBase-input').should('not.be.disabled').type(user)
    cy.wait(200)
})

When('The user chooses {string} in the Select User selector on lib page',(user) =>{
    cy.get('.MuiAutocomplete-listbox .MuiAutocomplete-option').contains(user).click()
    cy.wait(200)
})

When('The user chooses {string} as the Action ID from the Actions Table on lib page',(actionid) =>{
  cy.get('main .react-grid-item:eq(3) [data-field="Action ID"]').contains('button', actionid).click()
  cy.wait(300)
})

When('The user selects the first Action ID from the Actions Table on lib page',() =>{
  cy.get('main .react-grid-item:eq(3) .MuiDataGrid-row [data-field="Action ID"] button').first().click()
  cy.wait(300)
})

Then('The Lib Actions Table displays the following',(dataTable) => {
  dataTable.hashes().forEach((element,k) => {
    const i=k+1
    cy.get('main .react-grid-item:eq(3) [data-field="Timestamp"]').eq(i).should('have.text',element.Timestamp)
    cy.get('main .react-grid-item:eq(3) [data-field="User"]').eq(i).should('have.text',element.User)
    cy.get('main .react-grid-item:eq(3) [data-field="Status"]').eq(i).should('have.text',element.Status)
    cy.get('main .react-grid-item:eq(3) [data-field="Action ID"]').eq(i).should('have.text',element.Action_ID)
    cy.get('main .react-grid-item:eq(3) [data-field="Component ID"]').eq(i).should('have.text',element.Component_ID)
    cy.get('main .react-grid-item:eq(3) [data-field="Action Type"]').eq(i).should('have.text',element.Action_Type)
    cy.get('main .react-grid-item:eq(3) [data-field="Component Labels"]').eq(i).should('have.text',element.Component_Labels)
  })
})

Then('The Lib Action ID card displays the selected ID',(dataTable) => {
  dataTable.hashes().forEach((element) => {
    cy.get('main .react-grid-item:eq(4) .MuiCardContent-root').should('have.text',element.Action_ID)
  })
})

Then('The Lib Action ID card should not be empty',() => {
  cy.get('main .react-grid-item:eq(4) .MuiCardContent-root')
    .invoke('text').should('not.be.empty')
})

Then('The Lib Version\\/Status Changes Table displays the following',(dataTable) => {
  dataTable.hashes().forEach((element,k) => {
    const i=k+1
    cy.get('main .react-grid-item:eq(6) [data-field="Timestamp"]').eq(i).should('have.text',element.Timestamp)
    cy.get('main .react-grid-item:eq(6) [data-field="User"]').eq(i).should('have.text',element.User)
    cy.get('main .react-grid-item:eq(6) [data-field="Action ID"]').eq(i).should('have.text',element.Action_ID)
    cy.get('main .react-grid-item:eq(6) [data-field="Component ID"]').eq(i).should('have.text',element.Component_ID)
    cy.get('main .react-grid-item:eq(6) [data-field="Old Version"]').eq(i).should('have.text',element.Old_Version)
    cy.get('main .react-grid-item:eq(6) [data-field="New Version"]').eq(i).should('have.text',element.New_Version)
    cy.get('main .react-grid-item:eq(6) [data-field="Old Status"]').eq(i).should('have.text',element.Old_Status)
    cy.get('main .react-grid-item:eq(6) [data-field="New Status"]').eq(i).should('have.text',element.New_Status)
  })
})


Then('The Lib Field Value Changes table displays the following',(dataTable) => {
  dataTable.hashes().forEach((element,k) => {
    const i=k+1
    cy.get('main .react-grid-item:eq(7) [data-field="Timestamp"]').eq(i).should('have.text',element.Timestamp)
    cy.get('main .react-grid-item:eq(7) [data-field="Component ID"]').eq(i).should('have.text',element.Component_ID)
    cy.get('main .react-grid-item:eq(7) [data-field="Field"]').eq(i).should('have.text',element.Field)
    cy.get('main .react-grid-item:eq(7) [data-field="Old Value"]').eq(i).should('have.text',element.Old_Value)
    cy.get('main .react-grid-item:eq(7) [data-field="New Value"]').eq(i).should('have.text',element.New_Value)
    
  })
})

Then('The Lib Old Component ID card displays the previous ID',(dataTable) => {
  dataTable.hashes().forEach((element) => {
    cy.get('main .react-grid-item:eq(10) .MuiCardContent-root').should('have.text',element.Old_Component_ID)
  })
})

Then('The Lib New Component ID card displays the current ID \\(at the time of the action\\)',(dataTable) => {
  dataTable.hashes().forEach((element) => {
    cy.get('main .react-grid-item:eq(9) .MuiCardContent-root').should('have.text',element.New_Component_ID)
  })
})


