function getCardByName(name) {
    return cy.get(`input[value^="${name}"]`).first()
      .parents('.react-grid-item').first()
}

Cypress.Commands.add('selectFromSelectorTable', (tableName, value) => {
    getCardByName(tableName).contains('[role="row"]', value).within(() => {
        cy.get('button').click()
    })
})

Cypress.Commands.add('findInTable', (table, dataTable) => {
    dataTable.hashes().forEach((element) => {
        getCardByName(table).find('[role="row"]').eq(element.row).within(() => {
            cy.get(`[data-field="${element.column}"]`).should('contain', element.value)
        })
    })
})

Cypress.Commands.add('findInPanel', (panelName, value) => {
    cy.get('.react-grid-item').should(($items) => {
        const card = $items.filter(`:has(input[value^="${panelName}"])`)
        expect(card.length, `Card "${panelName}" should exist`).to.be.greaterThan(0)
        const content = card.find('.MuiCardContent-root')
        expect(content.length, `Card "${panelName}" should have content`).to.be.greaterThan(0)
        expect(content.text()).to.contain(value)
    })
})

Cypress.Commands.add('panelShouldNotContain', (panelName, value) => {
    cy.get('.react-grid-item').should(($items) => {
        const card = $items.filter(`:has(input[value^="${panelName}"])`)
        expect(card.length, `Card "${panelName}" should exist`).to.be.greaterThan(0)
        const content = card.find('.MuiCardContent-root')
        expect(content.length, `Card "${panelName}" should have content`).to.be.greaterThan(0)
        expect(content.text()).to.not.contain(value)
    })
})
