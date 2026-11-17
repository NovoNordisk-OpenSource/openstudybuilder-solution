const { getShortUniqueId } = require("../../support/helper_functions");

const indicationUrl =
  "/dictionaries/terms?codelist_uid=DictionaryCodelist_000001&page_size=0";
const criteriaCategoryUrl =
  '/ct/terms?page_size=100&sort_by={"name.sponsor_preferred_name":true}&codelist_name=Criteria+Category';
const criteriaSubCategoryUrl =
  '/ct/terms?page_size=100&sort_by={"name.sponsor_preferred_name":true}&codelist_name=Criteria+Sub+Category';
const criteriaTypeUrl = "/ct/terms?page_size=100&codelist_name=Criteria+Type";



const criteriaTypeName = {
  inclusion: "Inclusion Criteria",
  exclusion: "Exclusion Criteria",
  dosing: "Dosing Criteria",
  "run-in": "Run-in Criteria",
  runIn: "Run-in Criteria",
  randomisation: "Randomisation Criteria",
  withdrawal: "Withdrawal Criteria",
};

// Creates and approves a criteria template with a unique name (so re-runs don't
// collide with 409 AlreadyExists) and captures its uid/name in Cypress.env.
// Sends a proper request object; the previous version double-encoded a string
// body and hardcoded uids, which failed with 400/409 against a fresh DB.
Cypress.Commands.add("createCriteriaTemplate", (criteriaType = "inclusion") => {
  const name = `Test ${criteriaType} criteria testTemplate ${getShortUniqueId()}`;
  cy.sendGetRequest(indicationUrl).then((indicationResp) => {
    const indicationUid = indicationResp.body.items[0].term_uid;
    cy.sendGetRequest(criteriaCategoryUrl).then((categoryResp) => {
      const categoryUid = categoryResp.body.items[0].term_uid;
      cy.sendGetRequest(criteriaSubCategoryUrl).then((subCategoryResp) => {
        const subCategoryUid = subCategoryResp.body.items[0].term_uid;
        cy.sendGetRequest(criteriaTypeUrl).then((typeResp) => {
          const typeUid = typeResp.body.items.find(
            (term) =>
              term.name.sponsor_preferred_name ===
              criteriaTypeName[criteriaType],
          ).term_uid;
          cy.sendPostRequest("/criteria-templates", {
            name: `<p>${name}</p>`,
            type_uid: typeUid,
            indication_uids: [indicationUid],
            category_uids: [categoryUid],
            sub_category_uids: [subCategoryUid],
          }).then((templateResp) => {
            const templateUid = templateResp.body.uid;
            Cypress.env("TEST_CRITERIA_TEMPLATE_UID", templateUid);
            Cypress.env("TEST_CRITERIA_TEMPLATE_NAME", name);
            cy.sendPostRequest(
              `/criteria-templates/${templateUid}/approvals`,
              {},
            );
          });
        });
      });
    });
  });
  cy.reload();
});

// Selects the previously created criteria template into the given study via the
// batch-select endpoint. This creates a study criterion without relying on the
// (fragile) template-copy UI dialog, and stores the resulting study_criteria_uid.
Cypress.Commands.add("selectStudyCriteriaFromTemplate", (studyUid) => {
  const templateUid = Cypress.env("TEST_CRITERIA_TEMPLATE_UID");
  cy.sendPostRequest(`/studies/${studyUid}/study-criteria/batch-select`, [
    {
      criteria_template_uid: templateUid,
      parameter_terms: [],
      library_name: "User Defined",
    },
  ]).then((resp) => {
    const created = Array.isArray(resp.body) ? resp.body[0] : resp.body;
    Cypress.env("TEST_STUDY_CRITERIA_UID", created.study_criteria_uid);
  });
});