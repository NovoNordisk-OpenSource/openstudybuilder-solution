import { apiGroupName, apiSubgroupName } from "./api_library_steps"
import { group_uid, subgroup_uid } from '../../support/api_requests/library_activities'
import { generateShortUniqueName } from "../../support/helper_functions";

const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getShortUniqueId } = require("../../support/helper_functions");

export let activityName, synonym, currentSubgroupName, currentGroupName
const nciconceptid = "NCIID", nciconceptname = "NCINAME", abbreviation = "ABB", definition = "DEF"

Then('User fills in the reason for change', () => cy.contains('.v-label', 'Reason for change').parent().find('[value]').type('Test update'))

Then('User toggles on the Archived Library', (value) => cy.contains('.v-switch', 'Archived library').find('input').check())

Then('The Library value is set to {string}', (value) => cy.checkRowByIndex(0, 'Library', value))

Then('Activity is present in first table row', () => cy.checkRowByIndex(0, 'Activity name', activityName))

When('The Add activity button is clicked', () => cy.clickButton('add-activity'))

Then('Activity is searched for and not found', () => cy.searchAndCheckPresence(activityName, false))

Then('Activity is searched for and found', () => cy.searchAndCheckPresence(activityName, true))

Then('Validation error for {string} subgroup is displayed', (status) => {
    cy.checkSnackbarMessage(`Activity Subgroup '${apiSubgroupName}' (${subgroup_uid}) is in status '${status}'. Activities can only be connected to Activity Subgroups in 'Final' status.`)
})

Then('Validation error for {string} group is displayed', (status) => {
    cy.checkSnackbarMessage(`Activity Group '${apiGroupName}' (${group_uid}) is in status '${status}'. Activities can only be connected to Activity Groups in 'Final' status.`)
})

Then('The user adds already existing synonym', () => cy.fillInputNew('activityform-synonyms-field', synonym))

Given('Custom group name is typed in activity form', () => cy.get('[data-cy="activityform-activity-group-dropdown"] input').type(apiGroupName))

Given('Custom subgroup name is typed in activity form', () => cy.get('[data-cy="activityform-activity-subgroup-dropdown"] input').type(apiSubgroupName))

When('Not Final group or subgroup is not available during activity creation', () => cy.checkNoDataAvailable())

Then('The user is not able to save activity with already existing synonym and error message is displayed', () => {
    cy.get('div[data-cy="form-body"]').should('be.visible');
    cy.get('.v-alert').should('be.visible').should('contain.text', 'Following Activities already have the provided synonyms');
})

When('Open the activity overview page', () => {
    cy.get('tbody.v-data-table__tbody').contains('a', activityName).click({ force: true });
});

Then('The newly added activity is visible in the table', () => {
    cy.checkRowByIndex(0, 'Activity name', activityName)
    cy.checkRowByIndex(0, 'Sentence case name', activityName.toLowerCase())
    cy.checkRowByIndex(0, 'Synonyms', synonym)
    cy.checkRowByIndex(0, 'NCI Concept ID', nciconceptid)
    cy.checkRowByIndex(0, 'NCI Concept Name', nciconceptname)
    cy.checkRowByIndex(0, 'Abbreviation', abbreviation)
    cy.checkRowByIndex(0, 'Data collection', "Yes")
})

Then('The user is not able to save the acitivity', () => {
    cy.get('div[data-cy="form-body"]').should('be.visible');
    cy.get('span.dialog-title').should('be.visible').should('have.text', 'Add activity');
})

Then('The validation message appears for activity group', () => cy.checkIfValidationAppears('activityform-activity-group-class'))

Then('The validation message appears for activity name', () => cy.checkIfValidationAppears('activityform-activity-name-class'))

Then('The validation message appears for activity subgroup', () => cy.checkIfValidationAppears('activityform-activity-subgroup-class'))

Then('The validation message appears for sentance case name that it is not identical to name', () => cy.checkIfValidationAppears('sentence-case-name-class', 'Sentence case name can only differ in case compared to name value'))

When('Select value for Activity group field', () => cy.selectFirstVSelect('activityform-activity-group-dropdown'))

When('Select value for Activity subgroup field', () => cy.selectFirstVSelect('activityform-activity-subgroup-dropdown'))

