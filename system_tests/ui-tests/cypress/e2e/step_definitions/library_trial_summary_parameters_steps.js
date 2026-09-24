const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const { getCurrStudyUid, getShortUniqueId } = require("../../support/helper_functions");

let createdTermName;
let createdTermCode;

Given("The Trial Summary Parameter details page is opened", () => {
    cy.visit('/library/trial_summary_parameters');
    cy.searchFor('Draft');
    cy.clickTableActionsButton(0);
    cy.clickButton("View or edit details");
});

When("The sponsor values edit button is clicked", () => {
    cy.clickButton("edit-sponsor-values");
});

When("The attributes values edit button is clicked", () => {
    cy.clickButton("edit-attributes-values");
});

When("The CT values history button is clicked", () => {
    cy.intercept("GET", "**/api/ct/terms/*/attributes/versions*").as("versionHistory");
    cy.clickButton("term-attributes-version-history");
});

When("The sponsor values history button is clicked", () => {
    cy.intercept("GET", "**/api/ct/terms/*/names/versions*").as("versionHistory");
    cy.clickButton("term-sponsor-version-history");
});

When("The edit order button is clicked from the CT term codelists context table row", () => {
    cy.get('[data-cy="codelists-context-table"] [data-cy="table-item-action-button"]').first().click();
    cy.clickButton("Edit");
});

When("The order and submission value are updated", () => {
    cy.get('[data-cy="term-submission-value"] input').clear({ force: true }).type("E2E_CODE_UPDATED");
    cy.get('[data-cy="term-order"] input').clear({ force: true }).type("2");
});

Then("The updated values are shown in the 'CT term codelists context' table", () => {
    cy.get('[data-cy="codelists-context-table"]')
        .should("contain", "E2E_CODE_UPDATED")
        .and("contain", "2");
});

Then("The following actions are available", (dataTable) => {
    dataTable.rows().forEach((action) => {
        cy.get(`[data-cy="${action[0]}"]`).should("be.visible");
    });
});

Then("The version history window is displayed", () => {
    cy.get('[data-cy="version-history-window"]').should("be.visible");
});

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
    cy.get('[data-cy="page-title"]').should("be.visible");
    cy.get('[data-cy="header-card"]')
        .should("contain", libraryLabel)
        .and("contain", conceptIdLabel);
});

When("The user searches for a term in the search field", () => {
    cy.get('[data-cy="data-table"] tbody tr')
        .filter(":visible")
        .first()
        .find("td")
        .eq(2)
        .invoke("text")
        .then((value) => {
        const searchValue = value.trim();
        cy.wrap(searchValue).as("trialSummaryParameterSearchValue");
        cy.intercept("GET", "**/api/ct/codelists/C66738/terms?*").as("trialSummaryParameterSearch");
        cy.fillInput('search-field', searchValue)
    });
});

Then("The table is filtered to show only matching results", () => {
    cy.get("@trialSummaryParameterSearchValue").then((searchValue) => {
        cy.wait("@trialSummaryParameterSearch").then(({ response }) => {
            response.body.items.forEach((item) => {
                expect(item.sponsor_preferred_name).to.equal(searchValue);
            });
        });
    });
});

Then("The {string} section is visible with the following fields", (sectionName, dataTable) => {
    const cardSelectors = {
        "Term sponsor values": '[data-cy="term-sponsor-values-card"]',
        "Term attributes values": '[data-cy="term-attributes-values-card"]',
    };
    const cardSelector = cardSelectors[sectionName];
    cy.get(cardSelector).within(() => {
        dataTable.rows().forEach((field) => {
            cy.contains('td', field[0]).should("be.visible");
        });
    });
});

Then("The {string} table is visible with the following headers", (sectionName, dataTable) => {
    cy.get(`[data-cy="${sectionName}"]`).within(() => {
        dataTable.rows().forEach((header) => {
            cy.get('thead').should("contain", header[0]);
        });
    });
});

Then("The codelist context table is visible", () => {
    cy.get('[data-cy="codelists-context-table"]').should("be.visible");
});

When("The Term sponsor values are edited", () => {
    cy.fillInput("ts-param-notes", "E2E Trial Summary Parameter update");
});

Then("The updated sponsor values are shown in the overview page", () => {
    cy.get('[data-cy="notes"]').should("contain", "E2E Trial Summary Parameter update");
});

When("The Term attributes values are edited", () => {
    cy.fillInput("ts-param-definition", "E2E Trial Summary Parameter definition update");
});

Then("The updated attributes values are shown in the overview page", () => {
    cy.get('[data-cy="definition"]').should("contain", "E2E Trial Summary Parameter definition update");
});

When("The new Trial Summary Parameter form is filled in without the Sponsor name", () => {
    fillNewTrialSummaryParameterForm({
        code: `CODE_${getShortUniqueId()}`,
        includeSponsorName: false,
    });
});

Then("The form displays a validation error for the Sponsor name", () => {
    assertRequiredField("ts-param-sponsor-name");
});

When("The new Trial Summary Parameter form is filled in without the CT name", () => {
    fillNewTrialSummaryParameterForm({
        sponsorName: `E2E TS Param ${getShortUniqueId()}`,
        code: `CODE_${getShortUniqueId()}`,
        includeLibrary: false,
    });
});

