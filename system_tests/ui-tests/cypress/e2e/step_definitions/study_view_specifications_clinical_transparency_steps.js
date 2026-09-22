const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const {
    DOMParser
} = require("@xmldom/xmldom");

When('The user selects {string} specification', (specification_to_select) => {
    cy.intercept('**/pharma-cm').as('specification_data')
    cy.contains('.page-title.ml-4', specification_to_select).should('exist')
    cy.get('[data-cy="select-specification"]').within(() => {
        cy.get('.v-field__field').click()
    })
    cy.get('.v-overlay__content').within(() => cy.contains('.v-list-item__content', 'View All').click())
    cy.get('.v-overlay__content').within(() => cy.contains('.v-list-item__content', specification_to_select).click())
    cy.wait(500) // waiting for table to reload
})

const study_id = "CDISC DEV-0";
const filePath = `cypress/downloads/Clinical Transparency ${study_id}.xml`

Then('The correct study values are presented for Identification', () => {
    cy.wait('@specification_data').then((data) => {
        cy.getRowIndex('Study ID').then(index => cy.checkRowByIndex(index, 'Values', data.response.body.unique_protocol_identification_number))
        cy.getRowIndex('Study Short Title').then(index => cy.checkRowByIndex(index, 'Values', data.response.body.brief_title))
        cy.getRowIndex('Study Acronym').then(index => cy.checkRowByIndex(index, 'Values', data.response.body.acronym))
        cy.getRowIndex('Study Title').then(index => cy.checkRowByIndex(index, 'Values', data.response.body.official_title))
    })
})

Then('The correct study values are presented for Secondary IDs', () => {
    cy.wait('@specification_data').then((data) => {
        let secondary_ids_data = data.response.body.secondary_ids
        secondary_ids_data.forEach((data, index) => {
            cy.checkRowByIndex(index, 'Secondary ID', data.secondary_id)
            cy.checkRowByIndex(index, 'Secondary ID Type', data.id_type)
            cy.checkRowByIndex(index, 'Registry Identifier', data.description)
        })
    })
})

// Then('The correct study values are presented for Conditions', () => {
//     // cy.wait('@specification_data').then((data) => {
//     //     let secondary_ids_data = data.response.body.secondary_ids
//     //      secondary_ids_data.forEach((data, index) => {
//     //          cy.checkRowByIndex(index, 'Secondary ID', data.secondary_id)
//     //          cy.checkRowByIndex(index, 'Secondary ID Type', data.id_type)
//     //          cy.checkRowByIndex(index, 'Registry Identifier', data.description)
//     //      })
//     //  })
// })

Then('The correct study values are presented for Design', () => {
    cy.wait('@specification_data').then((data) => {
        cy.getRowIndex('Study Type').then(index => cy.checkRowByIndex(index, 'Values', data.response.body.study_type))
        cy.getRowIndex('Study Intent Type').then(index => cy.checkRowByIndex(index, 'Values', data.response.body.intervention_type))
        cy.getRowIndex('Study Phase Classification').then(index => cy.checkRowByIndex(index, 'Values', data.response.body.study_phase))
        cy.getRowIndex('Intervention Model').then(index => cy.checkRowByIndex(index, 'Values', data.response.body.interventional_study_model))
        cy.getRowIndex('Number of Arms').then(index => cy.checkRowByIndex(index, 'Values', data.response.body.number_of_arms))
        cy.getRowIndex('Study is randomised').then(index => cy.checkRowByIndex(index, 'Values', data.response.body.allocation))
    })
})

Then('The correct study values are presented for Interventions', () => {
    cy.wait('@specification_data').then((data) => {
        let secondary_ids_data = data.response.body.study_arms
         secondary_ids_data.forEach((data, index) => {
             cy.checkRowByIndex(index, 'Arm Title', data.arm_title)
             cy.checkRowByIndex(index, 'Type', data.arm_type)
             cy.checkRowByIndex(index, 'Description', data.arm_description)
         })
     })
})

Then('The correct study values are presented for Outcome Measures', () => {
    cy.wait('@specification_data').then((data) => {
        let secondary_ids_data = data.response.body.outcome_measures
         secondary_ids_data.forEach((data, index) => {
             cy.checkRowByIndex(index, 'Outcome Measure', data.title)
             cy.checkRowByIndex(index, 'Time Frame', data.timeframe)
             cy.checkRowByIndex(index, 'Description', data.description)
         })
     })
})


Then('The user clicks on Download XML button', () => {
    cy.clickButton('export-xml-pharma-cm')
})

Then('The correct file is downloaded', () => {
    cy.readFile(filePath).then((xmlContent) => {
        let keys = [
            "acronym",
            "address",
            "affiliation",
            "allocation",
            "sharing_ipd",
            "study_type",
        ];
        for (let item in keys) {
            expect(keyOccursInXML(keys[item], xmlContent)).to.be.true // Output: true
        }



    })
})

Then('The file is XML valid', () => {
    cy.readFile(filePath).then((xmlContent) => {
        expect(validateXML(xmlContent)).to.be.true

    })
})

function keyOccursInXML(key, xmlString) {
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(xmlString, "text/xml");
    const elements = xmlDoc.getElementsByTagName(key);
    return elements.length > 0;
}

function validateXML(xmlContent) {
    const parser = new DOMParser();
    const xmlDoc = parser
        .parseFromString(xmlContent, "text/xml");
    if (xmlDoc
        .getElementsByTagName("parsererror")
        .length > 0) {
        console.error(
            "XML parsing error:",
            xmlDoc
                .getElementsByTagName("parsererror")[0]
        );
    } else {
        return true
    }
}