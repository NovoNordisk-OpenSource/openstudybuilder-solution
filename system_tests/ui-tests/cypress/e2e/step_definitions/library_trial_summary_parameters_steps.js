const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getCurrStudyUid, getShortUniqueId } = require("../../support/helper_functions");

let createdTermName;
let createdTermCode;

Given('[API] Trial Summary Parameter is created', () => {
    cy.createTrialSummaryParameter(createdTermName = `E2E test ${getShortUniqueId()}`, createdTermCode = `Submission Code ${getShortUniqueId()}`, `Submission Name ${getShortUniqueId()}`, 'def')
})

When('Trial summary parameter details page is opened', () => cy.contains('[data-cy="term-sponsor-values-card"]', 'Term sponsor values').should('be.visible'))

When("The sponsor values edit button is clicked", () => cy.clickButton("edit-sponsor-values"))

When("The attributes values edit button is clicked", () => cy.clickButton("edit-attributes-values"))

When('User intercepts term attributes versions history', () => cy.intercept("GET", "**/api/ct/terms/*/attributes/versions*").as("versionHistory"))

When('User intercepts term name versions history', () => cy.intercept("GET", "**/api/ct/terms/*/names/versions*").as("versionHistory"))

When("The CT values history button is clicked", () => cy.clickButton("term-attributes-version-history"))

When("The sponsor values history button is clicked", () => cy.clickButton("term-sponsor-version-history"))

When("The edit order button is clicked from the CT term codelists context table row", () => {
    cy.get('[data-cy="codelists-context-card"] [data-cy="edit-codelist-item"]').first().click()
})

When("The order and submission value are updated", () => {
    cy.get('[data-cy="term-submission-value"] input').clear({ force: true }).type("E2E_CODE_UPDATED");
    cy.get('[data-cy="term-order"] input').clear({ force: true }).type("2");
});

Then("The updated values are shown in the 'CT term codelists context' table", () => {
    cy.get('[data-cy="codelists-context-table"]').should("contain", "E2E_CODE_UPDATED").and("contain", "2");
});

Then("The following actions are available", (dataTable) => {
    dataTable.rows().forEach(action => cy.get(`[data-cy="${action[0]}"]`).should("be.visible"))
})

Then("The version history window is displayed", () => cy.get('[data-cy="version-history-window"]').should("be.visible"))

Then("The history contains timestamps and usernames", () => {
    cy.wait("@versionHistory").then(({ response }) => {
        expect(response?.body).to.be.an("array").and.not.be.empty;
        response.body.forEach((version, index) => {
            expect(version.start_date, `version ${index} start_date`).to.be.ok;
            expect(version.author_username, `version ${index} author_username`).to.be.ok;
        });

        cy.get('[data-cy="version-history-window"]')
            .should("be.visible")
            .find('[data-cy="data-table"]')
            .should("be.visible")
            .within(() => {
                response.body.forEach((version) => {
                    cy.contains("td", version.author_username).should("be.visible");
                    cy.get("tbody tr").should("contain", formatHistoryDate(version.start_date));
                });
            });
    });
});

Then("The page header shows the CT term name with {string} and {string}", (libraryLabel, conceptIdLabel) => {
    cy.get('[data-cy="page-title"]').should("be.visible")
    cy.get('[data-cy="header-card"]').should("contain", libraryLabel).and("contain", conceptIdLabel)
})

Then("The {string} section is visible with the following fields", (locator, dataTable) => {
    cy.get(`[data-cy="${locator}-values-card"]`).within(() => {
        dataTable.rows().forEach((field) => cy.contains('td', field[0]).should("be.visible"))
    })
})

Then("The {string} table is visible with the following headers", (sectionName, dataTable) => {
    cy.get(`[data-cy="${sectionName}"]`).within(() => {
        dataTable.rows().forEach(header => cy.get('thead').should("contain", header[0]))
    })
})

Then("The codelist context table is visible", () => cy.get('[data-cy="codelists-context-table"]').should("be.visible"))

When("The Term sponsor values are edited", () => cy.fillInput("ts-param-notes", "E2E Trial Summary Parameter update"))

Then("The updated sponsor values are shown in the overview page", () => {
    cy.get('[data-cy="notes"]').should("contain", "E2E Trial Summary Parameter update");
});

Then("The updated attributes values are shown in the overview page", () => {
    cy.get('[data-cy="definition"]').should("contain", "E2E Trial Summary Parameter definition update");
});

Then("The form displays a validation error for the Sponsor name", () => assertRequiredField("ts-param-sponsor-name"))

Then("The form displays a validation error for the submission name", () => assertRequiredField("ts-param-test-name-submission-value"))

Then("The form displays a validation error for the Code", () => assertRequiredField("ts-param-submission-value"))

Then("The form displays a validation error for the Required level", () => assertRequiredField("ts-param-required-level"))

Then("The osb field name has value {string}", (value) => cy.get('[data-cy="osb-field-name"]').should("contain", value))

Then('User clicks approve term sponsor values', () => cy.clickButton("approve-term-sponsor-values"))

Then('User clicks approve term attributes values', () => cy.clickButton("approve-term-attributes-values"))

Then('User selects created term as optional parameter', () => cy.selectVSelect("other-attr-optional-parameter-0", createdTermName))

Then('User selects null flavor as {string}', (value) => cy.selectVSelect('other-attr-optional-null-flavor-0', value))

Then('User removes required other study attribute', () => cy.get('[data-cy="other-attr-required-remove-0"]').click())

Then("The new Trial Summary Parameter is visible in the table", () => cy.searchAndCheckPresence(createdTermCode, true))

Then("The name status is set to {string}", (status) => {
    cy.get('[data-cy="data-table"] tbody tr').contains(createdTermName)
        .closest('tr').should("contain", status);
});

Then("The attributes status is set to {string}", (status) => {
    cy.get('[data-cy="data-table"] tbody tr').contains(createdTermName)
        .closest('tr').should("contain", status);
});

When('User fills trial summary parameter order as {string}', (value) => cy.fillInput("ts-param-order", value))

When('User fills trial summary parameter defintion as {string}', (value) => cy.fillInput("ts-param-definition", value))

When('User fills trial summary parameter sponsor name with random, unique value', () => cy.fillInput("ts-param-sponsor-name",  createdTermName = `E2E TS Param ${getShortUniqueId()}`))

When('User fills trial summary parameter sponsor name with already used value', () => {
    cy.getCellValueNoVisibilityCheck(0, 'Sponsor name').then(existingName => cy.fillInput("ts-param-sponsor-name",  existingName))
})

When('User fills trial summary parameter submission code value with random, unique value', () => cy.fillInput("ts-param-submission-value", createdTermCode = `CODE_${getShortUniqueId()}`))

When('User fills trial summary parameter submission name value with random, unique value', () => cy.fillInput("ts-param-test-name-submission-value", `NAME_${getShortUniqueId()}`))

When('User selects first library for trial summary parameter', () => cy.selectFirstVSelect("ts-param-library"))

When('User selects first required level for trial summary parameter', () => cy.selectFirstVSelect("ts-param-required-level"))

When('User selects {string} as required level for trial summary parameter', (value) => cy.selectVSelect("ts-param-required-level", value))

When('User selects {string} as osb name for trial summary parameter', (value) => cy.selectVSelect("ts-param-osb-field-name", value))

function assertRequiredField(dataCy) {
    cy.get(`[data-cy="${dataCy}"]`).closest('.v-input').should("contain", "This field is required")
}

function formatHistoryDate(value) {
    return new Date(value).toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
    });
}
