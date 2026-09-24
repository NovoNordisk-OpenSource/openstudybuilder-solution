const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

let topicCode, activityName, instanceName, nciCode, nciName, adamParam
let existingInstanceName, existingTopicCode, selectedActivityName, codeSubmissionValue

const clearField = (fieldName) => cy.contains('.v-stepper-window-item .v-input', fieldName).clear()
const fillField = (fieldName, value) => cy.contains('.v-stepper-window-item .v-input', fieldName).clear().type(value)
const checkSummary = (name, value) => cy.contains('.summary-label', name).parent().within(() => cy.get('.summary-value').should('have.text', value))
const clickActivityItemClassDropdown = () => cy.get('.v-form .v-card-text').filter(':visible').get('.d-flex .v-input:contains(Activity item class)').last().click()
const checkValue = (name, condition, value) => cy.contains('.v-stepper-window-item .v-input', name).find('input').should(condition, value)

Then('User can see which activity was selected in the previous step', () => cy.get('.v-alert__content').should('contain.text', activityName))

When('User intercepts available activities requests', () => cy.intercept('/api/concepts/activities/activities?page_number=1&page_size=*').as('getActivities'))

When('User intecepts preview request', () => cy.intercept('/api/concepts/activities/activity-instances/preview').as('preview'))

When('User intercepts activity instance creation request with strict_mode verification', () => {
    cy.intercept('POST', '/api/concepts/activities/activity-instances', (req) => {
        expect(req.body).to.have.property('strict_mode', true)
    }).as('createInstanceWithStrictMode')
})

When('User waits for activity instance creation request with strict_mode verification', () => {
    cy.wait('@createInstanceWithStrictMode')
})

When('User intecepts activity groupings request', () => cy.intercept('/api/concepts/activities/activity-instances/*/groupings?*').as('activityGroupings'))

When('User intecepts activity items request', () => cy.intercept('/api/concepts/activities/activity-instances/*/activity-items?*').as('activityItemClasses'))

When('User waits for available activities requests', () => cy.wait('@getActivities'))

When('User waits for preview request', () => cy.wait('@preview'))

When('User waits for activity groupings request', () => cy.wait('@activityGroupings'))

When('User waits for activity items request', () => cy.wait('@activityItemClasses'))

When('User saves activity name created via API', () => cy.getActivityNameByUid().then(name => activityName = name))

Then("User searches for created activity instance", () => cy.searchFor(instanceName))

Then("Created activity instance is displayed in the first table row", () => cy.checkRowByIndex(0, 'Activity Instance', instanceName))

Then("Activity instance is not visible in table", () => cy.searchAndCheckPresence(instanceName, false))

Given("The Activity Instance Wizard Stepper {string} page is displayed", (stepperPage) => {
    cy.contains('.v-stepper-item', stepperPage).should('have.class', 'v-stepper-item--selected')
})

Given("The Activity Instance Attributes edition page is displayed", () => {
    cy.contains('.dialog-title', 'Edit activity instance attributes').should('be.visible')
})

Given("The Activity Instance Groupings edition page is displayed", () => {
    cy.contains('.dialog-title', 'Edit activity instance groupings').should('be.visible')
})

Given("Add activity item class button is clicked", () => cy.get('.v-window-item button').filter(':visible').contains('Add Activity Item Class').eq(0).click())

When("First activity is selected from the activity list", () => cy.get('.v-overlay-container table tbody tr [type="checkbox"]').eq(0).check())

When("The {string} is selected from the Activity instance class field", name => requiredTabSelection('Activity instance', name))

When("The {string} is selected from the Data category field", name => requiredTabSelection('Data category', name))

When("The {string} is selected from the Data SubCategory field", name => requiredTabSelection('Data subcategory (optional)', name))

When("The {string} is selected from the Activity instance domain field", name => requiredTabSelection('Data domain', name))

When('Customize toggle is turn on', () => cy.get('input[aria-label="Customize"]').check())

