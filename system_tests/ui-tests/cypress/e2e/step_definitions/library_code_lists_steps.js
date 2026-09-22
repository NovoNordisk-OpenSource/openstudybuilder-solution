const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

let codelistName, termId, termSponsorName, termSentanceName, termName, termSubmissionValue, termNciValue, termDefinition, conceptId

When('The id of the first term on the list is saved', () => cy.getCellValue(0, 'Concept ID').then(id => termId = id))

When('The term is search for and found', () => cy.searchAndCheckPresence(conceptId, true))

When('The codelist is search for and found', () => cy.searchAndCheckPresence(codelistName, true))

When('The codelist and attributes status is set to {string}', (status) => {
    cy.checkRowByIndex(0, 'Code list status', status)
    cy.checkRowByIndex(0, 'Attributes status', status)
})

When('The codelist sponsor values are approved', () => cy.clickButton('approve-sponsor-values'))

When('The codelist attribute values are approved', () => cy.clickButton('approve-attributes-values'))

When('The codelist sponsor values edition is triggered', () => cy.clickButton('edit-sponsor-values'))

When('The codelist attribute values edition is triggered', () => cy.get('[aria-label="For the code list attributes values"] [title="Edit sponsor values"]').click())

When('The codelist sponsor values new version is created', () => cy.clickButton('create-new-sponsor-values'))

When('The codelist attribute values new version is created', () => cy.get('[title="Create new attributes version"]').click())

When('The sponsor preffered name is updated', () => cy.fillInput('sponsor-preffered-name', `Update ${termSponsorName}`))

When('The code list attributes are updated and change description is provided', () => {
    cy.contains('.v-overlay .v-input__control', 'Code list name').find('input').clear().type(`Update ${codelistName}`)
    cy.contains('.v-overlay .v-input__control', 'Submission value').find('input').clear().type(`Update ${termSubmissionValue}`)
    cy.contains('.v-overlay .v-input__control', 'NCI preferred name').find('input').clear().type(`Update ${termNciValue}`)
    cy.contains('.v-overlay .v-input__control', 'Definition').find('[aria-describedby^="input"]').clear().type(`Update ${termDefinition}`)
    cy.contains('.v-overlay .v-input__control', 'Change description').find('[aria-describedby^="input"]').clear().type('e2e test')
})

When('Codelist change description is provided', () => cy.fillInput('change-description', `e2e test`))

When('Code list attrubutes changes are saved', () => cy.contains('.v-card-actions button', 'Save').click())

