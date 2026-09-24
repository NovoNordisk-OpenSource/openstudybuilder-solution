const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

When('The user clicks {string} on the following Sponsor Version', (select, dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(0) [data-field="version"]').eq(i).should('have.text',element.version)
        cy.get('main .react-grid-item:eq(0) [data-field="extends"]').eq(i).should('have.text',element.extends)
        cy.get('main .react-grid-item:eq(0) [data-field="name"]').eq(i).should('have.text',element.name)
    })
    cy.get('main .react-grid-item:eq(0)').eq(0).within(() => {
        cy.contains('button', select).click();
      });
    cy.wait(300);
})

When('The user clicks {string} on the following Sponsor Dataset', (select, dataTable) => {
    dataTable.hashes().forEach((element) => {
        cy.get('main .react-grid-item:eq(1) [data-field="uid"]').eq(2).should('have.text',element.uid)
        cy.get('main .react-grid-item:eq(1) [data-field="label"]').eq(2).should('have.text',element.label)
        cy.get('main .react-grid-item:eq(1) [data-field="basic_std"]').eq(2).should('have.text',element.basic_std)
        cy.get('main .react-grid-item:eq(1) [data-field="purpose"]').eq(2).should('have.text',element.purpose)
        cy.get('main .react-grid-item:eq(1) [data-field="ig_comment"]').eq(2).should('have.text',element.ig_comment)
        cy.get('main .react-grid-item:eq(1) [data-field="xml_path"]').eq(2).should('have.text',element.xml_path)
    })
    cy.get('main .react-grid-item:eq(1) [data-field="select"]').eq(2).within(() => {
        cy.contains('button', select).click();
      });
    cy.wait(300);
})

When('The user clicks {string} on the following Sponsor Dataset Class', (select, dataTable) => {
    dataTable.hashes().forEach((element) => {
        cy.get('main .react-grid-item:eq(3) [data-field="uid"]').eq(6).should('have.text',element.uid)
        cy.get('main .react-grid-item:eq(3) [data-field="basic_std"]').eq(6).should('have.text',element.basic_std)
    })
    cy.get('main .react-grid-item:eq(3) [data-field="select"]').eq(6).within(() => {
        cy.contains('button', select).click();
      });
    cy.wait(300);
})

Then('The Datasets - table should display the following', (dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(1) [data-field="uid"]').eq(i).should('have.text',element.uid)
        cy.get('main .react-grid-item:eq(1) [data-field="label"]').eq(i).should('have.text',element.label)
        cy.get('main .react-grid-item:eq(1) [data-field="basic_std"]').eq(i).should('have.text',element.basic_std)
        cy.get('main .react-grid-item:eq(1) [data-field="purpose"]').eq(i).should('have.text',element.purpose)
        cy.get('main .react-grid-item:eq(1) [data-field="ig_comment"]').eq(i).should('have.text',element.ig_comment)
        cy.get('main .react-grid-item:eq(1) [data-field="xml_path"]').eq(i).should('have.text',element.xml_path)
    })
})

Then('The Dataset Classes table should display the following', (dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(3) [data-field="uid"]').eq(i).should('have.text',element.uid)
        cy.get('main .react-grid-item:eq(3) [data-field="basic_std"]').eq(i).should('have.text',element.basic_std)
    })
})

Then('The Sponsor Variables table should display the following', (dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(2) [data-field="uid"]').eq(i).should('have.text',element.uid)
        cy.get('main .react-grid-item:eq(2) [data-field="basic_std"]').eq(i).should('have.text',element.basic_std)
        cy.get('main .react-grid-item:eq(2) [data-field="key"]').eq(i).should('have.text',element.key)
        cy.get('main .react-grid-item:eq(2) [data-field="label"]').eq(i).should('have.text',element.label)
        cy.get('main .react-grid-item:eq(2) [data-field="type"]').eq(i).should('have.text',element.type)
        cy.get('main .react-grid-item:eq(2) [data-field="length"]').eq(i).should('have.text',element.length)
        cy.get('main .react-grid-item:eq(2) [data-field="displayformat"]').eq(i).should('have.text',element.displayformat)
        cy.get('main .react-grid-item:eq(2) [data-field="xmldatatype"]').eq(i).should('have.text',element.xmldatatype)
        cy.get('main .react-grid-item:eq(2) [data-field="xmlcodelist"]').eq(i).should('have.text',element.xmlcodelist)
        cy.get('main .react-grid-item:eq(2) [data-field="core"]').eq(i).should('have.text',element.core)
        cy.get('main .react-grid-item:eq(2) [data-field="origin"]').eq(i).should('have.text',element.origin)
        cy.get('main .react-grid-item:eq(2) [data-field="role"]').eq(i).should('have.text',element.role)
        cy.get('main .react-grid-item:eq(2) [data-field="term"]').eq(i).should('have.text',element.term)
        cy.get('main .react-grid-item:eq(2) [data-field="ig_comment"]').eq(i).should('have.text',element.ig_comment)
        cy.get('main .react-grid-item:eq(2) [data-field="enrich_rule"]').eq(i).should('have.text',element.enrich_rule)
        cy.get('main .react-grid-item:eq(2) [data-field="order"]').eq(i).should('have.text',element.order)
    })
})

Then('The Sponsor Variable Classes table should display the following in the first line', (dataTable) => {
    dataTable.hashes().forEach((element,k) => {
        const i=k+1
        cy.get('main .react-grid-item:eq(4) [data-field="uid"]').eq(i).should('have.text',element.uid)
        cy.get('main .react-grid-item:eq(4) [data-field="basic_std"]').eq(i).should('have.text',element.basic_std)
        cy.get('main .react-grid-item:eq(4) [data-field="label"]').eq(i).should('have.text',element.label)
        cy.get('main .react-grid-item:eq(4) [data-field="type"]').eq(i).should('have.text',element.type)
        cy.get('main .react-grid-item:eq(4) [data-field="length"]').eq(i).should('have.text',element.length)
        cy.get('main .react-grid-item:eq(4) [data-field="displayformat"]').eq(i).should('have.text',element.displayformat)
        cy.get('main .react-grid-item:eq(4) [data-field="xmldatatype"]').eq(i).should('have.text',element.xmldatatype)
        cy.get('main .react-grid-item:eq(4) [data-field="xmlcodelist"]').eq(i).should('have.text',element.xmlcodelist)
        cy.get('main .react-grid-item:eq(4) [data-field="core"]').eq(i).should('have.text',element.core)
        cy.get('main .react-grid-item:eq(4) [data-field="origin"]').eq(i).should('have.text',element.origin)
        cy.get('main .react-grid-item:eq(4) [data-field="role"]').eq(i).should('have.text',element.role)
        cy.get('main .react-grid-item:eq(4) [data-field="term"]').eq(i).should('have.text',element.term)
        cy.get('main .react-grid-item:eq(4) [data-field="ig_comment"]').eq(i).should('have.text',element.ig_comment)
        cy.get('main .react-grid-item:eq(4) [data-field="incl_cre_domain"]').eq(i).should('have.text',element.incl_cre_domain)
        cy.get('main .react-grid-item:eq(4) [data-field="order"]').eq(i).should('have.text',element.order)
    })
})