When('Customize toggle is turn off', () => cy.get('input[aria-label="Customize"]').uncheck())

When("Value {string} is selected for {int} Activity item class field", (value, index) => selectFirstItemClassValue(index, value))

When("For Activity item class {string} value {string} is selected", (name, value) => changeActivityItemClassValue(name, value))

Then("The Activity Item Classes selection displayed", () => cy.contains('.v-overlay .v-row .dialog-title', 'Select Activity Item Classes'). should('be.visible'))

Then("The Activity Item Classes selection is not displayed", () => cy.contains('.v-overlay .v-row .dialog-title', 'Select Activity Item Classes'). should('not.exist'))

Then("Warning about already existing topic code is displayed", () => cy.checkSnackbarMessage(`Activity Instance with Topic Code '${existingTopicCode}' already exists`))

Then("Warning about already existing activity name is displayed", () => cy.checkSnackbarMessage(`Activity Instance with Name '${existingInstanceName}' already exists`))

Then("Automatically assigned activity instance name is saved", () => {
    cy.contains('.v-stepper-window-item .v-input', 'Activity instance name').find('input').invoke('val').then(text => instanceName = text)
})

Then("Final activity instance name is saved", () => cy.get('.v-container .page-title').invoke('text').then(text => instanceName = text.trim()))

Then("The test_code value is not selected", () => cy.contains('.d-flex .v-input', 'Test Code').next().find('label.v-label').should('contain.text', 'Code submission value'))

Then("The test_code value is automatically populated", () => cy.contains('.d-flex .v-input', 'Test Code').next().find('.v-select__selection').should('not.contain.text', 'Code submission value'))

Then("Sentence case name is lowercased version of instance name", () => {
    cy.contains('.v-stepper-window-item .v-input', 'Activity instance name').find('input').invoke('val').then(nameText => {
        cy.contains('.v-stepper-window-item .v-input', 'Sentence case name').find('input').invoke('val').should('equal', nameText.toLowerCase())
    })
})

When("First available value for {string} is selected", (name) => selectFirstActivityItemClassValue(name))

When("First available value and codelist for {string} are selected", (name) => selectFirstCodelistActivityItemClassValue(name))

When("For activity item class {string} value {string} is searched and selected", (name, value) => selectSpecificActivityItemClass(name, value))

When("For activity item class {string} value {string} is selected", (name, value) => selectSpecificActivityItemClass(name, value, false))

When("For activity item class {string}, codelist {string} value {string} is searched and selected", (name, codelist, submissionValue) => selectSpecificCodelistAndActivityItemClass(name, codelist, submissionValue))

When("Activity created via API is searched for", () => cy.searchForInPopUp(activityName))

Then("Correct instance overview page is displayed", () => cy.get('.v-container .page-title').should('contain.text', selectedActivityName))

When("The already used instance name is saved", () => cy.getCellValue(0, 'Activity Instance').then(text => existingInstanceName = text))

When("The already used topic code is saved", () => cy.getCellValue(0, 'Topic code').then(text => existingTopicCode = text))

When("Selected Activity name is saved", () => cy.getCellValueInPopUp(0, 'Activity').then(text => selectedActivityName = text))

When("Selected Code Submission value is saved", () => {
    cy.contains('.d-flex .v-input', 'Test Code').next().find('.v-select__selection').invoke('text').then(val => codeSubmissionValue = val)
})

Then("Activity Instance Data field {string} is cleared", (fieldName) => clearField(fieldName))

When("The instance name is changed to the already used one", () => fillField('Activity instance name', existingInstanceName))

When("The instance name is changed to custom one", () => fillField('Activity instance name', instanceName = `Instance${getShortUniqueId()}`))

When("The instance name and sentence case name are updated", () => fillField('Activity instance name', instanceName += ' update'))

When("The NCI name is set", () => fillField('NCI preferred name (optional)', nciName = 'NCI name'))

