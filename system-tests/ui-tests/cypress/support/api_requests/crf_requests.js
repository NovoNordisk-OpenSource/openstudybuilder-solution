Cypress.Commands.add('createCrfTemplate', () => {
    cy.request({
        method: 'POST',
        url: Cypress.env('API') + '/concepts/odms/study-events',
        body: '{"name":"AutomatedTest"}'
    })
    cy.reload()
})

Cypress.Commands.add('createCrfForm', (oid) => {
    cy.request({
        method: 'POST',
        url: Cypress.env('API') + '/concepts/odms/forms',
        body: '{"oid":"' + oid + '","repeating":"no","alias_uids":[],"name":"TestAutomated","descriptions":[{"library_name":"Sponsor","language":"ENG","name":"TestAutomated"}],"library_name":"Sponsor"}'
    })
    cy.reload()
})

Cypress.Commands.add('createCrfItemGroup', (oid) => {
    cy.request({
        method: 'POST',
        url: Cypress.env('API') + '/concepts/odms/item-groups',
        body: '{"oid":"' + oid + '","repeating":"no","is_reference_data":"no","locked":"no","alias_uids":[],"sdtm_domain_uids":[],"name":"AutomatedTestItemGroup","descriptions":[{"library_name":"Sponsor","language":"ENG","name":"AutomatedTestItemGroup"}],"library_name":"Sponsor"}'
    })
    cy.reload()
})

Cypress.Commands.add('createCrfItem', (oid) => {
    cy.request({
        method: 'POST',
        url: Cypress.env('API') + '/concepts/odms/items',
        body: '{"oid":"' + oid + '","alias_uids":[],"locked":"no","name":"AutomatedTestsItem","datatype":"INTEGER","descriptions":[{"library_name":"Sponsor","language":"ENG","name":"AutomatedTestsItem"}],"library_name":"Sponsor","codelist_uid":null,"unitDefinitions":[],"terms":[]}'
    })
    cy.reload()
})