When('The user is redirected to the term page', () => {
    cy.url().should('contain', `${termId}/terms`)
    cy.get('.page-title').should('contain.text', termId)
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

Then('The timeline is visible', () => cy.get('[data-cy="timeline"]', {timeout: 10000}).should('be.visible'))

Then('Add term button is visible in actions menu', () => cy.get('[data-cy="add-term-button"]').should('be.visible'))

Then('The Edit sponsor values button is not visible', () => cy.get('[data-cy="edit-sponsor-values"]').should('not.exist'))

Then('The Create new sponsor values version button is visible', () => cy.get('[data-cy="create-new-sponsor-values"]').should('be.visible'))

When('The codelist summary is expanded', () => cy.clickButton('cl-summary-title'))

Then('The codelist summary show following data', (dataTable) => {
    dataTable.hashes().forEach(element => cy.get(`[data-cy="${element.name}"]`).should('contain', element.value))
})

Then('The sponsor preferred name is updated', () => {
    cy.contains('[aria-label="For the code list sponsor values"] tr td', 'Sponsor preferred name').next().should('contain.text', termSponsorName)
})

Then('The codelist attributes updated values are visible', () => {
    cy.contains('[aria-label="For the code list attributes values"] tr td', 'Code list name').next().should('contain.text', codelistName)
    cy.contains('[aria-label="For the code list attributes values"] tr td', 'Submission value').next().should('contain.text', termSubmissionValue)
    cy.contains('[aria-label="For the code list attributes values"] tr td', 'NCI preferred name').next().should('contain.text', termNciValue)
    cy.contains('[aria-label="For the code list attributes values"] tr td', 'Definition').next().should('contain.text', termDefinition)
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

Then('The term data is visible in the table', () => {
    cy.checkRowByIndex(0, 'Library', 'Sponsor')
    cy.checkRowByIndex(0, 'Concept ID', conceptId)
    cy.checkRowByIndex(0, 'Sponsor name', termSponsorName)
    cy.checkRowByIndex(0, 'Submission value', termName)
    cy.checkRowByIndex(0, 'NCI Preferred name', termNciValue)
    cy.checkRowByIndex(0, 'Definition', termDefinition)
})

When('The new term is added', () => {
    termSponsorName = `SponsorTerm ${getShortUniqueId()}`
    termSentanceName = termSponsorName.toLowerCase()
    termName = `TermName${getShortUniqueId()}`
    termNciValue = `NCITerm${getShortUniqueId()}`
    termDefinition = `Def${getShortUniqueId()}`
    conceptId = `Concept${getShortUniqueId()}`
    cy.clickButton('add-term-button')
    cy.get('[data-cy="create-new-term"] input').check( {force: true} )
    cy.clickButton('step.creation_mode-continue-button')
    cy.fillInput('term-sponsor-preferred-name', termSponsorName)
    cy.fillInput('term-sentence-case-name', termSentanceName)
    cy.clickButton('step.names-continue-button')
    cy.fillInput('term-concept-id', conceptId)
    cy.fillInput('term-nci-preffered-name',  termNciValue)
    cy.fillInput('term-definition', termDefinition)
    cy.clickButton('step.attributes-continue-button')
    cy.fillInput('term-name', termName)
    cy.fillInput('term-order', '1')
    cy.clickButton('step.order_and_submval_new-continue-button')
})

When('The term sponsor values are edited', () => {
    termSponsorName = `Edit ${termSponsorName}`
    cy.clickButton('edit-sponsor-values')
    cy.wait(1000)
    cy.fillInput('term-sponsor-preffered-name', termSponsorName)
    cy.fillInput('change-description', `Description edited of the change`)
})

When('The new Codelist is added', () => {
    termSponsorName = `SponsorTerm ${getShortUniqueId()}`
    codelistName = `Name ${getShortUniqueId()}`
    termSubmissionValue = `E2ETerm ${getShortUniqueId()}`
    termNciValue = `NCITerm${getShortUniqueId()}`
    termDefinition = `Definition ${getShortUniqueId()}`
    cy.clickButton('add-sponsor-codelist')
    cy.clickButton('step.codelist_type_selection-continue-button')
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
    cy.wait('@getData2', {timeout: 90000})
    cy.searchForInPopUp(termSponsorName)
    cy.longWaitForTable(60000)
    cy.get('table tbody tr [type="checkbox"]').eq(0).check()
    cy.clickButton('step.select-continue-button')
    cy.fillInput('term-order', '1')
    cy.clickButton('step.order_and_submval-continue-button')
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
    verifyTermSponsorName()
    cy.contains('NCI preferred name').next().should('contain', termNciValue)
    checkCodelistTable('Submission value', termName)
    cy.get('table tbody tr').contains('Definition').next().should('contain', termDefinition)
    cy.contains('Sentence case name').next().should('contain', termSentanceName)
    checkCodelistTable('Order', '1')
}

function verifyCodelist() {
    verifyTermSponsorName()
    cy.contains('NCI preferred name').next().should('contain', termNciValue)
    cy.contains('Submission value').next().should('contain', termSubmissionValue)
    cy.get('table tbody tr').contains('Definition').next().should('contain', termDefinition)
    cy.contains('Template parameter').next().should('contain', 'No')
    cy.contains('Code list name').next().should('contain', codelistName)
    cy.contains('Extensible').next().should('contain', 'Yes')
}

function checkStatusAndVersion(type, status, version) {
    cy.get(`[data-cy="${type}-status"]`).should('contain', status)
    cy.get(`[data-cy="${type}-version"]`).should('contain', version)
}

function checkCodelistTable(columnName, value) {
    cy.get('[aria-label="Term sponsor values"] table').eq(3).within(() => {
        cy.contains('thead th', columnName).invoke('index').then(index => {
            cy.get('tbody td').eq(index).should('contain', value)
        })
    }) 
}