When("The NCI code is set", () => fillField('NCI Code (optional)', nciCode = 'NCI code'))

When("The ADaM param is updated", () => fillField('ADaM parameter code', adamParam = `adam ${getShortUniqueId()}`))

When("The sentance case name is set to different value than instance name", () => fillField('Sentence case name', `${getShortUniqueId()}`))

When("The topic code is changed to the already used one", () => fillField('Topic code', existingTopicCode))

When("The Required for Activity checkbox is checked", () => cy.contains('.v-overlay .v-input', 'Required for activity').find('input').check())

When("The Change description is provided", () => cy.contains('.dialog-title', 'Change description').next().find('input').type('test', {force: true}));

Then("Activity Instance Name is identical to selected Activity Name", () => checkValue('Activity instance name', 'have.value', selectedActivityName))

Then("Activity Instance Name have Research added to it", () => checkValue('Activity instance name', 'have.value', `${selectedActivityName} Research`))

Then("Topic code is uppercased version of Activity Instance Name with _ instead of spaces", () => checkValue('Topic code', 'contain.value', selectedActivityName.toUpperCase().replaceAll(' ', '_')))

Then("Topic code have _RESEARCH added to it", () => checkValue('Topic code', 'have.value', `${selectedActivityName.toUpperCase().replaceAll(' ', '_')}_RESEARCH`))

Then("ADaM parameter code is four first letters of selected Code submission value of Activity Item Class", () => {
    checkValue('ADaM parameter code', 'contain.value', codeSubmissionValue.substring(0, 4))
})

Then("ADaM parameter code have X added to it", () => checkValue('ADaM parameter code', 'contain.value', `${codeSubmissionValue.substring(0, 4)}X`))

Then("ADaM parameter code input should not exists", () => {
    cy.contains('.v-stepper-window-item .v-input', 'ADaM parameter code').should('not.exist')
})

When("Data from research lab is checked", () => cy.get('input[aria-label="Data from a Research lab"]').check())

Then('Item classes unit_dimension and standardised unit are not displayed', () => {
    cy.contains('.d-flex .v-input', 'Unit dimension').should('not.exist')
    cy.contains('.d-flex .v-input', 'Standardised unit').should('not.exist')
})

Then('Value for required field {string} is highlighted as required', (name) => {
    cy.get(`.d-flex .v-input:contains(${name})`).next().should('contain.text', 'This field is required')
})

Then('Required field {string} is highlighted as required', (name) => {
    cy.get(`.d-flex .v-input:contains(${name})`).should('contain.text', 'This field is required')
})

Then('Warning about not matching name and sentence case name is displayed', () => {
    cy.get('.d-flex .v-input:contains(Sentence case name)').should('contain.text', 'Sentence case name can only differ in case compared to name value')
})

Then('Only values for Numeric Findings and MK as data domain are displayed for Activity Item Class selection in the Step 3', () => {
    const values = ['Analysis Method', 'Directionality', 'Laterality', 'Location', 'Method', 'Position']
    clickActivityItemClassDropdown()
    values.forEach(value => cy.contains('.v-overlay .v-list-item', value))
    clickActivityItemClassDropdown()
})

Then('Only values for Numeric Findings and MK as data domain are displayed for Activity Item Class selection in the Step 4', () => {
    const values = ['Analysis Method', 'Elapsed Time', 'Evaluation Interval', 'Evaluation Interval Text', 'Evaluator', 'Evaluator Identifier', 'Group Identifier']
    clickActivityItemClassDropdown()
    values.forEach(value => cy.contains('.v-overlay .v-list-item', value))
})

Then('The input with value {string} is disabled', (value) => cy.contains('.v-overlay .v-input', value).find('input').should('be.disabled'))

Then('The activity item class with its value is disabled', () => {
    cy.get('.v-form .v-card-text').filter(':visible').get('.d-flex .v-input:contains(Activity item class)').then(el => {
        cy.wrap(el).find('input').should('be.disabled')
        cy.wrap(el).next().find('input').should('be.disabled')
    })
})

