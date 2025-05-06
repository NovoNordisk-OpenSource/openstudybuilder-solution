const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let codelistName, termSponsorName, termSentanceName, termName, termSubmissionValue, termNciValue, termDefinition
let iterator = 1

//To be removed once ct-catalogues tests stop crashing
Then('Log that step was executed', () => {
    console.log(`Step ${iterator} was executed`)
    iterator += iterator
})

Given('CT data is loaded', () => {
  cy.intercept('/api/ct/codelists?*').as('getData')
  cy.wait('@getData', {timeout: 30000})
})

Then('CT Package data is loaded', () => {
    cy.intercept('/api/ct/packages').as('getPackages')
    cy.intercept('/api/ct/codelists?page_number=1&*').as('getCodeList')
    cy.wait('@getPackages', {timeout: 20000})
    cy.wait('@getCodeList', {timeout: 20000})
})

Then('The URL should contain {string} date selected and {string} ID', (date, id) => {
    cy.url().should('contain', `${date}/${id}/terms`)
})

Then('The URL should contain {string} ID', (id) => cy.url().should('contain', `${id}/terms`))

Then('The timeline is visible', () => cy.get('[data-cy="timeline"]', {timeout: 10000}).should('be.visible'))

Then('Add term button is visible in actions menu', () => cy.get('[data-cy="add-term-button"]').should('be.visible'))

Then('The Edit sponsor values button is not visible', () => cy.get('[data-cy="edit-sponsor-values"]').should('not.exist'))

Then('The Create new sponsor values version button is visible', () => cy.get('[data-cy="create-new-sponsor-values"]').should('be.visible'))

When('The codelist summary is expanded', () => cy.clickButton('cl-summary-title'))

Then('The codelist summary show following data', (dataTable) => {
    dataTable.hashes().forEach(element => cy.elementContain(element.name, element.value))
})

Then('The sponsor values should be in status {string} and version {string}', (status, version) => {
    checkStatusAndVersion('names', status, version)
})

Then('The attribute values should be in status {string} and version {string}', (status, version) => {
    checkStatusAndVersion('attributes', status, version)
})

Given('The test Codelist for editing is opened', () => {
    cy.createAndOpenCodelist()
    cy.contains('table tbody tr td', 'Sponsor preferred name').next().invoke('text').then(text => termSponsorName = text)
})

Given('The test term in test Codelist is opened', () => {
    cy.createAndOpenTerm()
    cy.contains('table tbody tr td', 'Sponsor preferred name').next().invoke('text').then(text => termSponsorName = text)
    cy.contains('table tbody tr td', 'Sentence case name').next().invoke('text').then(text => termSentanceName = text)
})

When('The Codelist sponsor values are validated', () => cy.clickButton('approve-sponsor-values'))

When('The term is validated', () => {
    cy.clickButton('approve-term-sponsor-values')
    cy.clickButton('approve-term-attributes-values')
})

When('The new term is added', () => {
    termSponsorName = `SponsorTerm ${Date.now()}`
    termSentanceName = `TermSentenceCase ${Date.now()}`
    termName = `TermName ${Date.now()}`
    termSubmissionValue = `E2ETerm ${Date.now()}`
    termNciValue = `NCITerm${Date.now()}`
    termDefinition = `Definition ${Date.now()}`
    cy.clickButton('add-term-button')
    cy.get('[data-cy="create-new-term"] input').check( {force: true} )
    cy.clickButton('step.creation_mode-continue-button')
    cy.fillInput('term-sponsor-preferred-name', termSponsorName)
    cy.fillInput('term-sentence-case-name', termSentanceName)
    cy.fillInput('term-order', '1')
    cy.clickButton('step.names-continue-button')
    cy.fillInput('term-name', termName)
    cy.fillInput('term-submission-value', termSubmissionValue)
    cy.fillInput('term-nci-preffered-name',  termNciValue)
    cy.fillInput('term-definition', termDefinition)
    cy.clickButton('step.attributes-continue-button')
})

