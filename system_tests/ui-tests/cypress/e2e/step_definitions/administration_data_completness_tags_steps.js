const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getCurrentStudyId } = require("../../support/helper_functions");

let currentTag
let tag1
let tag2
let tag3

When("The user provides new completness tag into the text field", () => {
    currentTag = Date.now()
    cy.fillInput('tag-name', currentTag)
});

When("The user clicks save button", () => {
    cy.clickButton('save-tag')
});

Then("The data completness tag is created", () => {
    cy.tableContains(currentTag)
});

When("The data completness tag in uncompleted state exists", () => {
    currentTag = Date.now()
    cy.sendPostRequest('/data-completeness-tags', {"name": currentTag.toString()})

});

When("The user sets the tag to completed for study", () => {
    selectTagStudy(getCurrentStudyId())
    cy.contains('.v-data-table__tr', currentTag).find('input').check()
});

When("The user sets the tag to uncompleted for the study", () => {
    selectTagStudy(getCurrentStudyId())
    cy.contains('.v-data-table__tr', currentTag).find('input').uncheck()
});

When("The data completness tag is visible on study list level for selected study", () => {
    cy.searchFor(getCurrentStudyId())
    cy.contains(currentTag).should('exist')
});

When("The data completness tag in completed state exists for the study", () => {
    currentTag = Date.now()
    selectTagStudy(getCurrentStudyId())
    createTag(currentTag)
    cy.contains('.v-data-table__tr', currentTag).find('input').check()
});

When("The data completness tag is not on study list level for selected study", () => {
    cy.searchFor(getCurrentStudyId())
    cy.contains(currentTag).should('not.exist')
});


When("The user creates multiple completion tags", () => {
    tag1 = `Tag1 ${Date.now()}`
    tag2 = `Tag2 ${Date.now()}`
    tag3 = `Tag3 ${Date.now()}`
    createTag(tag1)
    createTag(tag2)
    createTag(tag3)

});

When("Only the completed tag is visible on the study list level for the study", () => {
    cy.searchFor(getCurrentStudyId())
});

When("The user sets multiple tags to completed for selected study", () => {
    selectTagStudy(getCurrentStudyId())
    cy.contains('.v-data-table__tr', tag1).find('input').check()
    cy.contains('.v-data-table__tr', tag2).find('input').check()
    cy.contains('.v-data-table__tr', tag3).find('input').check()
});


Then('All the completed tags are visible for the study', () => {
    cy.searchFor(getCurrentStudyId())
    cy.tableContains(tag1)
    cy.tableContains(tag2)
    cy.tableContains(tag3)
})

function createTag(tag) {
    cy.fillInput('tag-name', tag)
    cy.clickButton('save-tag')
}

function selectTagStudy(study) {
    cy.get('[data-cy="select-study-to-tag"] input').clear().type(study)
    cy.selectAutoComplete("select-study-to-tag", study, { defocus: false })
}