Then("The form displays a validation error for the CT name", () => {
    assertRequiredField("ts-param-library");
});

When("The new Trial Summary Parameter form is filled in without the Code", () => {
    fillNewTrialSummaryParameterForm({
        sponsorName: `E2E TS Param ${getShortUniqueId()}`,
        includeCode: false,
    });
});

Then("The form displays a validation error for the Code", () => {
    assertRequiredField("ts-param-submission-value");
});

When("The new Trial Summary Parameter form is filled in without the Required level", () => {
    fillNewTrialSummaryParameterForm({
        sponsorName: `E2E TS Param ${getShortUniqueId()}`,
        code: `CODE_${getShortUniqueId()}`,
        includeRequiredLevel: false,
    });
});

Then("The form displays a validation error for the Required level", () => {
    assertRequiredField("ts-param-required-level");
});

When("The new Trial Summary Parameter form is filled in with an existing Sponsor name", () => {
    cy.getCellValueNoVisibilityCheck(0, 'Sponsor name').then((existingName) => {
        fillNewTrialSummaryParameterForm({
            sponsorName: existingName.trim(),
            code: `CODE_${getShortUniqueId()}`,
        });
    });
});

When("The new Trial Summary Parameter form is filled", () => {
    createdTermName = `E2E TS Param ${getShortUniqueId()}`;
    fillNewTrialSummaryParameterForm({
        sponsorName: createdTermName,
        code: `CODE_${getShortUniqueId()}`,
    });
});

Given("A Trial Summary Parameter mapped to Other Study Attributes is created through the UI", () => {
    createdTermName = `E2E TS Param ${getShortUniqueId()}`;
    createdTermCode = `CODE_${getShortUniqueId()}`;
    cy.visit('/library/trial_summary_parameters');
    cy.get('button .mdi-plus').click();
    fillNewTrialSummaryParameterForm({
        sponsorName: createdTermName,
        code: createdTermCode,
        requiredLevel: "Optional",
        osbFieldName: "other_study_attributes",
    });
    cy.searchFor(createdTermName);
    cy.get('[data-cy="data-table"] tbody').should("contain", createdTermName);
    cy.clickTableActionsButton(0);
    cy.clickButton("View or edit details");
    cy.get('[data-cy="osb-field-name"]').should("contain", "other_study_attributes");
    cy.clickButton("approve-term-sponsor-values");
    cy.get('[data-cy="approve-term-sponsor-values"]').should("not.exist");
    cy.clickButton("approve-term-attributes-values");
    cy.get('[data-cy="approve-term-attributes-values"]').should("not.exist");
    cy.visit(`/studies/${getCurrStudyUid()}/study_properties/other_study_attributes`);
    cy.get('[data-cy="add-other-study-attributes-button"]').click();
    cy.selectVSelect("other-attr-optional-parameter-0", createdTermName);
    cy.selectVSelect('other-attr-optional-null-flavor-0', 'Asked but unknown')
    cy.get('[data-cy="other-attr-required-remove-0"]').click()
    cy.clickButton("save-button");
    cy.get('[data-cy="form-body"]').should("not.exist");
    cy.get('[data-cy="data-table"] tbody').should("contain", createdTermCode);
});

Then("The new Trial Summary Parameter is visible in the table", () => {
    cy.searchFor(createdTermName);
    cy.get('[data-cy="data-table"] tbody').should("contain", createdTermName);
});

Then("The created Trial Summary Parameter is visible in the table", () => {
    cy.tableContains(createdTermCode);
});

Then("The name status is set to {string}", (status) => {
    cy.get('[data-cy="data-table"] tbody tr').contains(createdTermName)
        .closest('tr').should("contain", status);
});

Then("The attributes status is set to {string}", (status) => {
    cy.get('[data-cy="data-table"] tbody tr').contains(createdTermName)
        .closest('tr').should("contain", status);
});

function assertRequiredField(dataCy) {
    cy.get(`[data-cy="${dataCy}"]`)
        .closest('.v-input')
        .should("contain", "This field is required");
}

function fillNewTrialSummaryParameterForm({
    sponsorName,
    code,
    requiredLevel,
    osbFieldName,
    includeSponsorName = true,
    includeLibrary = true,
    includeCode = true,
    includeRequiredLevel = true,
}) {
    if (includeSponsorName) cy.fillInput("ts-param-sponsor-name", sponsorName);
    if (includeLibrary) cy.selectFirstVSelect("ts-param-library");
    if (includeCode) cy.fillInput("ts-param-submission-value", code);
    if (includeRequiredLevel) {
        requiredLevel
            ? cy.selectVSelect("ts-param-required-level", requiredLevel)
            : cy.selectFirstVSelect("ts-param-required-level");
    }
    if (osbFieldName) {
        cy.selectVSelect("ts-param-osb-field-name", osbFieldName);
    }
    cy.fillInput("ts-param-order", "1");
    cy.fillInput("ts-param-definition", "E2E Trial Summary Parameter definition");
    cy.clickButton("save-button");
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
