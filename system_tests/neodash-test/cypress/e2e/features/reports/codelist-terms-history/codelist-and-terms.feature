@REQ_ID:1070674
@neodash_tests
Feature: Codelist/Terms History - Codelist and Terms

    As a user, I want to browse codelists and their versions of terms in a dashboard

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Codelist / Terms history' page is opened

    Scenario: User must be able to view the Codelist and Terms report panels
        Given The neoDash 'Codelist and Terms' tab is selected
        Then The following set of neoDash reports are displayed
            | report                       |
            | Pick a Codelist              |
            | Codelist Concept ID          |
            | Overview at Date :           |
            | Select CT Package            |
            | Terms History for Codelist - |
            | History of terms in Codelist |
            | Details for Term(s):         |

    Scenario: User must be able to view report values for a selected codelist and term
        Given The neoDash 'Codelist and Terms' tab is selected
        When The user selects 'Arm Type' from the 'CTCodelistAttributesValue name' dropdown
        And The user selects a value from Select CT Package table
        And The user selects the first term in the Terms history for the codelist table
        Then The Codelist Concept ID report returns a value
        And The Select CT Package table returns values
        And The Terms History for Codelist table returns values
        And The History of terms in Codelist timeline returns values
        And The Details for Terms table returns values

    @manual_test
    Scenario: User must be able to view codelists and version of their terms
        Given The neoDash 'Codelist and Terms' tab is selected
        When The user selects 'Method' from the 'CTCodelistAttributesValue name' dropdown
        Then The terms from the 'Method' codelist are displayed as a table having '517' terms
        And The terms from the 'Method' codelist are displayed in a timeline-view and term 'ANGIOGRAPHY' having 3 versions

    @manual_test
    Scenario: User must be able to view codelists and version of selected terms and their detailed attributes
        Given The neoDash 'Codelist and Terms' tab is selected
        When The user selects 'Method' from the 'CTCodelistAttributesValue name' dropdown
        And The user filters of #Changes to show terms with 3 changes
        And The user selects the term 'MUGA' in the Terms history for the codelist table
        Then The versions for the term 'MUGA' are displayed in a timeline-view showing 4 versions
        And The Details for term(s) for the term 'MUGA' are displayed with the following values
            | SubmissionValue | Ccode  | PreferredTerm                    | Synonyms                                               | Definition                                                                                                                                                                                      | StartDate  | EndDate    | Version | SubmissionValuediff | Ccodediff | PreferredTermdiff | Synonymsdiff | Definitiondiff |
            | MUGA            | C38073 | Radionuclide Ventriculogram Scan |                                                        | A multi-gated acquisition (MUGA) scan and a form of radionuclide imaging that provides a comprehensive look at blood flow and the function of the lower chambers of the heart ventricles. (NCI) | 2014-09-26 | 2015-12-18 | 1.0     | no                  | no        | no                | no           | no             |
            | MUGA            | C38073 | Radionuclide Ventriculogram Scan | Radionuclide Ventriculogram Scan                       | A multi-gated acquisition (MUGA) scan and a form of radionuclide imaging that provides a comprehensive look at blood flow and the function of the lower chambers of the heart ventricles. (NCI) | 2015-12-18 | 2022-09-30 | 2.0     | no                  | no        | no                | no           | no             |
            | MUGA            | C38073 | Multigated Acquisition Scan      | Radionuclide Ventriculogram Scan                       | A multi-gated acquisition (MUGA) scan and a form of radionuclide imaging that provides a comprehensive look at blood flow and the function of the lower chambers of the heart ventricles. (NCI) | 2022-09-30 | 2023-03-31 | 3.0     | no                  | no        | yes               | no           | no             |
            | MUGA            | C38073 | Multigated Acquisition Scan      | Gated Heart Pool Scan,Radionuclide Ventriculogram Scan | A multi-gated acquisition (MUGA) scan and a form of radionuclide imaging that provides a comprehensive look at blood flow and the function of the lower chambers of the heart ventricles.       | 2023-03-31 |            | 4.0     | no                  | no        | no                | yes          | yes            |