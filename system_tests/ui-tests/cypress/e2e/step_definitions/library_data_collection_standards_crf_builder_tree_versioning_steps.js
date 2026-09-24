import { generateShortUniqueName } from "../../support/helper_functions";
const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

export let collectionName, formName, itemGroupName, itemName
let collectionUid, formUid, itemGroupUid, itemUid

Given('[API] A CRF Collection is created', () => {
    collectionName = generateShortUniqueName('C_');
    cy.createCrfCollection(collectionName).then(collectionResponse => collectionUid = collectionResponse.body.uid)
})

Given('[API] A CRF Form is created', () => {
    formName = generateShortUniqueName('F_');
    cy.createCrfForm(formName).then(formResponse => formUid = formResponse.body.uid)
})

Given('[API] CRF Item Group is created', () => {
    itemGroupName = generateShortUniqueName('IG_');
    cy.createCrfItemGroup(itemGroupName).then(itemGroupResponse => itemGroupUid = itemGroupResponse.body.uid)
})

Given('[API] CRF Item is created', () => {
    itemName = generateShortUniqueName('I_');
    cy.getUnitDefinitionUid('integer')
    cy.createCrfItem(itemName).then((itemResponse) => itemUid = itemResponse.body.uid)
})

Given('[API] CRF Form is linked to the collection', () => cy.linkFormToCollection(formUid, collectionUid))

Given('[API] CRF Item Group is linked to the form', () => cy.linkItemGroupToForm(formUid, itemGroupUid))

Given('[API] CRF Item is linked to the group', () => cy.linkItemToItemGroup(itemGroupUid, itemUid))

Given('[API] CRF Form is approved', () => cy.approveForm(formUid))

Given('[API] CRF Collection is approved', () => cy.approveCollection(collectionUid))

Then('All the child elements should be displayed in the notification page', () => {
    cy.get('.v-card.v-theme--NNCustomLightTheme').should('be.visible')
        .and('contain', formName) 
        .and('contain', itemGroupName)
        .and('contain', itemName)
})

Then('CRF Collection links to the form version {string}, status {string}', (version, status) => {
    verifyLinkedForm(collectionName, formName, version, status)
})

Then('All elements linked to the CRF Collection have version {string}, status {string}', (version, status) => {
    verifyLinkedChildElement (collectionName, formName, itemGroupName, itemName, version, status);
})

Then('No child elements should be displayed in the notification page', () => {
    cy.get('.v-card.v-theme--NNCustomLightTheme').should('be.visible').and('contain', 'No child items will be affected.')
})

When('The CRF Collection is found and click in the CRF Tree filters', () => {
    cy.contains('[aria-haspopup="listbox"]', 'Show all').click()
    cy.get('.v-sheet .v-list-item').should('have.length.at.least', 2)
    cy.get('input[placeholder="Search"]').type(collectionName, {delay: 0})
    cy.get('.infinite-scroll-container').should('not.be.visible')
    cy.get('input[placeholder="Search"]').type('{backspace}')
    cy.get('.v-sheet .v-list-item').should('contain.text', collectionName)
    cy.contains('.v-sheet .v-list-item', collectionName).click()
})

When('The CRF Tree is expanded for collection', () => cy.contains('.crf-tree-node .node-content', collectionName).find('.mdi-chevron-right').click())

When('The CRF Tree is expanded for form', () => cy.contains('.crf-tree-node .node-content', formName).find('.mdi-chevron-right').click())

When('The CRF Tree is expanded for item group', () => cy.contains('.crf-tree-node .node-content', itemGroupName).find('.mdi-chevron-right').click())

function verifyLinkedChildElement (collectionName, formName, itemGroupName, itemName, version, status) {
     cy.contains('.crf-tree-node .node-content', collectionName).should('contain.text', status)
        .parent().find('.node-children .node-content').should('contain.text', formName).should('contain.text', version).should('contain.text', status)
            .parent().find('.node-children .node-content').should('contain.text', itemGroupName).should('contain.text', version).should('contain.text', status)
                .parent().find('.node-children .node-content').should('contain.text', itemName).should('contain.text', version).should('contain.text', status)
}

function verifyLinkedForm(collectionName, formName, version, status) {
    cy.contains('.crf-tree-node .node-content', collectionName).should('contain.text', status)
        .parent().find('.node-children .node-content').should('contain.text', formName).should('contain.text', version).should('contain.text', status)
}