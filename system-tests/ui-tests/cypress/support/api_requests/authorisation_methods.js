//Login method to obtain token prepare env variables.
Cypress.Commands.add('prepareAuthTokens', () => {
    let httpToken = Cypress.env('TOKEN_ENDPOINT')
    if (String(httpToken).includes('https')) {
        cy.request({
            method: 'POST',
            url: Cypress.env('TOKEN_ENDPOINT'),
            form: true,
            body: {
                grant_type: Cypress.env('GRANT_TYPE'),
                client_id: Cypress.env('CLIENT_ID'),
                scope: Cypress.env('SCOPE'),
                client_secret: Cypress.env('CLIENT_SECRET')
            },
        }).then((response) => {
            let jwtToken = JSON.parse(Buffer.from(response.body.access_token.split('.')[1], 'base64').toString())
            let appData = {
                "access_token": response.body.access_token,
                "expires_at": jwtToken.exp,
                "id_token": Cypress.env('STATIC_IDTOKEN'),
                "profile": {
                    "name": Cypress.env('TESTUSER_NAME'),
                    "oid": jwtToken.oid,
                    "preferred_username": Cypress.env('TESTUSER_MAIL'),
                    "rh": jwtToken.rh,
                    "sub": jwtToken.sub,
                    "tid": jwtToken.tid,
                    "uti": jwtToken.uti,
                    "ver": jwtToken.ver
                },
                "refresh_token": "",
                "scope": Cypress.env('SCOPE'),
                "session_state": Cypress.env('STATIC_SESSION_STATE'),
                "token_type": "Bearer",

            }
            Cypress.env('authSessionKey', 'oidc.user:studybuilder-frontend:' + Cypress.env('STUDYBUILDER_CLIENT_ID'))
            Cypress.env('authSessionValue', JSON.stringify(appData))
            Cypress.env('authorization', 'Bearer ' + response.body.access_token)
        })
    } else {
        console.log('Auth not enabled or token endpoint not provided')
    }
})

//Take env variables and inject into the session storage
Cypress.Commands.add('loginUser', () => {
    let httpToken = Cypress.env('TOKEN_ENDPOINT')
    if (String(httpToken).includes('https')) {
        window.sessionStorage.setItem(Cypress.env('authSessionKey'), (Cypress.env('authSessionValue')))
    } else {
        console.log('Auth not enabled or token endpoint not provided')
    }
})

//Include auth tokens within all the cy.request() commands
Cypress.Commands.overwrite('request', (originalFn, ...args) => {
    let httpToken = Cypress.env('TOKEN_ENDPOINT')
    if (String(httpToken).includes('https')) {
        const defaults = {
            headers: {
                'Authorization': Cypress.env('authorization')
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
    } else {
        const defaults = {
            headers: {
                'Authorization': ''
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
    }
});