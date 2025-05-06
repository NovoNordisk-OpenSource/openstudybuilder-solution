# Introduction 
This a small script that exports all defined studies from a Studybuilder instance. 
It connects to the api given by the API_BASE_URL environment variable.

# Usage
1.	Setting up
    - Use any Python >= 3.6 
    - Install dependencies with pip:
      `pip install -r requirements.txt` 
2.	Run it
    ```sh
    export API_BASE_URL="http://localhost:8000"
    python export.py
    ```

# Filtering on study number

It's possible to filter the output by including and/or excluding study numbers.
This is controlled via the `INCLUDE_STUDY_NUMBERS` and `EXCLUDE_STUDY_NUMBERS` environment variables.

This follows the following logic:
- Make a list of available studies.
- If `INCLUDE_STUDY_NUMBERS` is defined, remove the studies not on the include list.
- If `EXCLUDE_STUDY_NUMBERS` is defined, remove the studies on the exclude list.


# Output data
All output files are saved in json format to the subdirectory `output`.
The file names are the same as their corresponding endpoints, with slashes replaced by dots.

Example for unit definitions under concepts:

`/concepts/unit-definitions --> ./output/concepts.unit-definitions.json` 

Study epochs for study with uid "Study_000004":

`/studies/Study_000004/study-epochs --> ./output/studies.Study_000004.study-epochs.json`


# Azure pipeline
A pipeline definition is included. This can export from any of the cloud environments, and publishes the results as pipeline artifacts.

#  Authentication
## Fetching an access token using a client secret
This supports [OAuth 2.0 client credentials flow with shared secret](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow#first-case-access-token-request-with-a-shared-secret).
Credentials can be configured by setting all the following environment variables.
If *CLIENT_ID* is set, the authentication routine is activated.
```shell
CLIENT_ID="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
CLIENT_SECRET="...FILL-ME..."
TOKEN_ENDPOINT="https://login.microsoftonline.com/aabbccdd-aabb-aabb-aabb-aabbccddeeff/oauth2/v2.0/token"
SCOPE="api://abcdef01-abcd-abcd-abcd-abcdef012345/.default"
```

- **TOKEN_ENDPOINT** is the OAuth 2.0 token endpoint to fetch the access token from.
  Can be found in the OpenID Connect metadata document, or Azure Active Directory -> App registrations -> Endpoints.
- **SCOPE** is the scope to request at the authentication flow, and in case of the Microsoft Identity Platform,
  that is the application ID (in URI format) of the API and *.default*
  The main point here is that the OAuth authority should give back a valid access token.
- **CLIENT_ID** is the application id registered for this client application
- **CLIENT_SECRET** is one of the secret key values set up with the client application at the authority
Authentication is done once per migration script session, fetching an access token which is then included in each
request as the *Authorization* header.

## Using interactive authentication
To enable single sign on, use the following environment variables:
```shell
CLIENT_ID="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
AUTH_ENDPOINT="https://login.microsoftonline.com/aabbccdd-aabb-aabb-aabb-aabbccddeeff/oauth2/v2.0/authorize"
TOKEN_ENDPOINT="https://login.microsoftonline.com/aabbccdd-aabb-aabb-aabb-aabbccddeeff/oauth2/v2.0/token"
SCOPE="api://abcdef01-abcd-abcd-abcd-abcdef012345/.default"
```
- **AUTH_ENDPOINT** is the OAuth 2.0 authorization endpoint to redirecting the user's browser to initiate the authorization code flow.
  Can be found in the OpenID Connect metadata document, or Azure Active Directory -> App registrations -> Endpoints.

The other parameters have the same meaning as
when using a [client secret](#fetching-an-access-token-using-a-client-secret)

When calling the first api endpoint, a browser window will open prompting the user to log in.

# TODO
- Add whatever parts that are missing in the exported data. 
- Move the pipeline to `build-tools`? 



