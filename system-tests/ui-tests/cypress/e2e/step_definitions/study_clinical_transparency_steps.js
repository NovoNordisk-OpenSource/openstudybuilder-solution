const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");
const {
    DOMParser
} = require("xmldom");
When('The user selects {string} specification', (specification_to_select) => {
    cy.intercept('**/pharma-cm').as('specification_data')
    cy.get('[data-cy="select-specification"]').within(() => {
        cy.get('.v-field__field').click()
    })
    cy.get('.v-overlay__content').within(() => cy.contains('.v-list-item__content', 'View All').click())
    cy.get('.v-overlay__content').within(() => cy.contains('.v-list-item__content', specification_to_select).click())
    cy.wait(500) // waiting for table to reload
})

const study_id = "CDISC DEV-0";
const filePath = `cypress/downloads/Clinical Transparency ${study_id}.xml`

When("The study disclosure page for CDISC DEV-0 is accessed", () => cy.visitStudyPageForStudyId(study_id, 'study_disclosure'))


Then('The correct study values are presented for Identification', () => {
    cy.wait('@specification_data').then((data) => {
        cy.checkRowValueByColumnName('Study ID', 'Values', data.response.body.unique_protocol_identification_number)
        cy.checkRowValueByColumnName('Study Short Title', 'Values', data.response.body.brief_title)
        cy.checkRowValueByColumnName('Study Acronym', 'Values', data.response.body.acronym)
        cy.checkRowValueByColumnName('Study Title', 'Values', data.response.body.official_title)
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
        cy.checkRowValueByColumnName('Study Type', 'Values', data.response.body.study_type)
        cy.checkRowValueByColumnName('Study Intent Type', 'Values', data.response.body.intervention_type)
        cy.checkRowValueByColumnName('Study Phase Classification', 'Values', data.response.body.study_phase)
        cy.checkRowValueByColumnName('Intervention Model', 'Values', data.response.body.interventional_study_model)
        cy.checkRowValueByColumnName('Number of Arms', 'Values', data.response.body.number_of_arms)
        cy.checkRowValueByColumnName('Study is randomised', 'Values', data.response.body.allocation)
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