Cypress.Commands.add('sendPostRequest', (url, body, failOnStatusCode = true, expectedCodes = [200, 201, 207]) => {
    cy.env(['API']).then(({API}) => cy.request({ method: 'POST', url: `${API}${url}`, body: body, failOnStatusCode: failOnStatusCode}).then((response) => {
        expect(response.status).to.be.oneOf(expectedCodes)
        return response;
    }))
})

Cypress.Commands.add('sendUpdateRequest', (method, url, body) => {
    cy.env(['API']).then(({API}) => cy.request(method, `${API}${url}`, body).then((response) => {
        expect(response.status).to.be.oneOf([200])
        return response;
    }))
})

Cypress.Commands.add('sendDeleteRequest', (url) => {
    cy.env(['API']).then(({API}) => cy.request('DELETE', `${API}${url}`, {}).then((response) => expect(response.status).to.be.oneOf([200, 204])))
})

Cypress.Commands.add('sendGetRequest', (url) => {
    cy.env(['API']).then(({API}) => cy.request('GET', `${API}${url}`).then((response) => {
        expect(response.status).to.eq(200)
        return response;
    }))
})
