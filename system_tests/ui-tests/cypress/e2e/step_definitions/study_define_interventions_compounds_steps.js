const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
import { study_compound_dosing_uid, study_compound_uid } from '../../support/api_requests/study_compounds_request.js';
import { getCurrStudyUid } from '../../support/helper_functions.js'

Given('[API] Study compound is created', () => cy.createSimpleCompound(getCurrStudyUid()))

Given('[API] Study compound dosing is created', () => cy.createCompoundDosing(getCurrStudyUid()))

Given('[API] Study compound simple data is fetched', () => cy.getCompundSimpleData())

Given('[API] Study compound alias data is fetched', () => cy.getCompundAliasData())

Given('[API] Study compound medical product data is fetched', () => cy.getMedicalProductData())

Given('[API] Study compound type of treatment data is fetched is created', () => cy.getTypeOfTreatmentUid())

Given('[API] Study compound data is fetched', () => cy.getStudyCompundData(getCurrStudyUid()))

Given('User searches the compound by the uid', () => cy.searchFor(study_compound_uid))

Given('User searches the compound dosing by the uid', () => cy.searchFor(study_compound_dosing_uid))

Given('User clicks add study compund button', () => cy.clickButton('add-study-compound'))

Given('User fills other information', () => cy.fillInput('other-information', 'Testing Information'))

Given('User select first type of treatment', () => cy.selectFirstVSelect('type-of-treatment'))

Given('User select last type of treatment', () => cy.selectLastVSelect('type-of-treatment'))

Given('User select first compund', () => cy.selectFirstVSelect('compound'))

Given('User select last compund', () => cy.selectLastVSelect('compound'))

Given('User select first medicinal product', () => cy.selectFirstVSelect('medicinal-product'))

Given('User select last medicinal product', () => cy.selectLastVSelect('medicinal-product'))

Given('User intercepts compund create request', () => cy.intercept('POST', '**/study-compounds').as('createdCompound'))

Given('User intercepts compund update request', () => cy.intercept('PATCH', '**/study-compounds/*').as('createdCompound'))

Given('User intercepts compund delete request', () => cy.intercept('**/study-compounds/**').as('deleteRequest'))

Given('User intercepts compund aliases request', () => cy.intercept('**/concepts/compound-aliases**').as('compoundAliasesRequest'))

Given('User intercepts compunds request', () => cy.intercept('**/concepts/compounds/**').as('compoundRequest'))

Given('User intercepts medicial products request', () => cy.intercept('**/concepts/medicinal-products**').as('medicinalProductRequest'))

Given('User intercepts pharmaceutical products request', () => cy.intercept('**/concepts/pharmaceutical-products/**').as('pharmaceuticalProductRequest'))

Then('The study compound is present in the compounds table', () => {
    cy.wait('@createdCompound').then((req) => {
        let compoundData = req.response.body
        cy.searchFor(compoundData.study_compound_uid)
        cy.checkRowByIndex(0, 'Type of treatment', compoundData.type_of_treatment.term_name)
        cy.checkRowByIndex(0, 'Compound', compoundData.compound.name)
        cy.checkRowByIndex(0, 'Compound alias', compoundData.compound_alias.name)
        cy.checkRowByIndex(0, 'Medicinal product', compoundData.medicinal_product.name)
        cy.checkRowByIndex(0, 'Dose frequency', compoundData.medicinal_product.dose_frequencies.map((freq) => freq.name).join(', '))
    })
})

Then('The compound alias data is automatically populated from library', () => {
    cy.wait('@compoundAliasesRequest').then((request) => {
        let alias_name = request.response.body.items[0].compound.name
        let other_aliases = otherAliases(request.response.body.items)

        cy.get('[data-cy="compound-alias"]').should('contain', alias_name)
        cy.get('[data-cy="other-aliases"] input').should('have.value', other_aliases)
    })
})

Then('The Medicinal Product data is automatically populated from library', () => {
    cy.wait('@medicinalProductRequest').then((request) => {
        let dispensed_in = request.response.body.items[0].dispenser.name
        cy.get('[data-cy="dispensed-in"] input').should('have.value', dispensed_in ? dispensed_in : '-')
    })
})

Then('The Pharmaceutical Product data is automatically populated from library', () => {
    cy.wait('@pharmaceuticalProductRequest').then((request) => {
        let active_substance = request.response.body.formulations[0].ingredients[0].active_substance.inn
        let analyte_number = request.response.body.formulations[0].ingredients[0].active_substance.analyte_number
        let long_number = request.response.body.formulations[0].ingredients[0].active_substance.long_number
        let short_number = request.response.body.formulations[0].ingredients[0].active_substance.short_number
        let substance_unii = request.response.body.formulations[0].ingredients[0].active_substance.unii.substance_unii
        let pclass = request.response.body.formulations[0].ingredients[0].active_substance.unii.pclass_name
        let id = request.response.body.formulations[0].ingredients[0].active_substance.unii.pclass_id
        let pharmacological_class = `${pclass} (${id})`

        cy.get('[data-cy="active-substance"] input').should('have.value', active_substance ? active_substance : '-')
        cy.get('[data-cy="analyte-number"] input').should('have.value', analyte_number ? analyte_number : '-')
        cy.get('[data-cy="long-number"] input').should('have.value', long_number ? long_number : '-')
        cy.get('[data-cy="short-number"] input').should('have.value', short_number ? short_number : '-')
        cy.get('[data-cy="substance"] input').should('have.value', substance_unii ? substance_unii : '-')
        cy.get('[data-cy="pharmacological-class"] input').should('have.value', pharmacological_class ? pharmacological_class : '-')
    })
})

Then('The user cannot save the form', () => cy.get('.v-messages__message').should('contain', 'This field is required'))

Then('The study compound is removed', () => {
    cy.wait('@deleteRequest').then((req) => expect(req.response.statusCode).to.eq(204))
})

Given('The study compounds data is cleaned for testing purspose', () => {
    let currentStudy = getCurrStudyUid()
    cy.sendGetRequest(`/studies/${currentStudy}/study-compounds`).then((response) => {
        if (response.body.items.length > 0) {
            response.body.items.forEach((item) => {
                cy.sendDeleteRequest(`/studies/${currentStudy}/study-compounds/${item.study_compound_uid}`)
            })
        }
    })
})

function otherAliases(aliases) {
    const otherSynonyms = aliases.filter((item) => !item.is_preferred_synonym)
    return otherSynonyms.length
        ? otherSynonyms.map((item) => item.name).join(', ')
        : '-'
}