const { Given, When, Then } = require("@badeball/cypress-cucumber-preprocessor");

let templateForLinking
let formForLinking
let itemGroupForLinking
let selectedForm
let selectedItemGroup
let selectedItem

Given('The CRF Template in {string} status exists in database', (status) => {
    cy.request(Cypress.env('API') + '/concepts/odms/templates').then((resp) => {
        expect(JSON.stringify(resp.body.items)).to.contain(status)
    })
})

Given('The CRF Form in {string} status exists in database', (status) => {
    cy.request(Cypress.env('API') + '/concepts/odms/forms').then((resp) => {
        expect(JSON.stringify(resp.body.items)).to.contain(status)
    })
})

Given('The CRF Item Group in {string} status exists in database', (status) => {
    cy.request(Cypress.env('API') + '/concepts/odms/item-groups').then((resp) => {
        expect(JSON.stringify(resp.body.items)).to.contain(status)
    })
})

Given('The CRF Item in {string} status exists in database', (status) => {
    cy.request(Cypress.env('API') + '/concepts/odms/items').then((resp) => {
        expect(JSON.stringify(resp.body.items)).to.contain(status)
    })
})

When('The CRF Form is linked to CRF Template', () => {
    cy.contains('.v-chip__content', 'T').first().parent().parent().invoke('text').then((template) => {
        templateForLinking = template.substring(2, 256).trim()
    })
    cy.clickFirstButton('link-crf-template-to-crf-form')
    cy.get('[data-cy="form-body"]').filter(':visible').within(() => {
        cy.clickFirstButton('add-item-link')
        cy.get('[data-cy="remove-item-link"]').first().parent().siblings().invoke('text').then((form) => {
            selectedForm = form
        })
        cy.clickButton('save-button')
    })
    cy.waitForFormSave()
})

When('The CRF Item Group is linked to CRF Form', () => {
    cy.contains('.v-chip__content', 'F').first().parent().parent().invoke('text').then((form) => {
        formForLinking = form.substring(2, 256).trim()
    })
    cy.clickFirstButton('link-crf-form-to-crf-item-group')
    cy.get('[data-cy="form-body"]').filter(':visible').within(() => {
        cy.clickFirstButton('add-item-link')
        cy.get('[data-cy="remove-item-link"]').first().parent().siblings().invoke('text').then((itemGroup) => {
            selectedItemGroup = itemGroup
        })
        cy.clickButton('save-button')
    })
    cy.waitForFormSave()
})

When('The CRF Item is linked to CRF Item Group', () => {
    cy.contains('.v-chip__content', 'G').first().parent().parent().invoke('text').then((itemGroup) => {
        itemGroupForLinking = itemGroup.substring(2, 256).trim()
    })
    cy.clickFirstButton('link-crf-item-group-to-crf-item')
    cy.get('[data-cy="form-body"]').filter(':visible').within(() => {
        cy.clickFirstButton('add-item-link')
        cy.get('[data-cy="remove-item-link"]').first().parent().siblings().invoke('text').then((form) => {
            selectedItem = form
        })
        cy.clickButton('save-button')
    })
    cy.waitForFormSave()
})

Then('The CRF Form is displayed underneath the linked CRF Template', () => {
    cy.contains(templateForLinking).parentsUntil('tbody').next().within(() => {
        cy.contains('td', selectedForm)
    })
})

Then('The CRF Item Group is displayed underneath the linked CRF Form', () => {
    cy.contains(selectedForm).parentsUntil('tbody').next().within(() => {
        cy.contains('td', selectedItemGroup)
    })
})

Then('The CRF Item is displayed underneath the linked CRF Item Group', () => {
    cy.contains(itemGroupForLinking).parentsUntil('tbody').next().within(() => {
        cy.contains('td', selectedItem)
    })
})

When('The Mandatory checkbox is checked for given CRF Form', () => {
    cy.intercept('POST', '**/add-forms**').as('formWait')
    cy.get('[width="6%"] > .v-btn').first().click()
    cy.contains('.roundChip > .v-chip__content', 'F').first().parent().parent().parent().within(() => {
        cy.get('.v-input').not('.v-input--is-disabled').click()
    })
})

When('The Mandatory checkbox is checked for given CRF Item Group', () => {
    cy.intercept('POST', '**/add-item-groups**').as('itemGroupWait')
    cy.get('[width="6%"] > .v-btn').first().click()
    cy.get('[width="7%"] > .v-btn').first().click()
    cy.contains('.roundChip > .v-chip__content', 'G').first().parent().parent().parent().within(() => {
        cy.get('.v-input').not('.v-input--is-disabled').click()
    })
})

When('The Mandatory checkbox is checked for given CRF Item', () => {
    cy.intercept('POST', '**/add-items**').as('itemGroupWait')
    cy.get('[width="6%"] > .v-btn').first().click()
    cy.get('[width="7%"] > .v-btn').first().click()
    cy.get('[width="9%"] > .v-btn').first().click()
    cy.contains('.roundChip > .v-chip__content', 'I').first().parent().parent().parent().within(() => {
        cy.get('.v-input').not('.v-input--is-disabled').click()
    })
})

Then('The given CRF Form is now Mandatory', () => {
    cy.wait('@formWait').then((req) => {
        expect(req.response.body.forms[0].mandatory).to.equal('yes')
    })
})

Then('The given CRF Item Group is now Mandatory', () => {
    cy.wait('@itemGroupWait').then((req) => {
        expect(req.response.body.itemGroups[0].mandatory).to.equal('yes')
    })
})

Then('The given CRF Item is now Mandatory', () => {
    cy.wait('@itemGroupWait').then((req) => {
        expect(req.response.body.items[0].mandatory).to.equal('yes')
    })
})

Then('The given CRF Form has tick-mark in the Repeating column', () => {
    cy.get('[width="6%"] > .v-btn').first().click()
    cy.get('[width="7%"] > .v-btn').first().click()
    cy.get('[width="9%"] > .v-btn').first().click()
    cy.contains('.roundChip > .v-chip__content', 'F').first().parent().parent().parent().within(() => {
        cy.get('.v-input--is-disabled').within(() => {
            cy.get('.mdi-checkbox-marked').should('exist')
        })
    })
})

Then('The given CRF Item Group has tick-mark in the Repeating column', () => {
    cy.get('[width="6%"] > .v-btn').first().click()
    cy.get('[width="7%"] > .v-btn').first().click()
    cy.get('[width="9%"] > .v-btn').first().click()
    cy.contains('.roundChip > .v-chip__content', 'G').first().parent().parent().parent().within(() => {
        cy.get('.v-input--is-disabled').within(() => {
            cy.get('.mdi-checkbox-marked').should('exist')
        })
    })
})

Given('The CRF Tree consisting of Template, Form, Item Group and Item exists', () => {
    cy.log('pending')
})