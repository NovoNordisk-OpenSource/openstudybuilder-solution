@REQ_ID:1741028

Feature: Studies - About Studies

    As a user I want to have ability of reading information about certain areas of the system and those areas purpose.

    Background: User must be logged in
        Given The user is logged in

    #hidden feature
    #Scenario: User must be able to see the description of the Process Overview area
    #    Given The '/studies' page is opened
    #    Then A tile 'Process Overview' is visible with following description
    #        """
    #        Find schematic overviews of the activities covered under Studies. You can use these to navigate to the relevant pages to enter or look up information.
    #        """

    Scenario: User must be able to see the description of the Manage Studies area
        Given The '/studies' page is opened
        Then A tile 'Manage Study' is visible with following description
            """
            Register new studies in the application and manage the life-cycle of these.
            """

    Scenario: User must be able to see the description of the Define Study area
        Given The '/studies' page is opened
        Then A tile 'Define Study' is visible with following description
            """
            Specify the design, interventions, study population, objectives, visit structure, schedule of activities and activity, etc. by using controlled terminology and syntax templates or by reusing content from other studies.
            """

    Scenario: User must be able to see the description of the View Specifications area
        Given The '/studies' page is opened
        Then A tile 'View Specifications' is visible with following description
            """
            Preview the study information (entered e.g. under Define Study), but compiled for different downstream usages, e.g. for import into the protocol template, for upload to external registries, for population of the SDTM study design datasets, for CRF design, etc.
            """

    Scenario: User must be able to see the description of the View Listings area
        Given The '/studies' page is opened
        Then A tile 'View Listings' is visible with following description
            """
            Various kinds of listings of the study specification data defined for your study.
            """

    Scenario Outline: User must be able to use tile dropdowns to navigate to the pages
        Given A test study is selected
        And The '/studies' page is opened
        When The '<page>' is clicked in the dropdown of '<name>' tile
        Then The current URL is '<url>'

        Examples:
            | page                          | name                | url                                  |
            #| Protocol Process              | Process Overview    | /studies/protocol_process            | #hidden feature
            | Study                         | Manage Study        | /study_status                        |
            | Data Standard Versions        | Manage Study        | /data_standard_versions              |
            | Study Title                   | Define Study        | /study_title                         |
            | Registry Identifiers          | Define Study        | /registry_identifiers                |
            | Study Properties              | Define Study        | /study_properties                    |
            | Study Structure               | Define Study        | /study_structure                     |
            | Study Population              | Define Study        | /population                          |
            | Study Criteria                | Define Study        | /selection_criteria                  |
            | Study Purpose                 | Define Study        | /study_purpose                       |
            | Study Activities              | Define Study        | /activities                          |
            | Data Specifications           | Define Study        | /data_specifications                 |
            | Protocol Elements             | View Specifications | /protocol_elements                   |
            | SDTM Study Design Datasets    | View Specifications | /sdtm_study_design_datasets          |
            | USDM                          | View Specifications | /usdm                                |
            | ICH M11                       | View Specifications | /ichm11                              |
            | Clinical Transparency         | View Specifications | /study_disclosure                    |
            #| Analysis Study Metadata (New) | View Listings       | /analysis_study_metadata_new/mdvisit | #hidden by feature flag
