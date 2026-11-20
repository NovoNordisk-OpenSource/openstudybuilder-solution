const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getCurrStudyUid } = require("../../support/helper_functions");


let footnoteEditText = Date.now()
let footnoteText

Given('[API] The footnote exists for current study', () => {
    cy.addFootnoteToStudy(getCurrStudyUid(), 'TEST FOOTNOTE')
})

Given('[API] The footnote exists for study {string}', (studyId) =>
    cy.getStudyUid(studyId).then((uid) => cy.addFootnoteToStudy(uid, 'TEST FOOTNOTE')))


Then('The manage footnotes dialog contains {string}', (text) => {
    cy.get('.v-card').should('contain.text', 'Manage footnotes').and('contain.text', text);
})

When('The user selects cells for footnote creation', () => {
    selectCellByIndex(1)
    selectCellByIndex(2)

})

Then('The selected cells are highlighted for footnote creation', () => {
    cy.get('.clickable-object-cell').eq(1).should('have.class', 'highlighted-footnote-cell')
    cy.get('.clickable-object-cell').eq(2).should('have.class', 'highlighted-footnote-cell')
})

When('The user selects option to create a footnote from {string}', (value) => cy.clickButton(`create-footnote-option-${value}`))

When('The user creates a footnote from scratch', () => {
    selectCellByIndex(1)
    selectCellByIndex(2)
    cy.fillTextArea('footnote-text', 'Sample [Activity] footnote text')
    cy.selectAutoComplete('autocomplete-input-field', '1,25-Dihydroxyvitamin D3')
    cy.clickButton('submit-footnote')
})

Then('The footnote is successfully created from scratch', () => {
    cy.get('.footnote-name').should('contain.text', 'Sample 1,25-dihydroxyvitamin d3 footnote text')
    cy.clickButton('close-footnotes-button')
    cy.get('.clickable-object-cell').eq(2).click()
    cy.get("[data-cy='footnote-chip']").should('contain.text', 'Sample 1,25-dihydroxyvitamin d3 footnote text')
})

When('The user creates a footnote from standards', () => {
    selectCellByIndex(3)
    selectCellByIndex(4)
    cy.get('[data-cy="footnote-standards-pre-instance-switch"] input[type="checkbox"]')
        .uncheck({ force: true })
    cy.get('.standards-list .template-readonly').eq(0).then(el => {
        cy.wrap(el).invoke('text').then((text) => footnoteText = text.substring(0, 3))
        cy.wrap(el).click()
    })
    cy.clickButton('submit-footnote-standards')
})

Then('The footnote is successfully created from standards', () => {
    cy.clickButton('close-footnotes-button')
    cy.get('.clickable-object-cell').eq(4).click()
    cy.get("[data-cy='footnote-chip']").should('contain.text', `a${footnoteText}`)
})

When('The user creates a footnote from studies', () => {
    selectCellByIndex(5)
    selectCellByIndex(6)
    cy.selectAutoComplete('footnote-studies-source-study', 'CDISC DEV-9885 (Footnotes testing study B)')
    cy.get('.studies-list .template-readonly').eq(0).then(el => {
        cy.wrap(el).invoke('text').then((text) => footnoteText = text.substring(0, 3))
        cy.wrap(el).click()
    })
    cy.clickButton('submit-footnote-studies')
})

Then('The footnote is successfully created from studies', () => {
    cy.clickButton('close-footnotes-button')
    cy.clickButton('close-footnotes-button')
    cy.get('.clickable-object-cell').eq(6).click()
    cy.get("[data-cy='footnote-chip']").should('contain.text', `a${footnoteText}`)

})

When('The user opens link dialog for the {string}', (object_type) => {
    cy.get(`[object-type-0="${object_type}"]`).eq(0).click({ force: true })
})

When('The user opens link dialog for the study epoch', () => {
    cy.get(`[object-type="StudyEpoch"]`).eq(0).click({ force: true })
})

When('The user opens link dialog for the study visit', () => {
    cy.get(`[object-type="StudyVisit"]`).eq(0).click({ force: true })
})

When('The user selects footnote', () => {
    cy.selectAutoComplete('footnote-autocomplete', 'TEST FOOTNOTE')
})


Then('The footnote is successfully linked', () => {
    cy.get("[data-cy='footnote-chip']").should('contain.text', 'TEST FOOTNOTE')
})

When('The user intercepts SoA Footnotes {string} request', (requestType) => {
    if (requestType === 'edit') {
        cy.intercept({ method: 'PATCH', url: '**/study-soa-footnotes/**' }).as('footnoteEdit')
    }
    else if (requestType === 'delete') {
        cy.intercept({ method: 'DELETE', url: '**/study-soa-footnotes/**' }).as('footnotesDelete')
    }
    else {
        throw new Error(`Unsupported request type: ${requestType}`)
    }
})

When('The footnote is edited', () => {
    cy.get('.footnote-edit-panel').click()
    cy.fillTextArea('footnote-text', footnoteEditText)
    cy.clickButton('submit-footnote')
    cy.wait('@footnoteEdit').its('response.statusCode').should('eq', 200)
})

Then('The footnote is successfully updated and the link remains', () => {
    cy.clickButton('close-footnotes-button')
    cy.get(`[object-type="StudyVisit"]`).eq(0).click({ force: true })
    cy.get("[data-cy='footnote-chip']").should('contain.text', footnoteEditText)
})

When('The footnote is deleted', () => {
    cy.get('.footnote-delete-panel').click()
    cy.clickButton('continue-popup')
    cy.wait('@footnotesDelete').its('response.statusCode').should('eq', 204)
    cy.clickButton('close-footnotes-button')

})

Then('The footnote is successfully deleted', () => {
    cy.get(`[object-type="StudyVisit"]`).eq(0).click({ force: true })
    cy.get("[data-cy='footnote-chip']").should('not.exist')
})

function selectCellByIndex(index) {
    cy.get('.clickable-object-cell').eq(index).click({ force: true })
}