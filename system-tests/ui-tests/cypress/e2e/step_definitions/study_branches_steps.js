const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let branchName = "BA Test Arm Name"
let branchShortName = "BA Test Short Name"
let branchRandGroup = "BA Randomisation"
let branchCode = "BA Test Branch Code"

Given('A study without Study Arms has been selected', () => {
    cy.selectTestStudy('Study_000004')
})

Given('A study with Study Arms has been selected', () => {
    cy.selectTestStudy('Study_000001')
    cy.createTestArm('Study_000001')
    cy.reload()
})

When('The form for new study branch arm is filled and saved', () => {
    cy.fixture('studyBranchArm').then((branch_arm) => {
        cy.wait(2500)
        cy.clickButton('add-study-branch-arm')
        cy.selectFirstVSelect('study-arm')
        cy.fillInput('study-branch-arm-name', branch_arm.name)
        cy.fillInput('study-branch-arm-short-name', branch_arm.short_name)
        cy.fillInput('study-branch-arm-randomisation-group', branch_arm.randomisation_group)
        cy.fillInput('study-branch-arm-code', branch_arm.code)
        cy.fillInput('study-branch-arm-planned-number-of-subjects', branch_arm.no_of_subjects)
        cy.fillInput('study-branch-arm-description', branch_arm.description)
        cy.clickButton('save-button')
    })
})

Then('The study branch arm is visible within the table', () => {
    cy.wait(2000)
    cy.fixture('studyBranchArm').then((branch_arm) => {
        cy.checkRowValueByColumnName(branch_arm.name, 'Branch arm name', branch_arm.name)
        cy.checkRowValueByColumnName(branch_arm.name, 'Branch arm short name', branch_arm.short_name)
        cy.checkRowValueByColumnName(branch_arm.name, 'Branch Code', branch_arm.code)
        cy.checkRowValueByColumnName(branch_arm.name, 'Randomisation group', branch_arm.randomisation_group)
        cy.checkRowValueByColumnName(branch_arm.name, 'Number of subjects', branch_arm.no_of_subjects)
        cy.checkRowValueByColumnName(branch_arm.name, 'Description', branch_arm.description)
    })
})

When('The study branch arm is edited', () => {
    cy.fixture('studyBranchArm').then((branch_arm) => {
        cy.rowActionsByValue(branch_arm.name, 'Edit')
        cy.fillInput('study-branch-arm-name', branch_arm.edit_name)
        cy.fillInput('study-branch-arm-short-name', branch_arm.edit_short_name)
        cy.fillInput('study-branch-arm-description', branch_arm.edit_description)
    })
    cy.clickButton('save-button')
    cy.waitForFormSave()
    cy.checkSnackbarMessage('Branch Arm updated')
})

Then('The study branch arm with updated values is visible within the table', () => {
    cy.fixture('studyBranchArm').then((branch_arm) => {
        cy.checkRowValueByColumnName(branch_arm.edit_name, 'Branch arm name', branch_arm.edit_name)
        cy.checkRowValueByColumnName(branch_arm.edit_name, 'Branch arm short name', branch_arm.edit_short_name)
        cy.checkRowValueByColumnName(branch_arm.edit_name, 'Branch Code', branch_arm.code)
        cy.checkRowValueByColumnName(branch_arm.edit_name, 'Randomisation group', branch_arm.randomisation_group)
        cy.checkRowValueByColumnName(branch_arm.edit_name, 'Number of subjects', branch_arm.no_of_subjects)
        cy.checkRowValueByColumnName(branch_arm.edit_name, 'Description', branch_arm.edit_description)
    })
})

When('The new Study Branch Arm with selected Study Arm is added', () => {
    cy.wait(2500)
    cy.clickButton('add-study-branch-arm')
    cy.wait(1500)
    cy.selectFirstVSelect('study-arm')
    cy.fillInput('study-branch-arm-name', 'a'.repeat(3))
    cy.fillInput('study-branch-arm-short-name', 'a'.repeat(3))
    cy.fillInput('study-branch-arm-randomisation-group', 'a'.repeat(3))
    cy.clickButton('save-button')
})

