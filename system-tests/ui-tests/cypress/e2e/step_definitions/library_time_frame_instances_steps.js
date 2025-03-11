const {
    Given,
    When,
    Then,
  } = require("@badeball/cypress-cucumber-preprocessor");
  
  Given("The test timeframe instance exists in the table", () => {
    cy.get("table tbody tr").should("exist");
  });
  
  Then("The History for timeframe window is displayed", () => {
    cy.get(`[data-cy="version-history-window"]`).should("exist");
  });
  
  Then(
    "The {string} option is not available for the timeframe instance",
    (option) => {
      cy.get(".v-list-item__content").should("not.contain", option);
      cy.get(".v-list-item__content").should("contain", "History"); //To make sure it is searching in the correct place
    }
  );
  
  Then("The List of studies with a specific timeframe window is displayed", () => {
    cy.get(".dialog-title").should(
      "contain",
      "List of studies with a specific timeframe"
    );
  });
  
  Then(
    "The {string} option is not available for the Timeframe instance",
    (option) => {
      cy.get(".v-list-item__content").should("not.contain", option);
      cy.get(".v-list-item__content").should("contain", "History"); //To make sure it is searching in the correct place
    }
  );
  
  Then("The History for Timeframe window is displayed", () => {
    cy.get(`[data-cy="version-history-window"]`).should("exist");
  });
  
  Then("The List of studies with a specific Timeframe window is displayed", () => {
    cy.get(".dialog-title").should(
      "contain",
      "List of studies with a specific timeframe"
    );
  });
  