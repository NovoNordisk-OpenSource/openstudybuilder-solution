const {
  Given,
  When,
  Then,
} = require("@badeball/cypress-cucumber-preprocessor");

Given("The test endpoint instance exists in the table", () => {
  cy.get("table tbody tr").should("exist");
});

Then("The History for endpoint window is displayed", () => {
  cy.get(`[data-cy="version-history-window"]`).should("exist");
});

Then(
  "The {string} option is not available for the endpoint instance",
  (option) => {
    cy.get(".v-list-item__content").should("not.contain", option);
    cy.get(".v-list-item__content").should("contain", "History"); //To make sure it is searching in the correct place
  }
);

Then("The List of studies with a specific endpoint window is displayed", () => {
  cy.get(".dialog-title").should(
    "contain",
    "List of studies with a specific endpoint"
  );
});

Then(
  "The {string} option is not available for the Endpoint instance",
  (option) => {
    cy.get(".v-list-item__content").should("not.contain", option);
    cy.get(".v-list-item__content").should("contain", "History"); //To make sure it is searching in the correct place
  }
);

Then("The History for Endpoint window is displayed", () => {
  cy.get(`[data-cy="version-history-window"]`).should("exist");
});

Then("The List of studies with a specific Endpoint window is displayed", () => {
  cy.get(".dialog-title").should(
    "contain",
    "List of studies with a specific endpoint"
  );
});
