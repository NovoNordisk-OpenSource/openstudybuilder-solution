const { When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let therapeuticArea = 'Nonalcoholic', studyDiseaseConditionOrIndication = 'Nonalcoholic', durationUnit = 'days', stableDiseaseMinDuration = '10'
let diagnosisGroup = 'Nonalcoholic steatohepatitis', relapseCriteria = 'Test relapse criteria', healthySubjectIndicator= 'No'
let rareDiseaseIndicator = 'No', sex = 'Female', minParticipantAge = '18', maxParticipantAge = '99'
let paediatricStudyIndicator = 'No', paediatricInvestigationPlanIndicator = 'No', paediatricPostMarketStudyIndicator = 'No'

When('The population is edited', () => {
    cy.selectMultipleSelect('Therapeutic area', therapeuticArea)
    cy.selectMultipleSelect('Study disease, condition or indication', studyDiseaseConditionOrIndication)
    cy.setDuration('stable-disease-min-duration', stableDiseaseMinDuration, durationUnit)
    cy.selectMultipleSelect('Diagnosis group', diagnosisGroup)
    cy.fillInput('Relapse criteria', relapseCriteria)
    cy.selectRadioButton('Healthy subject indicator', healthySubjectIndicator)
    cy.selectRadioButton('Rare disease indicator', rareDiseaseIndicator)
    cy.selectAutoComplete('Sex of study participants', sex)
    cy.setDuration('planned-minimum-age', minParticipantAge, durationUnit)
    cy.setDuration('planned-maximum-age', maxParticipantAge, durationUnit)
    cy.selectRadioButton('Paediatric study indicator', paediatricStudyIndicator)
    cy.selectRadioButton('Paediatric investigation plan indicator', paediatricInvestigationPlanIndicator)
    cy.selectRadioButton('Paediatric post-market study indicator', paediatricPostMarketStudyIndicator)
})

Then('The population data is reflected in the table', () => {
    cy.tableContains(therapeuticArea)
    cy.tableContains(studyDiseaseConditionOrIndication)
    cy.tableContains(`${stableDiseaseMinDuration} ${durationUnit}`)
    cy.tableContains(healthySubjectIndicator)
    cy.tableContains(diagnosisGroup)
    cy.tableContains(relapseCriteria)
    cy.tableContains(rareDiseaseIndicator)
    cy.tableContains(sex)
    cy.tableContains(`${minParticipantAge} ${durationUnit}`)
    cy.tableContains(`${maxParticipantAge} ${durationUnit}`)
    cy.tableContains(paediatricStudyIndicator)
    cy.tableContains(paediatricInvestigationPlanIndicator)
    cy.tableContains(paediatricPostMarketStudyIndicator)
})