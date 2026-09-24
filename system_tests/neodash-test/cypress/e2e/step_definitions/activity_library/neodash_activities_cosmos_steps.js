const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Then('The Activity as COSMOS BC Concept displays the activity in a yaml format', () => {
  cy.get('input[value^="Activity as COSMOS BC Concept"]', { timeout: 20000 }).first()
    .parents('.react-grid-item').first()
    .find('textarea').first()
    .should(($ta) => {
      const text = ($ta.val() || '').trim()
      expect(text, 'Activity as COSMOS BC Concept returned no value (empty) - possible bug').to.not.equal('')
      expect(text, 'Activity as COSMOS BC Concept returned no data - possible bug').to.not.contain('Query returned no data')
    })
})

Then('The Activity as COSMOS SDTM datasetspecialization displays the activity in a yaml format', () => {
  cy.get('input[value^="Activity as COSMOS SDTM Dataset Specialization"]', { timeout: 20000 }).first()
    .parents('.react-grid-item').first()
    .find('textarea').first()
    .should(($ta) => {
      const text = ($ta.val() || '').trim()
      expect(text, 'Activity as COSMOS SDTM Dataset Specialization returned no value (empty) - possible bug').to.not.equal('')
      expect(text, 'Activity as COSMOS SDTM Dataset Specialization returned no data - possible bug').to.not.contain('Query returned no data')
    })
})

