const { getShortUniqueId } = require("../../support/helper_functions");

const sdpsUrl = (studyUid) =>
  `/studies/${studyUid}/study-design-populations?page_number=1&page_size=0&total_count=true`;
const createSdpUrl = (studyUid) =>
  `/studies/${studyUid}/study-design-populations`;
const sdpUrl = (studyUid, sdpUid) =>
  `/studies/${studyUid}/study-design-populations/${sdpUid}`;

Cypress.Commands.add("createStudyDesignPopulation", (studyUid) => {
  cy.sendPostRequest(createSdpUrl(studyUid), {
    name: `SDP ${getShortUniqueId()}`,
  });
  cy.reload();
});

// Creates a population with an explicit group_id so tests can assert the chip
// value shown on a linked criterion row. Exposes the group_id via Cypress.env.
Cypress.Commands.add("createStudyDesignPopulationWithGroupId", (studyUid) => {
  const groupId = `GRP${getShortUniqueId()}`;
  cy.sendPostRequest(createSdpUrl(studyUid), {
    group_id: groupId,
    name: `SDP ${getShortUniqueId()}`,
  }).then(() => {
    Cypress.env("TEST_SDP_GROUP_ID", groupId);
  });
});

Cypress.Commands.add("checkAndCreateStudyDesignPopulation", () => {
  const studyUid = Cypress.env("TEST_STUDY_UID");
  cy.request(Cypress.env("API") + sdpsUrl(studyUid)).then((resp) => {
    if (resp.body.total === 0) {
      cy.createStudyDesignPopulation(studyUid);
    }
  });
});

// Self-contained: fetch every population for the study and delete it. Previously
// this iterated a module-level array that was only filled by getSdpUids, so
// callers that skipped that step deleted nothing and populations accumulated.
Cypress.Commands.add("deleteStudyDesignPopulations", (studyUid) => {
  cy.sendGetRequest(sdpsUrl(studyUid)).then((response) => {
    response.body.items.forEach((item) =>
      cy.sendDeleteRequest(sdpUrl(studyUid, item.uid)),
    );
  });
});
