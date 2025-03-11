const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let cohort_code = 50
When('The form for new study cohort is filled and saved', () => {
  cy.fixture('studyCohort').then((cohort) => {
    cy.clickButton('add-study-cohort')
    cy.fillInput('study-cohort-name', cohort.name)
    cy.fillInput('study-cohort-short-name', cohort.short_name)
    cy.fillInput('study-cohort-code', cohort_code)
    cohort_code = cohort_code + 1
    cy.fillInput('study-cohort-description', cohort.description)
    cy.clickButton('save-button')
  })
})
When('The form for new study cohort is filled', () => {
  cy.fixture('studyCohort').then((cohort) => {
    cy.clickButton('add-study-cohort')
    cy.fillInput('study-cohort-name', cohort.name)
    cy.fillInput('study-cohort-short-name', cohort.short_name)
    cy.fillInput('study-cohort-code', cohort_code)
    cohort_code = cohort_code + 1
    cy.fillInput('study-cohort-description', cohort.description)
  })
})


Then('The study cohort is visible within the table', () => {
  cy.fixture('studyCohort').then((cohort) => {
    cy.tableContains(cohort.name)
    cy.tableContains(cohort.short_name)
    cy.tableContains(cohort.code)
    cy.tableContains(cohort.description)
  })
})

When('The study cohort is edited', () => {
  cy.fixture('studyCohort').then((cohort) => {
    cy.rowActionsByValue(cohort.name, 'Edit')
    cy.fillInput('study-cohort-name', cohort.edit_name)
    cy.fillInput('study-cohort-short-name', cohort.edit_short_name)
    cy.fillInput('study-cohort-description', cohort.edit_description)
  })
  cy.clickButton('save-button')
  cy.waitForFormSave()
  cy.checkSnackbarMessage('Cohort updated')
})

When('The study cohort is edit form is opened', () => {
    cy.wait(1500)
    cy.tableRowActions(0, 'Edit')
})

Then('The fields of Arm and Branch arms in the cohort edit form are active for editing', () => {
    cy.get('[data-cy="study-arm"]').should('not.have.attr', 'disabled')
    cy.get('[data-cy="branch-arm"]').should('not.have.attr', 'disabled')
})

Then('The study cohort with updated values is visible within the table', () => {
  cy.fixture('studyCohort').then((cohort) => {
    cy.tableContains(cohort.edit_name)
    cy.tableContains(cohort.edit_short_name)
    cy.tableContains(cohort.edit_description)
  })
})

When('The new Study Cohort with selected Study Arm is added', () => {
  cy.clickButton('add-study-cohort')
  cy.fillInput('study-cohort-name', 'a'.repeat(3))
  cy.fillInput('study-cohort-short-name', 'a'.repeat(3))
  cy.fillInput('study-cohort-code', 'a'.repeat(3))
  cy.fillInput('study-cohort-planned-number-of-subjects', '1')
  cy.clickButton('save-button')
})

When('No value is specified for the field Cohort Code', () => {
  cy.get('[data-cy="study-cohort-code"]').click({ force: true })
})

When('The value {string} is entered for the field Number of subjects in the Study Cohorts form', (example) => {
  cy.clickButton('add-study-cohort')
  cy.selectFirstMultipleSelect('study-arm')
  cy.get('[data-cy="study-cohort-planned-number-of-subjects"]').type(example)
})

Then('The validation appears under the field in the Study Cohorts form', (lessThan) => {
  cy.get('.v-messages__message').should('contain', "Value can't be less than 1")
})

When('The value entered for the field Number of subjects is higher than the value defined for the selected study arm in the Study Cohorts form', () => {
  cy.clickButton('add-study-cohort')
  cy.selectFirstMultipleSelect('study-arm')
  cy.fillInput('study-cohort-planned-number-of-subjects', 101)
})

When('The Study Arm field is not populated in the Study Cohorts form', () => {
  cy.clickButton('add-study-cohort')
  cy.get('[data-cy="study-arm"]').clear({ force: true })
})

When('The Study Branch field is not populated in the Study Cohorts form', () => {
  cy.get('[data-cy="branch-arm"]').clear({ force: true })
})

