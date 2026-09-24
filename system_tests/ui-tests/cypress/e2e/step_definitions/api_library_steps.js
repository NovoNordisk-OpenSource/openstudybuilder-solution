const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

export let apiGroupName, apiSubgroupName, apiActivityName, apiInstanceName

When('Group name created through API is found', () => cy.getGroupNameByUid().then(text => apiGroupName = text))

When('Subgroup name created through API is found', () => cy.getSubGroupNameByUid().then(text => apiSubgroupName = text))

When('Activity name created through API is found', () => cy.getActivityNameByUid().then(text => apiActivityName = text))

When('Instance name created through API is found', () => cy.getActivityInstanceNameByUid().then(text => apiInstanceName = text))
