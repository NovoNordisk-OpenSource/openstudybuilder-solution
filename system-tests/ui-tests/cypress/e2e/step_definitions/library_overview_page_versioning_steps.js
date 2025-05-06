const { Given, When, Then } = require('@badeball/cypress-cucumber-preprocessor');

let activityName, instanceName, groupName, subgroupName
const checkInstanceStatusAndVersion = (status, version) => checkStatusAndVersion('Activity instances', instanceName, status, version)
const checkActivitytatusAndVersion = (status, version) => checkStatusAndVersion('Activity', activityName, status, version)
const checkActivitiesStatusAndVersion = (status, version) => checkStatusAndVersion('Activities', activityName, status, version)
const checkGroupStatusAndVersion = (status, version) => checkStatusAndVersion('Activity group', groupName, status, version)
const checkSubgroupStatusAndVersion = (status, version) => checkStatusAndVersion('Activity subgroups', subgroupName, status, version)
const checkIfTableEmpty = (type) => cy.contains('.v-row', type).find('table tbody').should('be.empty')

Given('[API] Activity, activity instance, group and subgroup names are fetched', () => {
    cy.getActivityNameByUid().then(name => activityName = name)
    cy.getActivityInstanceNameByUid().then(name => instanceName = name)
    cy.getGroupNameByUid().then(name => groupName = name)
    cy.getSubGroupNameByUid().then(name => subgroupName = name)
})

Given('A test activity overview page is opened', () => goToOverviewPageAndVerify(activityName))

Given('A test instance overview page is opened', () => goToOverviewPageAndVerify(instanceName))

Given('A test group overview page is opened', () => goToOverviewPageAndVerify(groupName))

Given('A test subgroup overview page is opened', () => goToOverviewPageAndVerify(subgroupName))

When('I click {string} button', (title) => cy.get(`button.v-btn[title="${title}"]`).click())

When('I make changes to the activity, enter a reason for change and save', () => edit('activity', activityName))

When('I make changes to the instance and save', () => edit('instance', instanceName))

When('I make changes to the group, enter a reason for change and save', () => edit('group', groupName))

When('I make changes to the subgroup, enter a reason for change and save', () => edit('subgroup', subgroupName))

Then('I verify that the version is {string} and status is {string}', (version, status) => {
    cy.contains('.v-col', 'Version').next().find('input').should('have.value', version)
    cy.contains('.v-col', 'Status').next().should('have.text', status)
})

Then('I verify the definition is {string}', (definition) => cy.contains('.v-col', 'Definition').next().should('have.text', definition))

When('I select the earlier version 2.0 from the version dropdown list', () => {
    cy.get('.v-col:contains("Version") + .v-col .v-select__selection').should('have.text', '2.0');
})

Then('I verify that no {string} is linked', (type) => checkIfTableEmpty(type))

Then('I verify that there is an instance with status {string} and version {string}', (status, version) => checkInstanceStatusAndVersion(status, version))

Then('I verify that there is an activity with status {string} and version {string}', (status, version) => checkActivitytatusAndVersion(status, version))

Then('I verify that there are activities with status {string} and version {string}', (status, version) => checkActivitiesStatusAndVersion(status, version))

Then('I verify that there is a group with status {string} and version {string}', (status, version) => checkGroupStatusAndVersion(status, version))

Then('I verify that there is a subgroup with status {string} and version {string}', (status, version) => checkSubgroupStatusAndVersion(status, version))

function goToOverviewPageAndVerify(name) {
    cy.searchFor(name)
    cy.get('table tbody tr td').contains(name).click()
    cy.get('.d-flex.page-title').should('contain.text', name);
    cy.get('button[role="tab"][value="html"]').contains('Overview');
}

function edit(type, name) {
    cy.wait(2000)
    if (type == 'instance') {
        cy.clickFormActionButton('continue')
        cy.clickFormActionButton('continue')
        cy.fillInput('instanceform-instancename-field',  `Update ${name}`)
    }
    else if (type == 'activity') {
        cy.fillInput('activityform-activity-name-field', `Update ${name}`)
        cy.contains('.v-col', 'Reason for change').find('textarea').not('.v-textarea__sizer').type('Test purpose')
    }
    else {
        cy.fillInput('groupform-activity-group-field', `Update ${name}`)
        cy.fillInput('groupform-change-description-field', "Test purpose")
    }
    cy.clickFormActionButton('save')
}

function checkStatusAndVersion(type, name, status, version) {
    cy.get('.v-row').contains(new RegExp(`^${type}$`, "g")).parent().find('table tbody').within(() => {
        cy.contains('tr', status).should('contain', name).should('contain', version)
    })
}
