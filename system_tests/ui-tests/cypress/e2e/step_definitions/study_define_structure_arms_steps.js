import { armLabel } from "./study_define_structure_wizard_steps";

const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getCurrStudyUid, generateShortUniqueName } = require("../../support/helper_functions");

Given('[API] Uid of study type {string} is fetched', (studyType) => cy.getArmTypeUid(studyType))

Given('[API] The Study Arm exists within selected study', () => cy.createTestArm(getCurrStudyUid()))

Given('[API] The Study Arm with name {string} exists within selected study', (customName) => cy.createTestArm(getCurrStudyUid(), customName))

Given('[API] Get all Study Arms within selected study', () => cy.getArmsUids(getCurrStudyUid()))

Given('[API] Delete all Study Arms within selected study', () => cy.deleteArms(getCurrStudyUid()))

Then('The study arm {int} with type {string} data is available in the table, including number of participants {int} and connected branches {int}', (index, type, participants, connectedBranches) => {
    checkArmData(type, `Test Arm ${index}`, `Arm ${index}`, `RG${index}`, `AC${index}`, `Arm desc ${index}`, connectedBranches, participants)
})

Then('The new study arm data is available in the table', () => checkArmData('Placebo Arm', 'Test Arm 1', 'Arm 1', 'RG1', 'AC1', 'Arm desc 1'))

Then('The new study arm data is updated in the table', () => checkArmData('Placebo Arm', 'Test Arm 1 Update', 'Arm 1 Update', 'RG1U', 'AC1U', 'Arm desc 1 Update'))

When('The study arm label value is visible in the table', () => cy.checkRowByIndex(0, 'Arm label', armLabel))

When('The study arm label value is empty', () => cy.checkRowByIndex(0, 'Arm label', ''))

function checkArmData(type, name, shortName, randomGroup, randomCode, description, connectedBranches = '', participants = '') {
    cy.checkRowByIndex(0, 'Type', type)
    cy.checkRowByIndex(0, 'Arm name', name)
    cy.checkRowByIndex(0, 'Arm short name', shortName)
    cy.checkRowByIndex(0, 'Random. group', randomGroup)
    cy.checkRowByIndex(0, 'Random. code', randomCode)
    cy.checkRowByIndex(0, 'Description', description)
    if (connectedBranches) {
        cy.checkRowByIndex(0, 'Connected Branches', connectedBranches)
        cy.checkRowByIndex(0, 'No. of participants', participants)
    }
}