const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The user clicks {string} on the following Sponsor Model', (select, dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(5) [data-field="name"]').eq(i).should('have.text',element.name)
        cy.get('main .react-grid-item:eq(5) [data-field="version"]').eq(i).should('have.text',element.version)
    })
    cy.get('main .react-grid-item').eq(5).within(() => {
        cy.contains('button', select).click();
      });
    cy.wait(300);
})

When('The user clicks {string} on the following Available Model', (select, dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(0) [data-field="model"]').eq(i).should('have.text',element.model)
    })
    cy.get('main .react-grid-item').eq(0).within(() => {
        cy.contains('button', select).click();
      });
    cy.wait(300);
})

When('The user clicks {string} on the following Model Version', (select, dataTable) => {
    dataTable.hashes().forEach((element) => {
        cy.get('main .react-grid-item:eq(1) [data-field="version"]').eq(3).should('have.text',element.version)
    })
    cy.get('main .react-grid-item:eq(1) [data-field="select"]').eq(3).within(() => {
        cy.contains('button', select).click();
      });
    cy.wait(300);
})

When('The user clicks {string} on the following Sponsor Version on the Model tab', (select, dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(5) [data-field="version"]').eq(i).should('have.text',element.version)
        cy.get('main .react-grid-item:eq(5) [data-field="name"]').eq(i).should('have.text',element.name)
    })
    cy.get('main .react-grid-item:eq(5)').eq(0).within(() => {
        cy.contains('button', select).click();
      });
    cy.wait(300);
})

When('The user clicks {string} on the following Model Class', (select, dataTable) => {
    dataTable.hashes().forEach((element) => {
        cy.get('main .react-grid-item:eq(2) [data-field="class"]').each((item,index) => {
            const inst=item.text()
            const i = index-1
            if (inst==element.class){
              cy.get(`main .react-grid-item:eq(2) [data-id="${i}"] [data-field="select"]`).click()
              cy.log(`The select: ${inst}, at index ${i}`)
             }
            })
          })
          cy.wait(300)
})

When('The user clicks {string} on the following Variable Class', (select, dataTable) => {
    dataTable.hashes().forEach((element) => {        
        cy.get('main .react-grid-item:eq(3) [data-field="variable"]').each((item,index) => {
            const inst=item.text()
            const i = index-1
            if (inst==element.variable){
              cy.get(`main .react-grid-item:eq(3) [data-id="${i}"] [data-field="sponsormodel"]`).click()
              cy.log(`The select: ${inst}, at index ${i}`)
             }
            })
          })
    cy.wait(300);
})

Then('The following models are available in the Available Models table', (dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(0) [data-field="model"]').eq(i).should('have.text',element.model)
    })
})

Then('The table title should change to the following', (dataTable) => {
    dataTable.hashes().forEach((element) => {
        cy.get('input[id="standard-outlined"]').each((items,index) => {
          const value = Cypress.$(items).val();
            if (index == element.no){
               expect(value).to.contain(element.Table_Name)
            }
        })
     })
})

Then('The Versions table should display the following', (dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(1) [data-field="version"]').eq(i).should('have.text',element.version)
    })
})

Then('The Classes table should display the following', (dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(2) [data-field="class"]').eq(i).should('have.text',element.class)
    })
})

Then('The Impl. by card should display the following', (dataTable) => {
    dataTable.hashes().forEach((element) => {
        cy.get('main .react-grid-item:eq(4) .MuiCardContent-root').should('have.text',element.text)
    })
})

Then('The Variable Classes table should display the following', (dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(3) [data-field="variable"]').eq(i).should('have.text',element.variable)
        cy.get('main .react-grid-item:eq(3) [data-field="label"]').eq(i).should('have.text',element.label)
        cy.get('main .react-grid-item:eq(3) [data-field="role"]').eq(i).should('have.text',element.role)
        cy.get('main .react-grid-item:eq(3) [data-field="length"]').eq(i).should('have.text',element.length)
        cy.get('main .react-grid-item:eq(3) [data-field="qualifies"]').eq(i).should('have.text',element.qualifies)
        cy.get('main .react-grid-item:eq(3) [data-field="origin"]').eq(i).should('have.text',element.origin)
    })
})