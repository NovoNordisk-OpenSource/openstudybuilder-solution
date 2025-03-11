import {
  getUidByStudyId,
  findMetadataByVersionAndStatus,
} from "../../support/helper_functions";

Cypress.Commands.add("selectTestStudy", (study) => {
  cy.request(Cypress.env("API") + "/studies/" + study).then((response) => {
    cy.log(response);
    window.localStorage.setItem("selectedStudy", JSON.stringify(response.body));
  });
});

Cypress.Commands.add("selectStudyByStudyId", (study_id) => {
  cy.request(
    Cypress.env("API") +
      "/studies?sort_by=%7B%22current_metadata.identification_metadata.study_id%22:true%7D&page_size=0"
  ).then((resp) => {
    let uid = getUidByStudyId(study_id, resp.body.items);
    cy.selectTestStudy(uid);
  });
});

Cypress.Commands.add(
  "selectStudyByIdVersionAndStatus",
  (study_id, version, status) => {
    cy.request(
      Cypress.env("API") +
        "/studies?sort_by=%7B%22current_metadata.identification_metadata.study_id%22:true%7D&page_size=0"
    ).then((resp) => {
      let uid = getUidByStudyId(study_id, resp.body.items);
      cy.request(
        Cypress.env("API") +
          "/studies/" +
          uid +
          "/snapshot-history?page_number=1&page_size=10&total_count=true"
      ).then((dataset) => {
        let metadata = findMetadataByVersionAndStatus(dataset.body.items, version, status)
        console.log(metadata)
        window.localStorage.setItem("selectedStudy", JSON.stringify(metadata));
    });
    });
  }
);

Cypress.Commands.add("visitStudyPageForStudyId", (study_id, page) => {
  cy.request(
    Cypress.env("API") +
      "/studies?sort_by=%7B%22current_metadata.identification_metadata.study_id%22:true%7D&page_size=0"
  ).then((resp) => {
    let uid = getUidByStudyId(study_id, resp.body.items);
    cy.visit("/studies/" + uid + "/" + page);
  });
});
