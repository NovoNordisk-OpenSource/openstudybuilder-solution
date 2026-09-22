const studyDataSupplierSync = (study_uid) =>  `/studies/${study_uid}/study-data-suppliers/sync`

Cypress.Commands.add('deleteDataSuppliersFromStudy', (studyUid) => {
    cy.sendUpdateRequest('PUT', studyDataSupplierSync(studyUid), {suppliers: []})
})