When('The term sponsor values are edited', () => {
    termSponsorName = `Edit ${termSponsorName}`
    cy.clickButton('edit-sponsor-values')
    cy.wait(1000)
    cy.fillInput('term-sponsor-preffered-name', termSponsorName)
    cy.fillInput('change-description', `Description edited of the change`)
    cy.clickButton('save-button')
    cy.get('[data-cy="form-body"] .dialog-title').should('not.exist')
})

When('The new Codelist is added', () => {
    termSponsorName = `SponsorTerm ${Date.now()}`
    codelistName = `Name ${Date.now()}`
    termSubmissionValue = `E2ETerm ${Date.now()}`
    termNciValue = `NCITerm${Date.now()}`
    termDefinition = `Definition ${Date.now()}`
    cy.clickButton('add-sponsor-codelist')
    cy.selectAutoComplete('catalogue-dropdown', 'ADAM CT')
    cy.clickButton('step.catalogue-continue-button')
    cy.fillInput('sponsor-preffered-name', termSponsorName)
    cy.clickButton('step.names-continue-button')
    cy.fillInput('codelist-name', codelistName)
    cy.fillInput('submission-value', termSubmissionValue)
    cy.fillInput('nci-preffered-name', termNciValue)
    cy.get('[data-cy="extensible-toggle"] input').check()
    cy.fillInput('definition', termDefinition)
    cy.clickButton('step.attributes-continue-button')
})

When('The Codelist sponsor values are edited', () => {
    termSponsorName = `Edit ${termSponsorName}`
    cy.clickButton('edit-sponsor-values')
    cy.wait(1000)
    cy.fillInput('sponsor-preffered-name', termSponsorName)
    cy.fillInput('change-description', `Description edited of the change`)
    cy.clickButton('save-button')
    cy.waitForFormSave()
})

Then('The term page is opened and showing correct data', () => verifyTerm())

Then('The edited term page is showing correct data', () => verifyTermSponsorName(true))

Then('The edited codelist page is showing correct data', () => verifyTermSponsorName())

Then('The new Codelist page is opened and showing correct data', () => verifyCodelist())

When('The existing term is added', () => {
    cy.clickButton('add-term-button')
    cy.get('[data-cy="select-exitsing-term"] input').check({force: true})
    cy.intercept('/api/ct/terms?*').as('getData2')
    cy.clickButton('step.creation_mode-continue-button')
    cy.wait('@getData2', {timeout: 30000})
    cy.searchForInPopUp(termSponsorName)
    cy.longWaitForTable(60000)
    cy.get('table tbody tr [type="checkbox"]').eq(0).check()
    cy.clickButton('step.select-continue-button')
})

Then('The version history contain the changes of edited Codelist', () => {
    cy.clickButton('sponsor-values-version-history')
    cy.get('.v-card table tbody tr').eq(1).find('td', termSponsorName).next().next()
                                    .should('contain', 'Draft').next().should('contain', '0.2')
})

function verifyTermSponsorName(checkSentanceName = false) {
    cy.wait(1000)
    cy.contains('Sponsor preferred name').next().should('contain', termSponsorName)
    if (checkSentanceName) cy.contains('Sentence case name').next().should('contain', termSponsorName.toLowerCase())
}

function verifyTerm() {
    verifyData(true)
    cy.contains('Sentence case name').next().should('contain', termSentanceName)
    cy.contains('Order').next().should('contain', 1)
    cy.contains('Name submission value').next().should('contain', termName)
}

function verifyCodelist() {
    verifyData()
    cy.contains('Template parameter').next().should('contain', 'No')
    cy.contains('Code list name').next().should('contain', codelistName)
    cy.contains('Extensible').next().should('contain', 'Yes')
}

function verifyData(isTerm = false) {
    verifyTermSponsorName()
    let submissionValueHeader = isTerm ? 'Code submission value' : 'Submission value'
    cy.contains('NCI preferred name').next().should('contain', termNciValue)
    cy.contains(submissionValueHeader).next().should('contain', termSubmissionValue)
    cy.get('table tbody tr').contains('Definition').next().should('contain', termDefinition)
}

function checkStatusAndVersion(type, status, version) {
    cy.elementContain(`${type}-status`, status)
    cy.elementContain(`${type}-version`, version)
}
