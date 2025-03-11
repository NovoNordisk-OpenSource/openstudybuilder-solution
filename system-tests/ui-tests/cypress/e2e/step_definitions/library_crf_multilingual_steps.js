const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let formName, itemName, itemGroupName

When('The multilingual CRFs option is toggled on in the settings menu', () => setMultilingualOptionInSettings(true))

When('The multilingual CRFs option is toggled off in the settings menu', () => setMultilingualOptionInSettings(false))

Given('The single language CRFs are enabled', () => setMultilingualOption(false))

Given('The multilingual CRFs are enabled', () => setMultilingualOption(true))

Then('The system is showing Translations section for the CRF Forms', () => {
    checkIfSystemDisplayesTranslations('forms', 'form')
})

Then('The system is showing Translations section for the CRF Item Groups', () => {
    checkIfSystemDisplayesTranslations('item-groups', 'item-group')
})

Then('The system is showing Translations section for the CRF Items', () => {
    checkIfSystemDisplayesTranslations('items', 'item')
})

Then('The system is not showing Translations section for the CRF Forms', () => {
    checkIfSystemDisplayesTranslations('forms', 'form', false)
})

Then('The system is not showing Translations section for the CRF Item Groups', () => {
    checkIfSystemDisplayesTranslations('item-groups', 'item-group', false)
})

Then('The system is not showing Translations section for the CRF Items', () => {
    checkIfSystemDisplayesTranslations('items', 'item', false)
})

When('The new CRF Form is created with description providied', () => {
    formName = `CRFFNAME ${Date.now()}`
    cy.clickButton('add-crf-form')
    cy.fillInput('form-oid', 'CRFNOID')
    cy.fillInput('form-oid-name', formName)
    proceedAndSave()
})

When('The new CRF Item Group is created with description providied', () => {
    itemGroupName = `CRFITGNAME ${Date.now()}`
    cy.clickButton('add-crf-item-group')
    cy.fillInput('item-group-name', itemGroupName)
    proceedAndSave()
})

When('The new CRF Item is created with description providied', () => {
    itemName = `CRFINAME ${Date.now()}`
    cy.clickButton('add-crf-item')
    cy.fillInput('item-name', itemName)
    cy.selectVSelect('item-data-type', 'INTEGER')
    cy.clickFormActionButton('continue')
    proceedAndSave()
})

Then('The CRF Form description is saved within the system', () => checkIfExists(formName))

Then('The CRF Item Group description is saved within the system', () => checkIfExists(itemGroupName))

Then('The CRF Item description is saved within the system', () => checkIfExists(itemName))

function proceedAndSave() {
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('save')
    cy.waitForTable()
}

function checkIfSystemDisplayesTranslations(section, button, shouldBeDisplayed = true) {
    let condition = shouldBeDisplayed ? 'contain' : 'not.contain'
    cy.visit(`library/crfs/${section}`)
    cy.clickButton(`add-crf-${button}`)
    cy.get('.v-stepper-item__title').should(condition, 'Translations')
}

function setMultilingualOption(turnOn) {
    localStorage.setItem('userData', `{"darkTheme":false,"rows":10,"studyNumberLength":4,"multilingual":${turnOn}}`)
    cy.reload()
}

function setMultilingualOptionInSettings(turnOn) {
    cy.clickButton('topbar-admin-icon')
    cy.get('[data-cy="settings-multilingual-crf"] input').then(radioButton => {
        turnOn ? cy.wrap(radioButton).check( {force: true} ) : cy.wrap(radioButton).uncheck( {force: true} ) 
    })
    cy.clickButton('save-settings-button')
}

function checkIfExists(name) {
    cy.fillInput('search-field', name)
    cy.tableContains(name)
}