When('The Cohort name field is not populated', () => {
  cy.clearField('study-cohort-name')
})

When('The Cohort short name field is not populated', () => {
  cy.clearField('study-cohort-short-name')
})

When('The Cohort code field is not populated', () => {
  cy.clearField('study-cohort-code')
})

When('The Study Cohort is created with given cohort name', () => {
  cy.clickButton('add-study-cohort')
  cy.selectFirstMultipleSelect('study-arm')
  cy.fillInput('study-cohort-name', 'Cohort Test Name')
  cy.fillInput('study-cohort-short-name', 'CH TN')
  cy.fillInput('study-cohort-code', '12')
  // cy.fillInput('study-cohort-planned-number-of-subjects', '1')
  cy.clickButton('save-button')
  cy.waitForFormSave()
})

When('Another Study Cohort is created with the same cohort name', () => {
  cy.clickButton('add-study-cohort')
  cy.fillInput('study-cohort-name', 'Cohort Test Name')
  cy.fillInput('study-cohort-short-name', 'CH TN1')
  cy.fillInput('study-cohort-code', '11')
  // cy.fillInput('study-cohort-planned-number-of-subjects', '1')
  cy.clickButton('save-button')
})

When('The Study Cohort is created with given cohort short name', () => {
  cy.clickButton('add-study-cohort')
  cy.selectFirstMultipleSelect('study-arm')
  cy.fillInput('study-cohort-name', 'CH TSN')
  cy.fillInput('study-cohort-short-name', 'CH Test Short Name')
  cy.fillInput('study-cohort-code', '13')
  // cy.fillInput('study-cohort-planned-number-of-subjects', '1')
  cy.clickButton('save-button')
  cy.waitForFormSave()
})

When('Another Study Cohort is created with the same cohort short name', () => {
  cy.clickButton('add-study-cohort')
  cy.selectFirstMultipleSelect('study-arm')
  cy.fillInput('study-cohort-name', 'CH TSN1')
  cy.fillInput('study-cohort-short-name', 'CH Test Short Name')
  cy.fillInput('study-cohort-code', '14')
  // cy.fillInput('study-cohort-planned-number-of-subjects', '1')
  cy.clickButton('save-button')
})

When('The Study Cohort is created with given cohort code', () => {
  cy.clickButton('add-study-cohort')
  cy.selectFirstMultipleSelect('study-arm')
  cy.fillInput('study-cohort-name', 'CH TCD')
  cy.fillInput('study-cohort-short-name', 'CH TCD')
  cy.fillInput('study-cohort-code', '88')
  // cy.fillInput('study-cohort-planned-number-of-subjects', '1')
  cy.clickButton('save-button')
  cy.waitForFormSave()
})

When('Another Study Cohort is created with the same cohort code', () => {
  cy.clickButton('add-study-cohort')
  cy.selectFirstMultipleSelect('study-arm')
  cy.fillInput('study-cohort-name', 'CH TCD1')
  cy.fillInput('study-cohort-short-name', 'CH TCD1')
  cy.fillInput('study-cohort-code', '88')
  // cy.fillInput('study-cohort-planned-number-of-subjects', '1')
  cy.clickButton('save-button')
})

When('For the {string} a text longer than {string} is provided in the Study Cohorts form', (field, length) => {
  let textLen = parseInt(length) + 1
  cy.clickButton('add-study-cohort')
  cy.get('[data-cy="' + field + '"]').within(() => {
    cy.get('.v-field__input')
      .clear()
      .invoke('val', 'a'.repeat(textLen))
      .trigger('input')
    
  })

})

When('For the Cohort Code a value higher than 90 is provided in the Study Cohorts form', (field) => {
  cy.clickButton('add-study-cohort')
  cy.fillInput('study-cohort-code', '91')
})

Then('The validation appears for cohort code field {string}', (message) => {
  cy.get('.v-messages__message').should('contain', message)
})

When('For the {string} a {string} value is provided in Study Cohort form', (field, number) => {
  let value = parseInt(number)
  cy.clickButton('add-study-cohort')
  cy.fillInput('study-cohort-code', value)

})