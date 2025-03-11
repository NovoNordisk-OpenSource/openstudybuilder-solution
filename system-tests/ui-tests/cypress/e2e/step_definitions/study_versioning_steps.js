const {
  Given,
  When,
  Then,
} = require("@badeball/cypress-cucumber-preprocessor");

let imported_study_id_with_versions = "CDISC DEV-1111";

Given("The CDISC DEV-1111 study is selected", () => cy.selectStudyByStudyId(imported_study_id_with_versions));

Given(
  "The test study definition in status {string} and version {string} is selected", (status, version) => {
    cy.selectStudyByIdVersionAndStatus(
      imported_study_id_with_versions,
      parseFloat(version),
      status
    );
  }
);

Given("The test study definition in status Released and version 1.1 is selected", () => cy.tableRowActions(1, 'Select'));

Given("The test study definition in status Locked and version 1 is selected", () => cy.tableRowActions(2, 'Select'));

When("The {string} for {string} is selected", (page, value) => {
  cy.visitStudyPageForStudyId(imported_study_id_with_versions, page);
});

When("The Study Status page in Manage Study is accessed", () => cy.visitStudyPageForStudyId(imported_study_id_with_versions, 'study_status/study_status'))

Then("The {string} is displayed", (value) => {
  cy.get("body").should("contain", value);
});