Then('The default value for Data collection must be checked', () => {
    cy.get('[data-cy="activityform-datacollection-checkbox"]').within(() => {
        cy.get('.mdi-checkbox-marked').should('exist');
    })
})

When('The user enters a value for Activity name', () => cy.fillInput('activityform-activity-name-field', "TEST"))

When('The user enters unique value for Activity name', () => cy.fillInput('activityform-activity-name-field', getShortUniqueId()))

Then('The field for Sentence case name will be defaulted to the lower case value of the Activity name', () => {
    cy.get('[data-cy$="activity-name-field"] input').then(($input) => {
        cy.get('[data-cy="sentence-case-name-field"] input').should('have.value', $input.val().toLowerCase())
    })
})

When('The user define a value for Sentence case name and it is not identical to the value of Activity name', () => {
    cy.fillInput('activityform-activity-name-field', "TEST")
    cy.fillInput('sentence-case-name-field', "TEST2")
})

When('The activity name is updated', () => editActivityName())

Then('User intercepts request for activity creation', () => cy.intercept('POST', '/api/concepts/activities/activities').as('getData'))

Then('User waits for activity creation request to finish', () => cy.wait('@getData', { timeout: 20000 }))

Then('[API] User gets data of activity with name {string}, group {string}, subgroup {string}', (name, group, subgroup) => cy.getActivityDataByName(name, group, subgroup))

Then('[API] Activity name is fetched and assigned to variable', () => cy.getActivityNameByUid().then(name => activityName = name))

Then('[API] Group and subgroup are created and approved to be used for activity creation', () => createAndApproveGroupAndSubgroup())

Then('[API] Activity with data collection set to {int} and {string} included in the name is created and approved', (isDataCollected, partialName) => {
    isDataCollected ? cy.createActivity(generateShortUniqueName(partialName)) : cy.createActivity(generateShortUniqueName(partialName), false)
    cy.approveActivity()
})

When('[API] Activity in status Final with Final group and subgroub exists', () => {
    if (!activityName) createActivityViaApi(true)
})

Then('[API] Study Activity is created and group is drafted', () => {
    createAndChangeStatusOfLinkedItemViaApi(() => cy.groupNewVersion())
})

Then('[API] Study Activity is created and group is inactivated', () => {
    createAndChangeStatusOfLinkedItemViaApi(() => cy.inactivateGroup())
})

Then('[API] Study Activity is created and subgroup is drafted', () => {
    createAndChangeStatusOfLinkedItemViaApi(() => cy.subGroupNewVersion())
})

Then('[API] Study Activity is created and subgroup is inactivated', () => {
    createAndChangeStatusOfLinkedItemViaApi(() => cy.inactivateSubGroup())
})

Then('[API] Study Activity is created and approved', () => createActivityViaApi(true))

Then('[API] No data collection Study Activity is created and approved', () => createActivityViaApi(true, false))

Then('[API] Study Activity with no mutliple instances allowed is created and approved', () => createActivityViaApi(true, true, false))

Then('[API] Study Activity is created and not approved', () => createActivityViaApi(false))

Then('[API] Study Activity is created', () => getGroupAndSubgroupAndCreateActivity())

When('[API] Activity in status Draft exists', () => createActivityViaApiSimplified())

When('[API] Activity is approved', () => cy.approveActivity())

When('[API] Activity is inactivated', () => cy.inactivateActivity())

When('[API] Activity is reactivated', () => cy.reactivateActivity())

When('[API] Activity new version is created', () => cy.activityNewVersion())

Given('[API] First activity for search test is created', () => createActivityViaApiSimplified(`SearchTest${getShortUniqueId()}`))

Given('[API] Second activity for search test is created', () => cy.createActivity(`SearchTest${getShortUniqueId()}`))

When('[API] Activity is created', () => cy.createActivity())

When('[API] Unsubmitted requested Activity is archived', () => cy.archiveRequestedActivity())

When('The user opens version history of activity subgroup', () => {
    cy.intercept('**versions').as('version_history_data')
    cy.tableRowActions(0, 'History')
})

Then('The version history displays correct data for activity subgroup', () => {
    cy.wait('@version_history_data').then((req) => {
        let data = req.response.body[0]
        cy.getCellValue(0, 'Activity subgroup', data.name)
        cy.getCellValue(0, 'Sentence case name', data.name_sentence_case)
        cy.getCellValue(0, 'Status', data.status)
        cy.getCellValue(0, 'Version', data.version)
        cy.getCellValue(0, 'User', data.author_username)
    })
})

