const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

const jobsUrl = "**/api/jobs*";
const completedJob = {
    uid: "Job_000001",
    job_name: "Clone study CDISC DEV-9866 to 123-6678",
    status: "COMPLETED",
    author_id: "all.in@b2bfv7zbjhkehgyw.onmicrosoft.com",
    started_at: "2026-08-27T10:00:00Z",
    ended_at: "2026-08-27T10:00:05Z",
};

function interceptJobs(items, details = null) {
    cy.intercept("GET", jobsUrl, (request) => {
        request.reply({ body: { items, total: items.length, page: 1, size: 10 } });
    }).as("backgroundJobs");
    if (details) {
        cy.intercept("GET", `**/api/jobs/${details.uid}`, { body: details }).as("backgroundJobDetails");
    }
}

Given("Background jobs API returns a completed, running and failed job", () => {
    interceptJobs([
        completedJob,
        { ...completedJob, uid: "Job_000002", job_name: "Import study data", status: "RUNNING", ended_at: null },
        { ...completedJob, uid: "Job_000003", job_name: "Export study data", status: "FAILED" },
    ]);
});

Given("Background jobs API returns a completed job", () => interceptJobs([completedJob]));

Given("Background jobs API returns a completed job with details", () => {
    interceptJobs([completedJob], {
        ...completedJob,
        response: { uid: "Study_000100", message: "Study cloned successfully" },
        log: ["2026-08-27 10:00:01 INFO Copying study", "2026-08-27 10:00:05 INFO Completed"],
    });
});

When("User opens the background jobs dialog", () => {
    cy.clickButton("topbar-help");
    cy.clickButton("topbar-background-jobs");
    cy.wait("@backgroundJobs");
});

When("User opens the background job details", () => {
    cy.get('.v-overlay__content:visible').first().find('button[title="Job details"]').first().click();
    cy.wait("@backgroundJobDetails");
});

When("User refreshes the background jobs list", () => {
    cy.get('.v-overlay__content:visible').first().find('button[title="Reload"]').click();
    cy.wait("@backgroundJobs");
});

Then("The background jobs dialog is visible", () => cy.get('.v-overlay__content:visible').should("contain", "Background jobs"));

Then("The background jobs table has the expected columns", () => {
    cy.get('.v-overlay__content:visible').first().within(() => {
        cy.get('table thead').should("contain", "Name").and("contain", "Status").and("contain", "Started by").and("contain", "Started at").and("contain", "Finished at");
    });
});

Then("The background jobs table shows the job statuses", () => {
    cy.get('.v-overlay__content:visible').first().within(() => {
        cy.get('table tbody').should("contain", "COMPLETED").and("contain", "RUNNING").and("contain", "FAILED");
    });
});

Then("The background job details dialog is visible", () => cy.get('.v-overlay__content:visible').last().should("contain", "Job details"));

Then("The background job details show the response and log", () => {
    cy.get('.v-overlay__content:visible').last().should("contain", "Clone study CDISC DEV-9866 to 123-6678").and("contain", "COMPLETED").and("contain", "INFO Copying study").and("contain", "INFO Completed");
});

Then("The background jobs list was requested more than once", () => cy.get("@backgroundJobs.all").should("have.length.at.least", 2));