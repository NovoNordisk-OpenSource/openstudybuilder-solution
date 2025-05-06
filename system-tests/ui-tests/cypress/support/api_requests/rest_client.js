Cypress.Commands.add('sendPostRequest', (url, body) => {
    cy.request('POST', Cypress.env('API') + url, body).then((response) => {
        expect(response.status).to.be.oneOf([200, 201])
        return response;
    })
})

Cypress.Commands.add('sendDeleteRequest', (url) => {
    cy.request('DELETE', Cypress.env('API') + url, {}).then((response) => expect(response.status).to.eq(200))
})

Cypress.Commands.add('sendGetRequest', (url) => {
    cy.request('GET', Cypress.env('API') + url).then((response) => {
        expect(response.status).to.eq(200)
        return response;
    })
})