Then('The instance name displayed on the summary has updated value', () => cy.contains('.page-title', instanceName).should('be.visible'))

Then('The Activity instance class displayed on the summary has value {string}', (value) => checkSummary('Activity instance class', value))

Then('The Required for activity displayed on the summary has value {string}', (value) => checkSummary('Required for activity', value))

Then('The Sentence case name displayed on the summary has updated value', () => checkSummary('Sentence case name', instanceName.toLowerCase()))

Then('The NCI Concept Name displayed on the summary has updated value', () => checkSummary('NCI Concept Name', nciName))

Then('The NCI Concept ID displayed on the summary has updated value', () => checkSummary('NCI Concept ID', nciCode))

Then('The ADaM parameter code displayed on the summary has updated value', () => checkSummary('ADaM parameter code', adamParam))

function selectFirstActivityItemClassValue(type) {
    cy.contains('.d-flex .v-input', type).next().click()
    waitForValuesToLoadAndClickByIndex(0)
}

function selectFirstCodelistActivityItemClassValue(type) {
    cy.contains('.d-flex .v-input', type).next().contains('.v-input', 'Codelist').then(el => {
        cy.wrap(el).click()
        waitForValuesToLoadAndClickByIndex(0)
        cy.wrap(el).next().click()
        waitForValuesToLoadAndClickByIndex(1)
    })
}

function selectSpecificActivityItemClass(type, value, search = true) {
    cy.contains('.d-flex .v-input', type).next().click()
    search ? waitForValuesToLoadSearchAndClickByValue(value) : waitForValuesToLoadAndClickByValue(value)
}

function selectSpecificCodelistAndActivityItemClass(type, codelistValue, subimissionValue) {
    cy.contains('.d-flex .v-input', type).next().contains('.v-input', 'Codelist').then(el => {
        cy.wrap(el).click()
        waitForValuesToLoadAndClickByValue(codelistValue)
        cy.wrap(el).next().click()
        waitForValuesToLoadSearchAndClickByValue(subimissionValue)
    })
}

function selectFirstItemClassValue(index, itemClassName) {
    cy.get('.v-form .v-card-text').filter(':visible').eq(index).get('.d-flex .v-input:contains(Activity item class)').last().then(el => {
        cy.wrap(el).click()
        cy.contains('.v-overlay .v-list-item', new RegExp(`^${itemClassName}$`, 'g')).click()
        cy.wrap(el).next().click()
    })
    cy.get('.v-overlay .v-list-item').should('have.length.above', 1).eq(1).click()
    cy.wait(1000)
}

function changeActivityItemClassValue(itemClassName, itemClassValue) {
    cy.get('.v-form .v-card-text').contains('.d-flex .v-input', itemClassName).then(el => cy.wrap(el).next().click())
    cy.get('.v-overlay .v-list-item').should('have.length.above', 1).contains(itemClassValue).click()
    cy.wait(1000)
}

function requiredTabSelection(dropdown_name, value) {
    cy.contains('.v-stepper-window-item .v-input', dropdown_name).click()
    cy.contains('.v-overlay .v-list-item', value).click()
}

function waitForValuesToLoadAndClickByIndex(index) {
    cy.get('.v-overlay .v-list-item').should('not.contain.text', 'No data available')
    cy.get('.v-overlay .v-list-item').eq(index).click()
}

function waitForValuesToLoadAndClickByValue(value) {
    cy.get('.v-overlay .v-list-item').should('not.contain.text', 'No data available')
    cy.contains('.v-overlay .v-list-item', value).click()
}

function waitForValuesToLoadSearchAndClickByValue(value) {
    cy.get('.v-overlay .v-list-item').should('not.contain.text', 'No data available')
    cy.wait(1000)
    cy.get('input[placeholder="Search"]').click().type(value)
    waitForValuesToLoadAndClickByValue(value)
}