When('The Multiple instance allowed checkbox is set to {string}', (value) => {
    cy.get('[data-cy="activityform-multipleselection-checkbox"] input').then(el => {
    value == 'true' ? cy.wrap(el).check( {force: true} ) : cy.wrap(el).uncheck()
    })
});

Then('The Multiple instance allowed field is set to {string}', (expected) => {
    cy.get('.summary-label').contains('Multiple instances allowed')
      .parent()
      .find('.summary-value')
      .should('have.text', expected);
});

When('The current activity group is edited', () => {
    cy.fillInput('groupform-activity-group-field', `NewName ${getShortUniqueId()}`)
    cy.fillInput('groupform-change-description-field', 'DefChange Desc')
})

Then('The activity subgroups previously linked to that group remain linked', () => {
    cy.tableContains(apiSubgroupName)
})

When('The current activity subgroup is edited', () => {
    cy.fillInput('groupform-activity-group-field', `NewName ${getShortUniqueId()}`)
    cy.fillInput('groupform-change-description-field', 'DefChange Desc')
    cy.fillInput('groupform-definition-field', 'Def')
})

Then('The activity groups previously linked to that subgroup remain linked', () => cy.tableContains(apiGroupName))

When('User edits activity group to {string}', (activityGroupName) => selectCustomGrouping('group', activityGroupName))

When('User edits activity subgroup to {string}', (activitySubgroupName) => selectCustomGrouping('subgroup', activitySubgroupName))

When('User selects first activity group', () => cy.selectFirstVSelect(`activityform-activity-group-dropdown`))

When('User selects first activity subgroup', () => cy.selectFirstVSelect('activityform-activity-subgroup-dropdown'))

When('User sets activity name', () => cy.fillInput('activityform-activity-name-field', activityName = `Activity${getShortUniqueId()}`))

When('User fills in activity optional data', () => {
    cy.fillInputNew('activityform-synonyms-field', synonym = `Synonym${getShortUniqueId()}`)
    cy.fillInput('activityform-nci-concept-id-field', nciconceptid)
    cy.fillInput('activityform-nci-concept-name-field', nciconceptname)
    cy.fillInput('activityform-abbreviation-field', abbreviation)
    cy.fillInput('activityform-definition-field', definition)
})

function selectCustomGrouping(grouping, value) {
    cy.get(`[data-cy="activityform-activity-${grouping}-dropdown"] input`).clear().type(value)
    cy.selectFirstVSelect(`activityform-activity-${grouping}-dropdown`)
}

function editActivityName() {
    cy.wait(1000)
    cy.get('[data-cy="activityform-activity-name-class"] input').should('have.attr', 'value')
    cy.get('[data-cy="activityform-activity-name-field"] input').invoke('val').then(value => {
        cy.fillInput('activityform-activity-name-field', activityName = `Update ${value}`)
    })
}

function createAndApproveGroupAndSubgroup() {
    createAndApproveViaApi(() => cy.createGroup(), () => cy.approveGroup())
    createAndApproveViaApi(() => cy.createSubGroup(), () => cy.approveSubGroup())
}

function createActivityViaApi(approve, isDataCollected = true, isMultipleSelectionAllowed = true) {
    createAndApproveGroupAndSubgroup()
    approve ? createAndApproveViaApi(() => cy.createActivity('', isDataCollected, isMultipleSelectionAllowed), () => cy.approveActivity()) : cy.createActivity('', isDataCollected, isMultipleSelectionAllowed)
    cy.getActivityNameByUid().then(name => activityName = name)
}

function createActivityViaApiSimplified(customName = '') {
    getGroupAndSubgroupAndCreateActivity(customName)
    cy.getActivityNameByUid().then(name => activityName = name)
    cy.getActivitySynonymByUid().then(apiSynonym => synonym = apiSynonym)
}

function getGroupAndSubgroupAndCreateActivity(customName) {
    cy.getFinalGroupUid()
    cy.getFinalSubGroupUid()
    cy.createActivity(customName)
}

function createAndChangeStatusOfLinkedItemViaApi(action) {
    createActivityViaApi(true)
    action()
}

function createAndApproveViaApi(createFunction, approveFunction) {
    createFunction()
    approveFunction()
}