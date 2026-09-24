let bearerToken, authSessionKey, authSessionValue

Cypress.Commands.add('prepareAuthTokens', () => {
    cy.env(['TOKEN_ENDPOINT']).then(({ TOKEN_ENDPOINT }) => {
        if (String(TOKEN_ENDPOINT).includes('https')) {
            cy.getTokenData().then(response => {
                cy.env(['STATIC_IDTOKEN', 'TESTUSER_NAME', 'TESTUSER_MAIL', 'SCOPE', 'STATIC_SESSION_STATE', 'STUDYBUILDER_CLIENT_ID']).then(({ STATIC_IDTOKEN, TESTUSER_NAME, TESTUSER_MAIL, SCOPE, STATIC_SESSION_STATE, STUDYBUILDER_CLIENT_ID }) => {
                    const token = response.body.access_token
                    const jwtToken = JSON.parse(Cypress.Buffer.from(token.split('.')[1], 'base64').toString())
                    const appData = {
                        "access_token": token,
                        "expires_at": jwtToken.exp,
                        "id_token": STATIC_IDTOKEN,
                        "profile": {
                            "name": TESTUSER_NAME,
                            "oid": jwtToken.oid,
                            "preferred_username": TESTUSER_MAIL,
                            "rh": jwtToken.rh,
                            "sub": jwtToken.sub,
                            "tid": jwtToken.tid,
                            "uti": jwtToken.uti,
                            "ver": jwtToken.ver
                        },
                        "refresh_token": "",
                        "scope": SCOPE,
                        "session_state": STATIC_SESSION_STATE,
                        "token_type": "Bearer",
                    }
                    authSessionKey = `oidc.user:studybuilder-frontend:${STUDYBUILDER_CLIENT_ID}`
                    authSessionValue = JSON.stringify(appData)
                    bearerToken = `Bearer ${token}`
                })
            })
        }
        else {
            console.log('Auth not enabled or token endpoint not provided')
        }
    })
})

//Take env variables and inject into the session storage
Cypress.Commands.add('loginUser', () => {
    authSessionKey != null ? window.sessionStorage.setItem(authSessionKey, authSessionValue)
                           : console.log('Auth not enabled or token endpoint not provided')
})

Cypress.Commands.add('getTokenData', () => {
    cy.env(['TOKEN_ENDPOINT', 'GRANT_TYPE', 'CLIENT_ID', 'SCOPE', 'CLIENT_SECRET']).then(({ TOKEN_ENDPOINT, GRANT_TYPE, CLIENT_ID, SCOPE, CLIENT_SECRET }) => {
        cy.request({
            log: false,
            method: 'POST',
            url: TOKEN_ENDPOINT,
            form: true,
            body: tokenBody(GRANT_TYPE, CLIENT_ID, SCOPE, CLIENT_SECRET)
        }).then((response) => {
            return response;
        })
    })
})

//Include auth tokens within all the cy.request() commands
Cypress.Commands.overwrite('request', (originalFn, ...args) => {
    const defaults = {
        headers: {
            'Authorization': bearerToken ?? ''
        }
    };

    let options = {};
    if (typeof args[0] === 'object' && args[0] !== null) {
        options = args[0];
    } else if (args.length === 1) {
        [options.url] = args;
    } else if (args.length === 2) {
        [options.method, options.url] = args;
    } else if (args.length === 3) {
        [options.method, options.url, options.body] = args;
    }

    return originalFn({...defaults, ...options, ... { headers: {...defaults.headers, ...options.headers } } });
});

const tokenBody = (grantType, clientId, scope ,clientSecret) => {
    return {
        grant_type: grantType,
        client_id: clientId,
        scope: scope,
        client_secret: clientSecret
    }
}