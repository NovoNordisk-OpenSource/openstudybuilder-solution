const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let defaultTimeframeText = Date.now() + ' '
let template
let templateName
let oldVersion
let rowIndex

Given('The test time frame template exists with a status as {string}', (status) => {
  getRowIndexAndTemplateVersion(status)
});

Given('The test timeframe template exists in draft status and version 0.1', () => {
  addTemplate()
  getRowIndexAndTemplateVersion(template)
});

Given('The test timeframe template exists in Draft status and version 1.1', () => {
  addTemplateWithStatus(['Approve', 'New version'])
});

Given('The test timeframe template exists in Final status and version 1.0', () => {
  addTemplateWithStatus(['Approve'])
})

Given('The test timeframe template exists in Retired status', () => {
  addTemplateWithStatus(['Approve', 'Inactivate'])
})

Then('The {string} window is displayed', (window) => {
  cy.get(`[data-cy="version-history-window"]`).should('be.visible');
  cy.get('.dialog-title').contains(window)
})

When('The three dots menu list clicked for the test template', () => {
  cy.clickTableActionsButton(rowIndex)
})

When('The template is updated with test data and saved', () => {
  templateName = "Testing edit functionality"
  cy.get('.ql-editor').clear({ force: true }).type(templateName);
  cy.clickButton('save-button')
})

When('The Add time frame template section selected with test data', () => {
  cy.clickButton('add-template')
  cy.get('.dialog-title').contains('Add time frame template')
  cy.get('[data-cy="input-field"]').type(defaultTimeframeText);
  cy.wait(500)
  cy.get('[data-cy="types-dropdown"] .v-list-item').first().within(($option) => {
    let templateName = $option.text().trim().replace('[', '').replace(']', '');
    template = defaultTimeframeText + templateName
    cy.wrap($option).click()
  })
})

Then('The Delete option is not available for the Drafted template not in initial version', () => {
  cy.wait(500)
  cy.get('.v-list-item__content').should('contain', 'Edit');
  cy.get('.v-list-item__content').should('not.contain', 'Delete');
})

Then('The new Timeframe is visible in the Timeframe Template Table', () => {
  cy.getRowIndexByText(template).then(index => {
    rowIndex = index
    checkStatusAndVersion('Draft', '0.1')
  })
  cy.checkRowValueByColumnName(defaultTimeframeText, 'Template', template)
})

Then('The template is created as a draft version with an incremented value as an example 1.1', () => {
  checkStatusAndVersion('Draft', '1.1')
})

Then('The timeframe template is displayed with a status as {string} with the same version as before', (status) => {
  checkStatusAndVersion(status, oldVersion)
})

Then('The status of the template displayed as {string} with an incremented value as an example as 1.0', (status) => {
  checkStatusAndVersion(status, '1.0')
})

Then('The updated Timeframe is visible in the Timeframe Template Table', () => {
  checkStatusAndVersion('Draft', oldVersion + 0.1)
  cy.checkRowByIndex(rowIndex, 'Template', templateName)
})

Then('The drafted template is disappered from the table', () => {
  cy.checkRowByIndexToNotContain(rowIndex, 'Template', templateName)
})

When('The Add template button is clicked', () => {
  cy.clickButton('add-template')
})

When('Change description field is not filled with test data', () => {
  cy.get('.v-input').contains('Change description').parent().clear()
  cy.clickButton('save-button')
})

Then('The Add time frame template window is opened', (tab) => {
  cy.get('.dialog-title').contains('Add time frame template')
})

When('The Add time frame template section selected without test data', () => {
  cy.clickButton('add-template')
  cy.get('.dialog-title').contains('Add time frame template')
  cy.clickButton('save-button')
})

When('The {string} option is selected from the three dot menu list', (action) => {
  cy.wait(1000)
  cy.tableRowActions(rowIndex, action)
})

Then('The {string} tab is displayed by default', (tab) => {
  cy.get('.v-tab-item--selected').contains(tab)
})

Then('The message is displayed as {string}', (message) => {
  cy.get('[role="alert"]').contains(message)
})

function getRowIndexAndTemplateVersion(rowText) {
  cy.getRowIndexByText(rowText).then(index => {
    rowIndex = index
    cy.getValueFromCellsWithIndex(rowIndex, 5).then(value => {
      oldVersion = parseFloat(value)
    })
  })
}

function checkStatusAndVersion(status, version) {
  cy.waitForTable()
  cy.checkRowByIndex(rowIndex, 'Status', status)
  cy.checkRowByIndex(rowIndex, 'Version', version)
}

function addTemplate() {
  template = Date.now()
  cy.waitForTable()
  cy.clickButton('add-template')
  cy.get('[data-cy="input-field"]').type(template);
  cy.wait(1500)
  cy.clickButton('save-button')
  cy.wait(1500)
}

function addTemplateWithStatus(statusList) {
  addTemplate()
  statusList.forEach(status => {
    cy.rowActionsByValue(template, status)
    cy.wait(1500)
  })
  getRowIndexAndTemplateVersion(template)
}