const {
  Given,
  When,
  Then,
} = require("@badeball/cypress-cucumber-preprocessor");
const {
  getCurrStudyUid,
  getShortUniqueId,
} = require("../../support/helper_functions");

let sdpGroupId, sdpName, sdpDefinition;
const updatedSdpName = "Updated E2E Test Population";

Given("[API] The test Study Design Population exists", () =>
  cy.checkAndCreateStudyDesignPopulation(),
);

Given("[API] Delete all Study Design Populations within selected study", () =>
  cy.deleteStudyDesignPopulations(getCurrStudyUid()),
);

When("Add study design population button is clicked", () =>
  cy.clickButton("add-study-design-population"),
);

When("The study design population form is filled", () => {
  sdpGroupId = `GRP${getShortUniqueId()}`;
  sdpName = `SDP ${getShortUniqueId()}`;
  sdpDefinition = "E2E Test Population Definition";
  cy.fillInput("sdp-group-id", sdpGroupId);
  cy.fillInput("sdp-name", sdpName);
  cy.fillInput("sdp-definition", sdpDefinition);
});

Then("The new Study Design Population is visible within the table", () => {
  cy.tableContains(sdpGroupId);
  cy.tableContains(sdpName);
  cy.tableContains(sdpDefinition);
});

When("The Study Design Population is edited", () => {
  cy.fillInput("sdp-name", updatedSdpName);
});

Then("The updated Study Design Population is visible within the table", () => {
  cy.tableContains(updatedSdpName);
});

Then("The test Study Design Population is no longer available", () => {
  cy.searchAndCheckPresence(updatedSdpName, false);
});

Given("[API] A Study Design Population with a known Group ID exists", () =>
  cy.createStudyDesignPopulationWithGroupId(getCurrStudyUid()),
);

Given("[API] An inclusion criterion is selected into the study", () =>
  cy.selectStudyCriteriaFromTemplate(getCurrStudyUid()),
);

Given("The criteria table edit mode is activated", () =>
  cy.get('[data-cy="edit-study-criteria-in-table"]').click(),
);

When("The Study Design Population is linked to the criterion", () => {
  cy.intercept("PATCH", "**/study-criteria/**/study-design-populations").as(
    "linkPopulation",
  );
  cy.get('[data-cy="criteria-population-select"]')
    .first()
    .find(".v-field__input")
    .click();
  cy.get(".v-overlay__content .v-list", { timeout: 20000 })
    .filter(":visible")
    .contains(".v-list-item", Cypress.env("TEST_SDP_GROUP_ID"))
    .click();
  cy.get("body").type("{esc}");
  cy.wait("@linkPopulation").its("response.statusCode").should("eq", 200);
});

Then(
  "The linked Study Design Population Group ID is visible on the criterion row",
  () => cy.tableContains(Cypress.env("TEST_SDP_GROUP_ID")),
);

When("The Study Design Population is unlinked from the criterion", () => {
  cy.intercept("PATCH", "**/study-criteria/**/study-design-populations").as(
    "unlinkPopulation",
  );
  cy.get('[data-cy="criteria-population-select"]')
    .first()
    .find(".v-chip__close")
    .first()
    .click();
  cy.wait("@unlinkPopulation").its("response.statusCode").should("eq", 200);
});

Then(
  "The Study Design Population Group ID is no longer visible on the criterion row",
  () =>
    cy
      .get('[data-cy="criteria-population-select"]')
      .first()
      .should("not.contain", Cypress.env("TEST_SDP_GROUP_ID")),
);