Then('The edit form for the branch arm has the Arm name field disabled', () => {
    cy.get('[data-cy="table-item-action-button"]').first().click()
    cy.get('[data-cy="Edit"]').filter(':visible').click()
    cy.get('[data-cy="study-arm"]').should('have.class', 'v-input--disabled')
})

When('The Randomisation Group is populated in the Add New Branch Arm form', () => {
    cy.wait(2500)
    cy.clickButton('add-study-branch-arm')
    cy.wait(1500)
    cy.fillInput('study-branch-arm-randomisation-group', 'testOfValue')
})

When('No value is specified for the field Branch Arm Code', () => {
    cy.clickButton('form-body')
    cy.contains('testOfValue').should('have.length', 2)
})

Then('The Branch Arm code field is populated with value from Randomisation group field', () => {
    cy.get('[data-cy="study-branch-arm-code"]').invoke('val').should('contain', 'testOfValue')
})

When('The value {string} is entered for the field Number of subjects in the Study Branch Arms form', (example) => {
    cy.wait(2500)
    cy.clickButton('add-study-branch-arm')
    cy.wait(1500)
    cy.selectFirstVSelect('study-arm')
    cy.get('[data-cy="study-branch-arm-planned-number-of-subjects"]').type(example)
})

Then('The validation appears under the field in the Study Branch Arms form', (lessThan) => {
    cy.get('.v-messages__message').should('contain', "Value can't be less than 1")
})

When('The value entered for the field Number of subjects is higher than the value defined for the selected study arm in the Study Branch Arms form', () => {
    cy.wait(2500)
    cy.clickButton('add-study-branch-arm')
    cy.wait(1500)
    cy.selectFirstVSelect('study-arm')
    cy.fillInput('study-branch-arm-planned-number-of-subjects', 101)
})

When('The Study Arm field is not populated in the Study Branch Arms form', () => {
    cy.wait(2500)
    cy.clickButton('add-study-branch-arm')
    cy.wait(1500)
    cy.get('[data-cy="study-arm"]').click()
    cy.get('[data-cy="study-arm"] input').clear()
})

When('The Branch Arm name field is not populated', () => {
    cy.get('[data-cy="study-branch-arm-name"]').click()
    cy.get('[data-cy="study-branch-arm-name"] input').clear()
})

When('The Branch Arm short name field is not populated', () => {
    cy.log('Empty by default')
})

When('The Study Branch Arm is created with given branch arm name', () => {
    cy.wait(2500)
    cy.clickButton('add-study-branch-arm')
    cy.wait(1500)
    cy.selectFirstVSelect('study-arm')
    cy.fillInput('study-branch-arm-name', branchName)
    cy.fillInput('study-branch-arm-short-name', Date.now())
    cy.fillInput('study-branch-arm-randomisation-group', Date.now())
    cy.clickButton('save-button')
    cy.waitForFormSave()
})

When('Another Study Branch Arm is created with the same arm name', () => {
    cy.wait(2500)
    cy.clickButton('add-study-branch-arm')
    cy.wait(1500)
    cy.selectFirstVSelect('study-arm')
    cy.fillInput('study-branch-arm-name', branchName)
    cy.fillInput('study-branch-arm-short-name', Date.now())
    cy.fillInput('study-branch-arm-randomisation-group', Date.now())
    cy.clickButton('save-button')
})

When('The Study Branch Arm is created with given branch arm short name', () => {
    cy.wait(2500)
    cy.clickButton('add-study-branch-arm')
    cy.wait(1500)
    cy.selectFirstVSelect('study-arm')
    cy.fillInput('study-branch-arm-name', Date.now())
    cy.fillInput('study-branch-arm-short-name', branchShortName)
    cy.fillInput('study-branch-arm-randomisation-group', Date.now())
    cy.clickButton('save-button')

    cy.waitForFormSave()
})

