const clickLastElement = () => cy.get('.v-list-item').last().click()
const clickFirstElement = () => cy.get('.v-list-item').first().click()
const clickSecondElement = () => cy.get('.v-list-item').eq(1).click()
const checkLastElement = () => cy.get('.v-list-item input').last().check()
const checkFirstElement = () => cy.get('.v-list-item input').first().check()
const clickElementByValue = (value) => cy.contains('.v-list-item', value).click()

Cypress.Commands.add('checkNoDataAvailable', () => {
    cy.get('.v-overlay__content .v-list-item-title').should('have.text', 'No data available')
})

Cypress.Commands.add('selectAutoComplete', (dropdownName, value, scope) => {
    selectFromDropdown(dropdownName, '.v-field__input', () => clickElementByValue(value), false, scope)
})

Cypress.Commands.add('selectVSelect', (dropdownName, value) => {
    selectFromDropdown(dropdownName, '.v-field__input', () => clickElementByValue(value))
})

Cypress.Commands.add('clearDropdown', (dropdownName) => {
    clearDropdown(dropdownName)
})

Cypress.Commands.add('selectFirstVSelect', (dropdownName) => {
    selectFromDropdown(dropdownName, '.v-field__input', clickFirstElement)
})

Cypress.Commands.add('selectSecondVSelect', (dropdownName) => {
    selectFromDropdown(dropdownName, '.v-field__input', clickSecondElement)
})

Cypress.Commands.add('selectLastVSelect', (dropdownName) => {
    selectFromDropdown(dropdownName, '.v-field__input', clickLastElement)
})

Cypress.Commands.add('selectMultipleSelect', (dropdownName, value) => {
    selectFromDropdown(dropdownName, '.v-field__field', () => clickElementByValue(value))
})

Cypress.Commands.add('selectFirstMultipleSelect', (dropdownName) => {
    selectFromDropdown(dropdownName, '.v-field__field', clickFirstElement)
})

Cypress.Commands.add('selectLastMultipleSelect', (dropdownName) => {
    selectFromDropdown(dropdownName, '.v-field__field', clickLastElement)
})

Cypress.Commands.add('checkFirstMultipleSelect', (dropdownName) => {
    selectFromDropdown(dropdownName, '.v-field__field', checkFirstElement)
})

Cypress.Commands.add('checkLastMultipleSelect', (dropdownName) => {
    selectFromDropdown(dropdownName, '.v-field__field', checkLastElement)
})

function selectFromDropdown(dropdownName, dropdownLocator, action, defocus = true, scope) {
    activateDropdown(dropdownName, dropdownLocator, scope)
    performSelection(action)
    if (defocus) defocusOnForm()
}

function clearDropdown(dropdownName) {
    const selector = `[data-cy="${dropdownName}"]`

    cy.get(`${selector} .v-field`)
        .should('have.length', 1)
        .then(($field) => {
            if ($field.hasClass('v-field--dirty')) {
                cy.get(`${selector} .v-field__clearable`)
                    .find('[role="button"]')
                    .click({ force: true })
            }
        })

    cy.get(`${selector} .v-field`).should('not.have.class', 'v-field--dirty')
    cy.get(`${selector} input`).should('have.value', '')
}

function activateDropdown(dropdownName, innerLocator, scope) {
    const selector = scope ? `${scope} [data-cy="${dropdownName}"]` : `[data-cy="${dropdownName}"]`
    cy.get(selector).within(() => cy.get(innerLocator).click())
    cy.wait(500)
}

function performSelection(action) {
    cy.get('.v-overlay__content .v-list', { timeout: 20000 })
        .filter(':visible')
        .should('not.contain', 'No data available')
        .within(() => action())
}

function defocusOnForm() {
    cy.get('[data-cy="form-body"]').click({ force: true })
    cy.wait(500)
}