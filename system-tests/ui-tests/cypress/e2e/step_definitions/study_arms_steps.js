const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");


Given('The Study Arm exists within the study', () => {
    cy.createTestArm('Study_000001')
    cy.reload()
})

When('The new study arm form is filled and saved', () => {
    cy.fixture('studyArm').then((arm) => {
        cy.clickButton('add-study-arm')
        cy.selectAutoComplete('arm-type', arm.type)
        cy.fillInput('arm-name', arm.name)
        cy.fillInput('arm-short-name', arm.short_name)
        cy.fillInput('arm-randomisation-group', arm.randomisation_group)
        cy.fillInput('arm-planned-number-of-subjects', arm.no_of_subjects)
        cy.fillInput('arm-description', arm.description)
    })
    cy.clickButton('save-button')
    cy.waitForFormSave()
    cy.checkSnackbarMessage('Study Arm created')
})

Then('The new study arm is visible within the study arms table', () => {
    cy.fixture('studyArm').then((arm) => {
        cy.tableContains(arm.type)
        cy.tableContains(arm.name)
        cy.tableContains(arm.randomisation_group)
        cy.tableContains(arm.randomisation_group)
        cy.tableContains(arm.no_of_subjects)
        cy.tableContains(arm.description)
    })
})

When('The arm data is edited and saved', () => {
    cy.fixture('studyArm').then((arm) => {
        cy.rowActionsByValue(arm.name, 'Edit')
        cy.fillInput('arm-name', arm.edit_name)
        cy.fillInput('arm-short-name', arm.edit_short_name)
        cy.fillInput('arm-description', arm.edit_description)
    })
    cy.clickButton('save-button')
    cy.waitForFormSave()
    cy.checkSnackbarMessage('Study Arm updated')
})

Then('The study arm with updated values is visible within the study arms table', () => {
    cy.fixture('studyArm').then((arm) => {
        cy.tableContains(arm.edit_name)
        cy.tableContains(arm.edit_short_name)
        cy.tableContains(arm.edit_description)
    })
})

When('The Randomisation Group is populated in the Add New Arm form', () => {
    cy.clickButton('add-study-arm')
    cy.fillInput('arm-randomisation-group', 'testOfValue')
})

When('no value is specified for the field Arm Code', () => {
    cy.get('[data-cy="arm-code"]').click({ force: true })
})

Then('The Arm code field is populated with value from Randomisation group field', () => {
    cy.get('[data-cy="arm-code"]').within(() => {
        cy.get('.v-field__input').should('have.attr', 'value', 'testOfValue')
    })
})

When('The value {string} is entered for the field Number of subjects in the Study Arms form', (example) => {
    cy.clickButton('add-study-arm')
    cy.get('[data-cy="arm-planned-number-of-subjects"]').type(example)
})

Then('The validation appears under the field in the Study Arms form', () => {
    cy.get('.v-messages__message').should('contain', 'Value can\'t be less than 1')
})

When('The Arm name field is not populated', () => {
    cy.clickButton('add-study-arm')
    cy.get('[data-cy="arm-name"]').clear()
})

When('The Arm short name field is not populated', () => {
    cy.get('[data-cy="arm-short-name"]').clear()
})

Then('The required field validation appears for the {string} empty fields', (count) => {
    cy.clickButton('save-button')
    cy.get('.v-messages__message').should('contain', 'This field is required').and('have.length', count)
})

When('The Study Arm is created with given name', () => {
    cy.clickButton('add-study-arm')
    cy.selectFirstVSelect('arm-type')
    cy.fillInput('arm-name', 'Test Arm Name')
    cy.fillInput('arm-short-name', 'TESTOFNAME')
    cy.fillInput('arm-randomisation-group', 'TESTOFNAMERG')
    cy.clickButton('save-button')
    cy.waitForFormSave()
})

When('Another Study Arm is created with the same arm name', () => {
    cy.clickButton('add-study-arm')
    cy.selectFirstVSelect('arm-type')
    cy.fillInput('arm-name', 'Test Arm Name')
    cy.fillInput('arm-short-name', 'TESTOFNAME1')
    cy.fillInput('arm-randomisation-group', 'TESTOFNAMERG1')
    cy.clickButton('save-button')
})

When('The Study Arm is created with given short name', () => {
    cy.clickButton('add-study-arm')
    cy.selectFirstVSelect('arm-type')
    cy.fillInput('arm-name', 'TESTOFSHORTNAME')
    cy.fillInput('arm-short-name', 'Test Short Name')
    cy.fillInput('arm-randomisation-group', 'TESTOFSHORTNAMERG')
    cy.clickButton('save-button')
    cy.waitForFormSave()
})

When('Another Study Arm is created with the same arm short name', () => {
    cy.clickButton('add-study-arm')
    cy.selectFirstVSelect('arm-type')
    cy.fillInput('arm-name', 'TESTOFSHORTNAME1')
    cy.fillInput('arm-short-name', 'Test Short Name')
    cy.fillInput('arm-randomisation-group', 'TESTOFSHORTNAMERG1')
    cy.clickButton('save-button')
})

When('The Study Arm is created with given randomisation group', () => {
    cy.clickButton('add-study-arm')
    cy.selectFirstVSelect('arm-type')
    cy.fillInput('arm-name', 'TESTOFRGN')
    cy.fillInput('arm-short-name', 'TESTOFRGSN')
    cy.fillInput('arm-randomisation-group', 'Test Randomisation Group')
    cy.fillInput('arm-code', 'TESTOFRGSN')
    cy.clickButton('save-button')
    cy.waitForFormSave()
})

When('Another Study Arm is created with the same randomisation group', () => {
    cy.clickButton('add-study-arm')
    cy.selectFirstVSelect('arm-type')
    cy.fillInput('arm-name', 'TESTOFRGN1')
    cy.fillInput('arm-short-name', 'TESTOFRGSN1')
    cy.fillInput('arm-randomisation-group', 'Test Randomisation Group')
    cy.fillInput('arm-code', 'TESTOFRGSN1')
    cy.clickButton('save-button')
})

When('For the {string} a text longer than {string} is provided in the Study Arms form', (field, length) => {
    let textLen = parseInt(length) + 1
    cy.clickButton('add-study-arm')
    cy.get('[data-cy="' + field + '"]').clear().invoke('value', 'a'.repeat(textLen)).trigger('input')
})

When('In the Study Arms form randomistaion group is provided', () => {
    cy.clickButton('add-study-arm')
    cy.get('[data-cy="arm-randomisation-group"]').type('abc')
})

When('The study arm code is updated to exceed 20 characters', () => {
    cy.get('[data-cy="form-body"]').click()
    cy.get('[data-cy="arm-code"] input').clear().type('a'.repeat(21), { delay: 0.1, force: true })
})

Then('The system displays the message {string}', (message) => {
    cy.checkSnackbarMessage(message)
})

Then('The message {string} is displayed', (message) => {
    cy.contains(message).should('exist')
})

When('The delete action is clicked for the {string} study arm', (armName) => {
    cy.rowActionsByValue(armName, 'Delete')
    cy.checkSnackbarMessage('Arm deleted')
})

Then('The {string} arm is no longer available', (armName) => {
    cy.get('tbody').should('not.contain', armName)
})