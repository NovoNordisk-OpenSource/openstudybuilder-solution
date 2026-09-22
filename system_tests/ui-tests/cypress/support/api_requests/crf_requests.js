const dataTypesUrl = '/ct/codelists/terms?page_size=0&sort_by={"sponsor_preferred_name":true}&codelist_submission_value=CODMDT'
const odmsStudyEventsUrl = '/odms/study-events'
const odmsFormsUrl = '/odms/forms'
const odmsItemUrl = '/odms/items'
const odmItemGroupUrl = '/odms/item-groups'
const odmLinkFormToCollectionUrl = (collectionUid) => `/odms/study-events/${collectionUid}/forms?override=true`
const odmLinkGroupToFormUrl = (formUid) => `/odms/forms/${formUid}/item-groups?override=true`
const odmLinkItemToGroupUrl = (itemGroupUid) => `/odms/item-groups/${itemGroupUid}/items?override=true`
const odmApproveFormUrl = (formUid) => `/odms/forms/${formUid}/approvals`
const odmApproveCollectionUrl = (collectionUid) => `/odms/study-events/${collectionUid}/approvals`

let dataTypeUid

Cypress.Commands.add('createCrfCollection', (name) => { return cy.sendPostRequest(odmsStudyEventsUrl, {name:`${name}`}) })

Cypress.Commands.add('createCrfForm', (name) => { return cy.sendPostRequest(odmsFormsUrl, createCrfFormBody(name)) })

Cypress.Commands.add('createCrfItem', (name) => cy.sendPostRequest(odmsItemUrl, createCrfItemBody(name)))

Cypress.Commands.add('createCrfItemGroup', (name) => cy.sendPostRequest(odmItemGroupUrl, createCrfItemGroupBody(name)))

Cypress.Commands.add('linkFormToCollection', (nameformUid, collectionUid) => cy.sendPostRequest(odmLinkFormToCollectionUrl(collectionUid), linkFormToCollectionBody(nameformUid)))

Cypress.Commands.add('linkItemGroupToForm', (fromUid, groupItemUid) => cy.sendPostRequest(odmLinkGroupToFormUrl(fromUid), linkGroupToFormBody(groupItemUid)))

Cypress.Commands.add('linkItemToItemGroup', (itemGroupUid, itemUid) => cy.sendPostRequest(odmLinkItemToGroupUrl(itemGroupUid), linkItemToGroupBody(itemUid)))

Cypress.Commands.add('approveForm', (formUid) => cy.sendPostRequest(odmApproveFormUrl(formUid), {}))

Cypress.Commands.add('approveCollection', (collectionUid) => cy.sendPostRequest(odmApproveCollectionUrl(collectionUid), {}))

Cypress.Commands.add('getUnitDefinitionUid', (dataType) => cy.sendGetRequest(dataTypesUrl).then(response => dataTypeUid = response.body.items.find(item => item.submission_value == dataType).term_uid))

const createCrfFormBody = (name) => {
    return {
        oid: null,
        repeating: "No",
        aliases: [],
        translated_texts: [],
        vendor_elements: [],
        vendor_element_attributes: [],
        vendor_attributes: [],
        name: name,
    }
}

const createCrfItemBody = (name) => {
    return {
        oid: null,
        aliases: [],
        translated_texts: [],
        activity_instances: [
            {
                activity_instance_uid: "",
                activity_item_class_uid: "",
                odm_form_ui: "",
                odm_item_group_uid: "",
                order: 999999,
                preset_response_value: "",
                primary: false,
                value_condition: "",
                value_dependent_map: "",
                availableActivityItemClasses: [],
                availableParentForms: [],
                vendor_elements: [],
                vendor_element_attributes: [],
                vendor_attributes: []
            }
        ],
        name: name,
        datatype_uid: dataTypeUid,
        library_name: "Sponsor",
        unit_definitions: [],
        codelist_uid: null,
        terms: [],
        vendor_elements: [],
        vendor_element_attributes: [],
        vendor_attributes: []
    }
}

const createCrfItemGroupBody = (name) => {
    return {
        oid: null,
        repeating: "No",
        isReferenceData: "No",
        aliases: [],
        translated_texts: [],
        sdtm_domains: [],
        vendor_elements: [],
        vendor_element_attributes: [],
        vendor_attributes: [],
        name: name,
        library_name: "Sponsor",
        sdtm_domain_uids: []
    }
}

const linkFormToCollectionBody = (formUid) => {
    return [
            {
            "uid": formUid,
            "order_number": 1,
            "mandatory": "No",
            "locked": "No",
            "collection_exception_condition_oid": null
        }
    ]
}

const linkGroupToFormBody = (itemGroupUid) => {
    return [
            {
            "uid": itemGroupUid,
            "order_number": 1,
            "mandatory": "No",
            "collection_exception_condition_oid": null,
            "vendor": {
                "attributes": []
            }
        }
    ]
}

const linkItemToGroupBody = (itemUid) => {
    return [
            {
            "uid": itemUid,
            "order_number": 1,
            "mandatory": "No",
            "key_sequence": "No",
            "method_oid": "null",
            "imputation_method_oid": "null",
            "role": "null",
            "role_codelist_oid": "null",
            "collection_exception_condition_oid": "null",
            "vendor": {
                "attributes": []
            }
        }
    ]
}