const clickLastElement = () => cy.get('.v-list-item').last().click()
const clickFirstElement = () => cy.get('.v-list-item').first().click()
const clickElementByValue = (value) => cy.contains('.v-list-item', value).click()

Cypress.Commands.add('selectAutoComplete', (dropdownName, value) => {
    selectFromDropdown(dropdownName, '.v-field__input', () => clickElementByValue(value), false)
})

Cypress.Commands.add('selectVSelect', (dropdownName, value) => {
    selectFromDropdown(dropdownName, '.v-field__input', () => clickElementByValue(value))
})

Cypress.Commands.add('selectFirstVSelect', (dropdownName) => {
    selectFromDropdown(dropdownName, '.v-field__input', clickFirstElement)
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

function selectFromDropdown(dropdownName, dropdownLocator, action, defocus = true) {
    activateDropdown(dropdownName, dropdownLocator)
    performSelection(action)
    if (defocus) defocusOnForm()
}

function activateDropdown(dropdownName, innerLocator) {
    cy.get(`[data-cy="${dropdownName}"]`).within(() => cy.get(innerLocator).click())
    cy.wait(500)
}

function performSelection(action) {
    cy.get('.v-list')
        .filter(':visible')
        .should('not.contain', 'No data available')
        .within(() => action())
    cy.wait(500)
}

function defocusOnForm() {
    cy.get('[data-cy="form-body"]').click({force: true})
    cy.wait(500)
}