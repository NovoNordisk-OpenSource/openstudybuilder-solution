const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The user clicks {string} in the Select Template Parameter selector', (templateParameter) => {
  cy.get('.MuiAutocomplete-listbox .MuiAutocomplete-option').contains(templateParameter).click()
    cy.wait(200)
})

When('The user types {string} in the Select Template Parameter selector',(param) =>{
  cy.get('main .react-grid-item:eq(1) .MuiCardContent-root .MuiInputBase-input').should('not.be.disabled').clear().type(param)
  cy.wait(200)
})

When('The user types {string} in the Select Parameter Value selector', (parameterValue) => {
    cy.get('main .react-grid-item:eq(3) .MuiCardContent-root .MuiInputBase-input').should('not.be.disabled').type(parameterValue)
      cy.wait(200)
  })

When('The user clicks {string} in the Select Parameter Value selector', (parameterValue) => {
    cy.get('.MuiAutocomplete-listbox .MuiAutocomplete-option').contains(parameterValue).click()
      cy.wait(200)
  }) 

  When('The user switches to the {string} page',(string) => {
    cy.document().then((doc) => {
          if (string == 'Template Instantiations') {
              doc.querySelector("#tab_5> button").click()
              cy.wait(200)
          }
          if (string == 'Parent Templates') {
            doc.querySelector("#tab_2> button").click()
            cy.wait(200)
        }
        if (string == 'All Templates') {
          doc.querySelector("#tab_4> button").click()
          cy.wait(200)
        }
        if (string == 'Study Usage') {
          doc.querySelector("#tab_6> button").click()
          cy.wait(200)
        }
        if (string == 'Templates by Library') {
          doc.querySelector("#tab_7> button").click()
          cy.wait(200)
        }
      })
  });

Then('The following is displayed in the Template Parameters table', (dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(0) [data-field="TemplateParameter"]').eq(i).should('have.text',element.TemplateParameter)
      })
})

Then('The following is displayed in the Template Parameter Values table', (dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(2) [data-field="Name"]').eq(i).should('have.text',element.Name)
        cy.get('main .react-grid-item:eq(2) [data-field="SentenceCaseName"]').eq(i).should('have.text',element.SentenceCaseName)
      })
})

Then('The Selected Template Parameter and\\/or Value table should display the following', (dataTable) => {
  dataTable.hashes().forEach((element,k) => {
      const i=k+1
      cy.get('main .react-grid-item:eq(1) [data-field="Selected Parameters"]').eq(i).should('have.text',element.Selected_Parameters)
      cy.get('main .react-grid-item:eq(1) [data-field="Selected Values"]').eq(i).should('have.text',element.Selected_Values)
  })
})