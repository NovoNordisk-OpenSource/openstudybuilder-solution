const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

Given("the administration annoucement page is initialized", () => {
  // Toggle off the announcement option
  toggleOnOff(false)
});

Given("Toggle on announcement and verify visibility", () => {
  toggleOnOff(true)
}); 

When("the user chooses the type of announcement as Informative", () => {
    cy.get('body').click()
    cy.get('.mr-2 input[value="information"]').check()
  });

When("the user chooses the type of announcement as Warning", () => {
    cy.get('body').click()
    cy.get('.mr-2 input[value="warning"]').check()
  });

When("the user chooses the type of announcement as Error", () => {
    cy.get('body').click()
    cy.get('.mr-2 input[value="error"]').check()
  });

Then("the preview box at the bottom should change color to blue", () => {
  cy.get('.v-card-text .v-alert').should('have.class', 'bg-nnLightBlue200')
  });

Then("the preview box at the bottom should change color to yellow", () => {
  cy.get('.v-card-text .v-alert').should('have.css', 'background-color', 'rgb(250, 238, 204)')
  });

Then("the preview box at the bottom should change color to red", () => {
  cy.get('.v-card-text .v-alert').should('have.css', 'background-color', 'rgb(250, 221, 216)')
  });

When("the user fills in the announcement title", () => {
    cy.get('div.page-subtitle').contains('Announcement content').next().find('input').clear().type('TEST')
  });

When("the user fills in the announcement description", () => {
    cy.get('div.page-subtitle').contains('Announcement content').next().next().find('.v-field__input').clear().type('TEST DESCRIPTION')
  });
  
When("the user presses SAVE CHANGES", () => {
  saveAndReload()
 });

When("navigates to any other page in StudyBuilder", () => {
    cy.visit('/administration/announcements')
    cy.waitForPage()
    cy.get('body').click()
  });

When("presses CTRL-R to reload the page", () => {
    cy.get('body').type('{ctrl}r')
  });

Then("the announcement box should be shown", () => {
    cy.waitForPage ()
    cy.get('.v-alert').should('contain', 'TEST')
    cy.get('.v-alert').should('contain', 'TEST DESCRIPTION')  
  });

When("the user removes the notification window by clicking on the cross in the right side", () => {
  cy.get('div.v-alert__close button[aria-label="Close"]').click()
  });

Then("the notification should not reappear", () => {
    cy.get('.v-alert').should('not.exist') 
  });

  When("the user toggles Show announcement off", () => {
    toggleOnOff(false)
  });

function toggleOnOff(on) {
    cy.wait(1000)
    cy.get('.mr-6 .v-selection-control input').then(($toggle) => {
      on ? cy.wrap($toggle).check() : cy.wrap($toggle).uncheck()
    })
    saveAndReload()
  }

function saveAndReload() {
    cy.get('button.v-btn').contains('Save changes').click()
    cy.get('button.v-btn--loading').should('not.exist')
    cy.get('body').type('{ctrl}r')
  }




