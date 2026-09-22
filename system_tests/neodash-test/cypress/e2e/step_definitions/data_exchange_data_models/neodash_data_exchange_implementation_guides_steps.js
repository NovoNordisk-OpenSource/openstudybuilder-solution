const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
When('The user clicks {string} on the following implementation Sponsor Model', (select, dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(4) [data-field="name"]').eq(i).should('have.text',element.name)
        cy.get('main .react-grid-item:eq(4) [data-field="version"]').eq(i).should('have.text',element.version)
    })
    cy.get('main .react-grid-item').eq(4).within(() => {
        cy.contains('button', select).click();
    });
    cy.wait(300);
})

When('The user clicks {string} on the following Available Guide', (select, dataTable) => {
    dataTable.hashes().forEach((element) => {
        cy.get('main .react-grid-item:eq(0) [data-field="guide"]').eq(2).should('have.text',element.guide)
    })
    cy.get('main .react-grid-item:eq(0) [data-field="select"]').eq(2).within(() => {
        cy.contains('button', select).click();
      });
    cy.wait(300);
})

When('The user clicks {string} on the following Available Guide Version', (select, dataTable) => {
    dataTable.hashes().forEach((element) => {
        cy.get('main .react-grid-item:eq(1) [data-field="version"]').eq(1).should('have.text',element.version)
        cy.get('main .react-grid-item:eq(1) [data-field="implements"]').eq(1).should('have.text',element.implements)
    })
    cy.get('main .react-grid-item:eq(1) [data-field="select"]').eq(1).within(() => {
        cy.contains('button', select).click();
      });
    cy.wait(300);
})

When('The user clicks {string} on the following Dataset', (select, dataTable) => {
    dataTable.hashes().forEach((element) => {
        cy.get('main .react-grid-item:eq(2) [data-field="dataset"]').eq(2).should('have.text',element.dataset)
        cy.get('main .react-grid-item:eq(2) [data-field="implements"]').eq(2).should('have.text',element.implements)
    })
    cy.get('main .react-grid-item:eq(2) [data-field="select"]').eq(2).within(() => {
        cy.contains('button', select).click();
      });
    cy.wait(300);
})

When('The user clicks {string} on the following Guide Variable', (sponsormodel, dataTable) => {
    dataTable.hashes().forEach((element) => {
        cy.get('main .react-grid-item:eq(3) [data-field="variable"]').eq(1).should('have.text',element.variable)
        cy.get('main .react-grid-item:eq(3) [data-field="label"]').eq(1).should('have.text',element.label)
        cy.get('main .react-grid-item:eq(3) [data-field="description"]').eq(1).should('have.text',element.description)
        cy.get('main .react-grid-item:eq(3) [data-field="dataType"]').eq(1).should('have.text',element.dataType)
        cy.get('main .react-grid-item:eq(3) [data-field="length"]').eq(1).should('have.text',element.length)
        cy.get('main .react-grid-item:eq(3) [data-field="role"]').eq(1).should('have.text',element.role)
        cy.get('main .react-grid-item:eq(3) [data-field="codelist"]').eq(1).should('have.text',element.codelist)
        cy.get('main .react-grid-item:eq(3) [data-field="implements"]').eq(1).should('have.text',element.implements)
    })
    cy.get('main .react-grid-item:eq(3) [data-field="sponsormodel"]').eq(1).within(() => {
        cy.contains('button', sponsormodel).click();
      });
    cy.wait(300);
})

Then('The following guides are available in the Available Guides table', (dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(0) [data-field="guide"]').eq(i).should('have.text',element.guide)
    })
})

Then('The Versions - table should display the following', (dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(1) [data-field="version"]').eq(i).should('have.text',element.version)
        cy.get('main .react-grid-item:eq(1) [data-field="implements"]').eq(i).should('have.text',element.implements)
    })
})

Then('The Datasets table should display the following', (dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(2) [data-field="dataset"]').eq(i).should('have.text',element.dataset)
        cy.get('main .react-grid-item:eq(2) [data-field="implements"]').eq(i).should('have.text',element.implements)
    })
})

Then('The Variables - table should display the following', (dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(3) [data-field="variable"]').eq(i).should('have.text',element.variable)
        cy.get('main .react-grid-item:eq(3) [data-field="label"]').eq(i).should('have.text',element.label)
        cy.get('main .react-grid-item:eq(3) [data-field="description"]').eq(i).should('have.text',element.description)
        cy.get('main .react-grid-item:eq(3) [data-field="dataType"]').eq(i).should('have.text',element.dataType)
        cy.get('main .react-grid-item:eq(3) [data-field="length"]').eq(i).should('have.text',element.length)
        cy.get('main .react-grid-item:eq(3) [data-field="role"]').eq(i).should('have.text',element.role)
        cy.get('main .react-grid-item:eq(3) [data-field="codelist"]').eq(i).should('have.text',element.codelist)
        cy.get('main .react-grid-item:eq(3) [data-field="implements"]').eq(i).should('have.text',element.implements)
    })
})