When('Another Study Branch Arm is created with the same branch arm short name', () => {
    cy.wait(2500)
    cy.clickButton('add-study-branch-arm')
    cy.wait(1500)
    cy.selectFirstVSelect('study-arm')
    cy.fillInput('study-branch-arm-name', Date.now())
    cy.fillInput('study-branch-arm-short-name', branchShortName)
    cy.fillInput('study-branch-arm-randomisation-group', Date.now())
    cy.clickButton('save-button')

})

When('The Study Branch Arm is created with given branch arm randomisation group', () => {
    cy.wait(2500)
    cy.clickButton('add-study-branch-arm')
    cy.wait(1500)
    cy.selectFirstVSelect('study-arm')
    cy.fillInput('study-branch-arm-name', Date.now())
    cy.fillInput('study-branch-arm-short-name', Date.now())
    cy.fillInput('study-branch-arm-randomisation-group', branchRandGroup)
    cy.clickButton('save-button')
    cy.waitForFormSave()
})

When('Another Study Branch Arm is created with the same randomisation group', () => {
    cy.wait(2500)
    cy.clickButton('add-study-branch-arm')
    cy.wait(1500)
    cy.selectFirstVSelect('study-arm')
    cy.fillInput('study-branch-arm-name', Date.now())
    cy.fillInput('study-branch-arm-short-name', Date.now())
    cy.fillInput('study-branch-arm-randomisation-group', branchRandGroup)
    cy.fillInput('study-branch-arm-code', "arm-code")
    cy.clickButton('save-button')
})

When('The Study Branch Arm is created with given branch code', () => {
    cy.wait(2500)
    cy.clickButton('add-study-branch-arm')
    cy.wait(1500)
    cy.selectFirstVSelect('study-arm')
    cy.fillInput('study-branch-arm-name', Date.now())
    cy.fillInput('study-branch-arm-short-name', Date.now())
    cy.fillInput('study-branch-arm-randomisation-group', Date.now())
    cy.fillInput('study-branch-arm-code', branchCode)
    cy.clickButton('save-button')
    cy.waitForFormSave()
})

When('Another Study Branch Arm is created with the same branch code', () => {
    cy.wait(2500)
    cy.clickButton('add-study-branch-arm')
    cy.wait(1500)
    cy.selectFirstVSelect('study-arm')
    cy.fillInput('study-branch-arm-name', Date.now())
    cy.fillInput('study-branch-arm-short-name', Date.now())
    cy.fillInput('study-branch-arm-randomisation-group', Date.now())
    cy.fillInput('study-branch-arm-code', branchCode)
    cy.clickButton('save-button')
})

When('For the {string} a text longer than {string} is provided in the Study Branch Arms form', (field, length) => {
    let textLen = parseInt(length) + 1
    cy.wait(2500)
    cy.clickButton('add-study-branch-arm')
    cy.get('[data-cy="' + field + '"]')
        .clear()
        .invoke('val', 'a'.repeat(textLen))
        .trigger('input')
})

When('For the Branch Code a text longer than 20 characters is provided in the Study Branch Arms form', (field) => {
    cy.wait(2500)
    cy.clickButton('add-study-branch-arm')
    cy.wait(1500)
    cy.fillInput('study-branch-arm-randomisation-group', 'valtest')
    cy.fillInput('study-branch-arm-code', 'a'.repeat(21))
})

Then('The window of {string} is opened', (message) => {
    cy.elementContain('form-body', message)
})

Then('The Study Arm field is visible', () => {
    cy.get('[data-cy="study-arm"]').should('exist')
})


Then('The user clicks on Add Study Arm button in the information popup', () => {
    cy.clickButton('continue-popup')
})

Then('The Arm name field is visible', () => {
    cy.get('[data-cy="arm-name"]').should('exist')
    cy.clickButton('cancel-button')
})


