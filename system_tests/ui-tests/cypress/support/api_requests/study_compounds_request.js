import { element_uid } from "./study_elements_requests";

const { getShortUniqueId } = require("../../support/helper_functions");

export let study_compound_uid, study_compound_dosing_uid
let compound_simple_uid, compound_simple_name
let type_of_treatment_uid
let compound_alias_data, compound_alias_uid, medical_product_data, medical_product_uid
let study_compound_data, study_compound_dose_value_uid

const createCompoundUrl = (study_uid) => `/studies/${study_uid}/study-compounds`
const createCompoundDosingUrl = (study_uid) => `/studies/${study_uid}/study-compound-dosings`
const compoundSimpleUrl = '/concepts/compounds-simple?filters={"status":{"v":["Final"]}}&page_size=0'
const treatmentTypeUrl = '/ct/codelists/terms?page_size=100&sort_by={"sponsor_preferred_name":true}&codelist_submission_value=TPOFTRT'
const compoundAliasUrl = (compound_simple_uid) => `/concepts/compound-aliases?filters={"compound_uid":{"v":["${compound_simple_uid}"]},"status":{"v":["Final"]}}&page_size=0`
const medicalProducsUrl = (compound_simple_uid) => `/concepts/medicinal-products?filters={"compound.uid":{"v":["${compound_simple_uid}"]},"status":{"v":["Final"]}}&page_size=0`
const studyCompoundsUrl = (study_uid) => `/studies/${study_uid}/study-compounds?page_size=0`

Cypress.Commands.add('createSimpleCompound', (study_uid) => {
    cy.sendPostRequest(createCompoundUrl(study_uid), createStudyCompoundsBody()).then(response => study_compound_uid = response.body.study_compound_uid)
})

Cypress.Commands.add('createCompoundDosing', (study_uid) => {
    cy.sendPostRequest(createCompoundDosingUrl(study_uid), createStudyCompoundsDosingBody()).then(response => study_compound_dosing_uid = response.body.study_compound_dosing_uid)
})

Cypress.Commands.add('getStudyCompundData', (study_uid) => {
    cy.sendGetRequest(studyCompoundsUrl(study_uid)).then(response => {
        study_compound_uid = response.body.items[0].study_compound_uid
        study_compound_dose_value_uid = response.body.items[0].medicinal_product.dose_values[0].uid
        study_compound_data = response.body.items[0]
    })
})

Cypress.Commands.add('getCompundSimpleData', () => {
    cy.sendGetRequest(compoundSimpleUrl).then(response => {
        compound_simple_uid = response.body.items[0].uid
        compound_simple_name = response.body.items[0].name
    })
})

Cypress.Commands.add('getCompundAliasData', () => {
    cy.sendGetRequest(compoundAliasUrl(compound_simple_uid)).then(response => {
        compound_alias_data = response.body.items[0]
        compound_alias_uid = response.body.items[0].uid
    })
})

Cypress.Commands.add('getMedicalProductData', () => {
    cy.sendGetRequest(medicalProducsUrl(compound_simple_uid)).then(response => {
        medical_product_data = response.body.items[0]
        medical_product_uid = response.body.items[0].uid
    })
})

Cypress.Commands.add('getTypeOfTreatmentUid', () => {
    cy.sendGetRequest(treatmentTypeUrl).then(response => type_of_treatment_uid = response.body.items[0].uid)
})

const createStudyCompoundsBody = () => {
    return {
        "compoundSimple": {
            "uid": compound_simple_uid,
            "name": compound_simple_name
        },
        "compound_alias": compound_alias_data,
        "medicinalProduct": medical_product_data,
        "dosage_form_uid": null,
        "strength_value_uid": null,
        "route_of_administration_uid": null,
        "dispenser_uid": null,
        "delivery_device_uid": null,
        "other_info": "E2E testing",
        "type_of_treatment_uid": "CTTerm_000155",
        "medicinal_product_uid": medical_product_uid,
        "compound_alias_uid": compound_alias_uid
    }
}

const createStudyCompoundsDosingBody = () => {
    return {
        "study_compound": study_compound_data,
        "dose_value_uid": study_compound_dose_value_uid,
        "study_element_uid": element_uid,
        "study_compound_uid": study_compound_uid
    }
}