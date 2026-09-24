const { Then } = require('@badeball/cypress-cucumber-preprocessor')
const { getCurrStudyUid } = require('../../support/helper_functions')

let bodyObject, studyObject

Then('JSON format is selected', () => cy.get('.v-overlay-container .v-list-item').should('contain', 'JSON').click())

Then('User intercepts usdm request', () => cy.intercept(`/api/usdm/v4/studyDefinitions/${getCurrStudyUid()}`).as('usdmRequest'))

Then('User gets data from usdm request', () => cy.wait('@usdmRequest').then(request => {
    bodyObject = request.response.body
    studyObject = request.response.body.study
}))

Then('A JSON text field showing the study definition in USDM format is displayed', () => {
    cy.get('.json-meta').eq(0).should('contain.text', `${Object.keys(bodyObject).length} keys`)
    cy.get('.json-meta').eq(1).should('contain.text', `${Object.keys(studyObject).length} keys`)
    checkData(0, bodyObject)
    checkData(1, studyObject)
})

function checkData(indexOfNode, objectToCompare) {
    cy.get('.json-meta').eq(indexOfNode).parent().next('.json-children').children('.json-content').children('.json-primitive').then(jsonKeys => {
        cy.wrap(jsonKeys).invoke('text').then(text => {
            for (const [key, value] of Object.entries(objectToCompare)) {
                const valueToCheck = `${JSON.stringify(key)}: ${JSON.stringify(value)}`
                if (typeof(value) != 'object' || value == null) expect(text).to.contain((valueToCheck))
            }
        })
    })

    cy.get('.json-meta').eq(indexOfNode).parent().next('.json-children').children('.json-content').children('.json-details').children().children('.json-key').then(jsonKeys => {
        cy.wrap(jsonKeys).invoke('text').then(text => {
            for (const [key, value] of Object.entries(objectToCompare)) {
                if (typeof(value) == 'object' && value != null) expect(text).to.contain((`"${key}"`))
            }
        })
    })
}
