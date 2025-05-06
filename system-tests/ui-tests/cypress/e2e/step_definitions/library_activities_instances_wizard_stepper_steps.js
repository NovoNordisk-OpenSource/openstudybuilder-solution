const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let topicCode, instanceName

Then("Created activity is visible in table", () => cy.searchAndCheckPresence(instanceName, true))

Given("The Activity Instance Wizard Stepper {string} page is displayed", (stepperPage) => {
    cy.contains('.v-stepper-item', stepperPage).should('have.class', 'v-stepper-item--selected')
})

Given("Add activity item class button is clicked", () => cy.contains('.v-window-item button', 'Add Activity Item Class').click())

When("An Activity is selected from the activity list", () => {
    cy.get('.v-overlay-container table tbody tr [type="radio"]').eq(0).check()
})

When("The {string} is selected from the Activity instance class field", name => requiredTabSelection('Activity instance', name))

When("First value is selected from the Activity instance class field", () => selectFirstActivityInstanceClass())

When("First value is selected from the Activity item class field", () => selectOptionalActivityItemClass(0))

When("Second value is selected from the Activity item class field", () => selectOptionalActivityItemClass(1))

When("The {string} is selected from the Activity instance domain field", name => requiredTabSelection('Data domain', name))

Then("The test_code, test_name, unit_dimention and standard_unit fields are inactive", () => validateRequiredInstanceClassFields('have.class', 'v-input--disabled'))

Then("The test_code, test_name, unit_dimention and standard_unit values are empty", () => validateRequiredInstanceClassFields('have.value', ''))

Then("The Required Activity Item Classes field is displayed", () => cy.contains('.v-overlay .v-row .dialog-title', 'Required Activity Item Classes'). should('be.visible'))

Then("Warning is displayed for mandatory field {string}", (fieldName) => warningIsDisplayed(fieldName))

Then("Warning about not matching name and sentence case name is displayed", () => cy.checkSnackbarMessage("Data validation error: Lowercase versions of"))

Then("Warning about already existing topic code is displayed", () => cy.checkSnackbarMessage(`Activity Instance with Topic Code '${topicCode}' already exists`))

Then("Warning about already existing activity name is displayed", () => cy.checkSnackbarMessage(`Activity Instance with Name '${instanceName}' already exists`))

Then("Mandatory field {string} is cleared", (fieldName) => clearField(fieldName))

Then("Field {string} is filled with value {string}", (fieldName, value) => fillField(fieldName, value))

Then("Automatically assigned activity instance name is saved", () => {
    cy.contains('.v-stepper-window-item .v-input', 'Activity instance name').find('input').invoke('val').then(text => instanceName = text)
})

Then("Activity instance is created", () => createInstance(true, true))

Then("Second Activity instance with the same topic code is created", () => createInstance(true, false))

Then("Second Activity instance with the same name is created", () => createInstance(false, true))

Then("The test_code value is automatically populated", () => cy.contains('.d-flex .v-input', 'test_code').next().should('not.be.empty'))

Then("The standard_unit value is not automatically populated", () => cy.contains('.d-flex .v-input', 'standard_unit').next().should('have.value', ''))

Then("The test_code value is enabled for picking different value", () => {
    cy.contains('.d-flex .v-input', 'test_code').next().click()
    cy.get('.v-overlay .v-list-item').eq(1).click()
})

Then("Sentence case name is lowercased version of instance name", () => {
    cy.contains('.v-stepper-window-item .v-input', 'Activity instance name').find('input').invoke('val').then(nameText => {
        cy.contains('.v-stepper-window-item .v-input', 'Sentence case name').find('input').invoke('val').should('equal', nameText.toLowerCase())
    })
})

When("The test_name value is selected", () => {
    cy.wait(2500)
    selectRequiredActivityItemClass('test_name')
})

When("The unit_dimension value is selected", () => selectRequiredActivityItemClass('unit_dimension'))

When("The Required Activity Item Classes field is filled with data", () => {
    cy.wait(4000)
    selectRequiredActivityItemClass('test_name')
    selectRequiredActivityItemClass('unit_dimension')
    selectRequiredActivityItemClass('standard_unit')
})

When("Activity created via API is searched for", () => {
    cy.getActivityNameByUid().then(name => cy.searchForInPopUp(name))
})

function createInstance(uniqueName, uniqueTopicCode) {
    cy.intercept('/api/concepts/activities/activity-instances').as('createInstance')
    if (uniqueName) instanceName = `Instance${Date.now()}`
    if (uniqueTopicCode) topicCode = `Topic${Date.now()}`
    cy.clickButton('add-activity')
    cy.wait(1000)
    cy.get('.v-overlay-container table tbody tr [type="radio"]').eq(0).check()
    cy.clickFormActionButton('continue')
    selectFirstActivityInstanceClass()
    cy.clickFormActionButton('continue')
    fillField('ADaM parameter', 'ADAM')
    fillField('Topic code', topicCode)
    fillField('Activity instance name', instanceName)
    fillField('Sentence case name', instanceName.toLowerCase())
    cy.clickFormActionButton('continue')
    cy.clickFormActionButton('save')
    cy.wait('@createInstance')
    cy.waitForTable()
}

function selectRequiredActivityItemClass(type) {
    cy.contains('.d-flex .v-input', type).next().click()
    cy.get('.v-overlay .v-list-item').eq(0).click()
}

function selectOptionalActivityItemClass(itemClassIndex) {
    cy.get('.v-form .v-card-text').filter(':visible').eq(itemClassIndex).contains('.d-flex .v-input', 'Activity item class').click()
    cy.get('.v-overlay .v-list-item').eq(itemClassIndex).click()
    cy.get('.v-form .v-card-text').filter(':visible').eq(itemClassIndex).contains('.d-flex .v-input', 'Activity item class').next().click()
    cy.get('.v-overlay .v-list-item').eq(0).should('not.have.text', 'No data available').click()
}

function requiredTabSelection(dropdown_name, value) {
    cy.contains('.v-stepper-window-item .v-input', dropdown_name).click()
    cy.contains('.v-overlay .v-list-item', value).click()
}

function selectFirstActivityInstanceClass() {
    cy.contains('.v-stepper-window-item .v-input', 'Activity instance').click()
    cy.get('.v-overlay .v-list-item').eq(0).click()
}

function warningIsDisplayed(fieldName) {
    cy.contains('.v-stepper-window-item .v-input', fieldName).contains('This field is required').should('be.visible')
}

function clearField(fieldName) {
    cy.contains('.v-stepper-window-item .v-input', fieldName).clear()
}

function fillField(fieldName, value) {
    cy.contains('.v-stepper-window-item .v-input', fieldName).clear().type(value)
}

function validateRequiredInstanceClassFields(validationRule, validationValue) {
    cy.contains('.d-flex .v-input', 'test_name').should(validationRule, validationValue)
    cy.contains('.d-flex .v-input', 'test_code').should(validationRule, validationValue)
    cy.contains('.d-flex .v-input', 'unit_dimension').should(validationRule, validationValue)
    cy.contains('.d-flex .v-input', 'standard_unit').should(validationRule, validationValue)
}