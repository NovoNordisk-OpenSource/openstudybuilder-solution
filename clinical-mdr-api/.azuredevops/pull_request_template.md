Before submitting this PR, please make sure to address the following checklist:

## Basics
- [ ] Main branch is merged into your PR branch
- [ ] There are no merge conflicts
- [ ] Links to related PRs are included
- [ ] Are you including new dependencies? 
- [ ] Are they in a stable state and widely used?
- [ ] Are their licenses appropriate?

## Quality  
- [ ] Code builds clean without any errors or warnings
- [ ] API endpoints follow [Zalando API Guidelines](https://opensource.zalando.com/restful-api-guidelines/) naming conventions and best practices
- [ ] No issues reported by SonarQube
- [ ] No issues reported by schemathesis
- [ ] No warnings reported by pytest
- [ ] Tests cover the implemented functionality/code sufficiently
- [ ] Consider refactoring code that needs it, e.g. remove duplicate lines by adding reusable methods
- [ ] Relevant GET endpoints added to the list of [API checks](https://orgremoved.visualstudio.com/Clinical-MDR/_git/verifications?path=/tests/test_api.py) performed by the [verifications pipeline](https://orgremoved.visualstudio.com/Clinical-MDR/_build?definitionId=6184)
- [ ] Relevant [DB constraints checks](https://orgremoved.visualstudio.com/Clinical-MDR/_git/verifications?path=/tests/test_db.py) added to the [verifications pipeline](https://orgremoved.visualstudio.com/Clinical-MDR/_build?definitionId=6184) (in addition to performing these DB checks as part of [API tests](https://orgremoved.visualstudio.com/Clinical-MDR/_git/clinical-mdr-api?path=/clinical_mdr_api/tests/integration/api), where appropriate)

## Performance
- [ ] Relevant GET endpoints are covered by [load tests](https://orgremoved.visualstudio.com/Clinical-MDR/_git/studybuilder-load-test?path=/tests/endpoints.py) (executed by [this](https://orgremoved.visualstudio.com/Clinical-MDR/_build?definitionId=6964) pipeline)
- [ ] Performance of endpoints is satisfactory
- [ ] Are API calls paginated where appropriate?
- [ ] Is there a simpler and faster API endpoint that provides only the needed data?
- [ ] If filtering is applied, can we include it in the database query instead of applying it after retrieving all instances?
- [ ] Can many small calls be replaced by fewer larger ones?

## Documentation
- [ ] API documentation (OpenAPI specification) is sufficient and in accordance with the implemented functionality
- [ ] Descriptions/examples of API endpoints/parameters are grammatically and semantically correct, and easy to use by API consumers
- [ ] Default/example values of API query parameters do not produce errors when consumer tries to send a request via SwaggerUI
- [ ] [Physical data model](https://orgremoved.visualstudio.com/Clinical-MDR/_git/neo4j-mdr-db?path=/model/physical_data_model) is in sync with our neomodel data model (defined in `domain_repositories/models` folder)
- [ ] Relationship cardinalities in the physical data model are the same as defined in the `domain_repositories/models` folder
- [ ] `README` file is up-to-date

## Other
- [ ] Are there any breaking changes to existing API endpoints that affect other systems?
- [ ] If yes, we need to inform client applications to synchronize with the changes (e.g. Word add-in)
- [ ] In case of breaking API and/or DB model changes, create work items (or related PR's) covering the needed changes in other repositories, e.g. [frontend](https://orgremoved.visualstudio.com/Clinical-MDR/_git/studybuilder), [studybuilder-import](https://orgremoved.visualstudio.com/Clinical-MDR/_git/studybuilder-import), [db-schema-migration](https://orgremoved.visualstudio.com/Clinical-MDR/_git/db-schema-migration), [verifications](https://orgremoved.visualstudio.com/Clinical-MDR/_git/verifications?path=/tests). 

---



