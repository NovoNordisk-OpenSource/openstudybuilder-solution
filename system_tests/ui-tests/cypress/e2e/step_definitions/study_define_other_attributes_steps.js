const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getCurrStudyUid } = require("../../support/helper_functions");

When("The Other Study Attributes edit form is opened", () => {
    cy.get('[data-cy="add-other-study-attributes-button"]').click();
    cy.get('[data-cy="form-body"]').should("be.visible");
});

Then("The required and optional study attribute sections are visible", () => {
    cy.get('[data-cy="form-body"]')
        .should("contain", "Required Attributes")
        .and("contain", "Optional Attributes");
});

Given("[API] All Other Study Attributes assigned to the selected study are deleted", () => {
    cy.deleteAllOtherStudyAttributes(getCurrStudyUid());
});

When("The Other Study Attributes edit form is closed", () => {
    cy.get('[data-cy="form-body"] button[data-cy="cancel-button"]').last().click();
});

When("User waits for Other Study Attributes table to refresh", () => cy.wait(1000));

When("User removes the first optional Other Study Attribute", () => {
    cy.get('[data-cy="form-body"] .other-study-attribute-panel')
    .eq(1)
        .find(".remove-btn")
        .click();
});

When("User selects the first required Other Study Attribute parameter", () => {
    cy.get('[data-cy="other-attr-required-parameter-0"]').click();
    cy.get('.v-overlay__content:visible .v-list-item').first().click();
});

When("User selects the first optional Other Study Attribute parameter", () => {
    cy.get('[data-cy="form-body"] .other-study-attribute-panel')
        .eq(1)
        .find('.table-cell--parameter .v-field__input')
        .click();
    cy.get('.v-overlay__content:visible .v-list-item').first().click();
});

When("User selects the first required Other Study Attribute null flavor", () => {
    cy.get('[data-cy="form-body"] .other-study-attribute-panel')
        .first()
        .find('.table-cell--field')
        .contains('Null flavor')
        .parent()
        .find('.v-field__input')
        .click();
    cy.get('.v-overlay__content:visible .v-list-item').first().click();
});

When("User edits the first required Other Study Attribute value", () => {
    cy.get('[data-cy="form-body"] .other-study-attribute-panel')
        .first()
        .contains('.table-cell', 'Parameter value')
        .find('input[type="text"]')
        .filter(":visible")
        .clear()
        .type("Updated from Cypress");
});

Then("The first required Other Study Attribute value is disabled and empty", () => {
    cy.get('[data-cy="form-body"] .other-study-attribute-panel')
        .first()
        .contains('.table-cell', 'Parameter value')
        .find('input')
        .should('be.disabled')
        .and('have.value', '');
});

When("User edits the first editable Other Study Attribute value", () => {
    cy.contains(".table-cell", "Parameter value")
        .find('input[type="text"]')
        .filter(":visible")
        .clear()
        .type("Updated from Cypress");
});

When("User intercepts the Other Study Attributes update request", () => {
    cy.intercept("POST", "**/study-other-attributes/batch").as("otherAttributesUpdate");
});

When("User waits for the Other Study Attributes update request", () => cy.wait("@otherAttributesUpdate"));

When("User intercepts the Other Study Attributes delete request", () => {
    cy.intercept("POST", "**/study-other-attributes/batch").as("otherAttributesDelete");
});

When("User waits for the Other Study Attributes delete request", () => cy.wait("@otherAttributesDelete"));

Then("The Other Study Attributes update request contains a POST operation", () => {
    cy.get("@otherAttributesUpdate").then(({ request }) => {
        const postOperation = request.body.find((operation) => operation.method === "POST");
        expect(postOperation).to.exist;
    });
});

Then("The required and optional parameter validations are displayed", () => {
    cy.get('[data-cy="form-body"]')
        .find('.v-messages__message')
        .should('have.length.at.least', 2)
        .and('contain', 'This field is required');
});

Then("The Other Study Attributes update request was not sent", () => {
    cy.get('@otherAttributesUpdate.all').should('have.length', 0);
});

Then("The Other Study Attributes update request contains a null flavor operation", () => {
    cy.get('@otherAttributesUpdate').then(({ request }) => {
        const nullFlavorOperation = request.body.find(
            (operation) => operation.content?.null_flavor_term_uid
        );
        expect(nullFlavorOperation).to.exist;
    });
});

Then("The Other Study Attributes update request contains PATCH and DELETE operations", () => {
    cy.get('@otherAttributesUpdate').then(({ request }) => {
        expect(request.body.find((operation) => operation.method === 'PATCH')).to.exist;
        expect(request.body.find((operation) => operation.method === 'DELETE')).to.exist;
    });
});

Then("The Other Study Attributes delete request contains a DELETE operation", () => {
    cy.get("@otherAttributesDelete").then(({ request }) => {
        const deleteOperation = request.body.find((operation) => operation.method === "DELETE");
        expect(deleteOperation).to.exist;
    });
});
