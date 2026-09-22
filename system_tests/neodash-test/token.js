const msal = require('@azure/msal-node');

const dotenv = require('dotenv');

dotenv.config();

const clientId = process.env.CYPRESS_NEODASH_CLIENT_ID;
const tenantId = process.env.CYPRESS_NEODASH_TENANT_ID;
const username = process.env.CYPRESS_NEODASH_USERNAME;
const password = process.env.CYPRESS_NEODASH_PASSWORD;
const clientSecret = process.env.CYPRESS_NEODASH_CLIENT_SECRET;

const scope = [`api://${clientId}/.default`];

const msalConfig = {
    auth: {
        clientId: clientId,
        authority: `https://login.microsoftonline.com/${tenantId}`,
        clientSecret: clientSecret,
    }
};

const cca = new msal.ConfidentialClientApplication(msalConfig);

const acquireTokenByUsernamePasswordRequest = {
    scopes: scope,
    username: username,
    password: password,
};

cca.acquireTokenByUsernamePassword(acquireTokenByUsernamePasswordRequest).then((response) => {
    if (response.error) {
        console.log("Error here: " + response.error);
        console.log("Description: " + response.error_description);
    } else {
        process.env.CYPRESS_NEODASH_ID_TOKEN = response.accessToken;
        process.env.LOGIN_TOKEN = response.accessToken
        console.log(response.accessToken)
    }
}).catch((error) => {
    console.log(error);
});