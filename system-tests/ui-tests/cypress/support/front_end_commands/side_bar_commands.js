Cypress.Commands.add('openFromSidebar', (section, submenu) => {
    cy.get('.v-navigation-drawer__content').within(() => {
        cy.clickButton(section).within(() => {
            cy.clickButton(submenu)
        })
    })

})