const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getCurrStudyUid } = require("../../support/helper_functions");

When('User clicks add other study attributes button', () => cy.get('[data-cy="add-other-study-attributes-button"]').click())

Then("The required and optional study attribute sections are visible", () => {
    cy.get('[data-cy="form-body"]').should("contain", "Required Attributes").and("contain", "Optional Attributes")
})

Given("[API] All Other Study Attributes assigned to the selected study are deleted", () => {
    cy.deleteAllOtherStudyAttributes(getCurrStudyUid());
});

When("The Other Study Attributes edit form is closed", () => {
    cy.get('[data-cy="form-body"] button[data-cy="cancel-button"]').last().click();
});

When("User removes the first optional Other Study Attribute", () => {
    cy.get('[data-cy="form-body"] .other-study-attribute-panel').eq(1).find(".remove-btn").click()
})

When("User selects the first required Other Study Attribute parameter", () => selectAttributeValue('required'))

When("User selects the first optional Other Study Attribute parameter", () => selectAttributeValue('optional'))

When("User selects the first optional Other Study Attribute null flavor", () => {
    cy.get('[data-cy="form-body"] .other-study-attribute-panel').eq(1)
        .find('.table-cell--field').contains('Null flavor')
            .parent().find('.v-field__input').click();
    cy.get('.v-overlay__content:visible .v-list-item').first().click();
});

When("User edits the first optional Other Study Attribute value", () => {
    cy.get('[data-cy="form-body"] .other-study-attribute-panel').eq(1)
        .contains('.table-cell', 'Parameter value').find('input[type="text"]').filter(":visible")
            .clear().type("Updated from Cypress");
});

Then("The first optional Other Study Attribute value is disabled and empty", () => {
    cy.get('[data-cy="form-body"] .other-study-attribute-panel').eq(1)
        .contains('.table-cell', 'Parameter value').find('input').should('be.disabled').and('have.value', '');
});

When("User intercepts the Other Study Attributes POST request", () => {
    cy.intercept("POST", "**/study-other-attributes/batch").as("otherAttributesUpdate")
});

When("User waits for the Other Study Attributes POST request", () => cy.wait("@otherAttributesUpdate"));

Then("The Other Study Attributes update request contains {string} operations", (value) => {
    cy.get('@otherAttributesUpdate').then(({ request }) => {
        expect(request.body.find(operation => operation.method === value)).to.exist
    })
})

Then("The required and optional parameter validations are displayed", () => {
    cy.get('[data-cy="form-body"]').find('.v-messages__message')
        .should('have.length.at.least', 2).and('contain', 'This field is required');
});

Then("The Other Study Attributes update request was not sent", () => {
    cy.get('@otherAttributesUpdate.all').should('have.length', 0);
});

Then("The Other Study Attributes update request contains a null flavor operation", () => {
    cy.get('@otherAttributesUpdate').then(({ request }) => {
        const nullFlavorOperation = request.body.find(operation => operation.content?.null_flavor_term_uid)
        expect(nullFlavorOperation).to.exist;
    })
})

function selectAttributeValue(type) {
    cy.get(`[data-cy="other-attr-${type}-parameter-0"]`).click()
    cy.get('.v-overlay__content:visible .v-list-item').first().click()
}