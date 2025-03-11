@REQ_ID:1070674
Feature: Library - Library page 'About' section

    As a user I want to have ability of reading information about certain areas of the system and those areas purpose.

    Background: User is logged in
        Given The user is logged in

    Scenario: User must be able to view the description under 'Process Overview' tile in library Module
        Given The '/library' page is opened
        Then A tile 'Process Overview' is visible with following description
            """
            Find schematic overviews of the activities covered under the Library. You can use these to navigate to the relevant pages to enter or look up information.
            """

    Scenario: User must be able to view the description under 'Code Lists' tile in library Module
        Given The '/library' page is opened
        Then A tile 'Code Lists' is visible with following description
            """
            Find the CDISC controlled terminology, including the code lists, the valid values and associated definitions for each code list and the evolution in packages and terms over time. Sponsor defined list and terms are also included.
            """

    Scenario: User must be able to view the description under 'Dictionaries' tile in library Module
        Given The '/library' page is opened
        Then A tile 'Dictionaries' is visible with following description
            """
            Find relevant external dictionaries and thesaurus for clinical development such as SNOMED, MedDRA, MED-RT, UNII, LOINC, UCUM. Since some of these dictionaries are very large, only selected terms relevant for the Novo Nordisk pipeline are included.
            """

    Scenario: User must be able to view the description under 'Concepts' tile in library Module
        Given The '/library' page is opened
        Then A tile 'Concepts' is visible with following description
            """
            Find controlled listings of the terms to use for generic concepts such as units, activities, compounds and CRFs.
            """

    Scenario: User must be able to view the description under 'Syntax Templates' tile in library Module
        Given The '/library' page is opened
        Then A tile 'Syntax Templates' is visible with following description
            """
            View (or manage) the different syntax templates used for specifying the objectives, the endpoints, the eligibility, randomisation, dosing and other criteria for the individual studies. Only templates in status Final can be used under Studies.
            """

    Scenario: User must be able to view the description under 'Template Instantiations' tile in library Module
        Given The '/library' page is opened
        Then A tile 'Template Instantiations' is visible with following description
            """
            See how the different templates are used in the studies, including number of studies using a specific syntax and which studies.
            """

    Scenario: User must be able to view the description under 'Template Collections' tile in library Module
        Given The '/library' page is opened
        Then A tile 'Template Collections' is visible with following description
            """
            Find relevant template collections for project templates, shared templates and supporting templates.
            """

    Scenario: User must be able to view the description under 'Data Exchange Standards' tile in library Module
        Given The '/library' page is opened
        Then A tile 'Data Exchange Standards' is visible with following description
            """
            See the complete master model for the following CDISC data exchange standards: CDASH, SDTM and ADaM.
            """

    Scenario: User must be able to view the description under 'List' tile in library Module
        Given The '/library' page is opened
        Then A tile 'List' is visible with following description
            """
            Find listings of all codes list and terms for controlled terminology, dictionaries, concepts as well as the data exchange standards, in both new and legacy format.
            """

    Scenario Outline: User must be able to use tile dropdowns to navigate to the pages
        Given A test study is selected
        And The '/library' page is opened
        When The '<page>' is clicked in the dropdown of '<name>' tile
        Then The current URL is '<url>'

        Examples:
            | name                    | page                  | url                                            |
            | Code Lists              | Dashboard             | /library/ct_dashboard                          |
            | Code Lists              | CT Catalogues         | /library/ct_catalogues/All                     |
            | Code Lists              | CT Packages           | /library/ct_packages                           |
            | Code Lists              | CDISC                 | /library/cdisc                                 |
            | Code Lists              | Sponsor               | /library/sponsor                               |
            | Code Lists              | Sponsor CT Packages   | /library/sponsor-ct-packages                   |
            | Dictionaries            | SNOMED                | /library/snomed                                |
            | Dictionaries            | MedDRA                | /library/meddra                                |
            | Dictionaries            | MED-RT                | /library/medrt                                 |
            | Dictionaries            | UNII                  | /library/unii                                  |
            | Dictionaries            | LOINC                 | /library/loinc                                 |
            | Dictionaries            | UCUM                  | /library/ucum                                  |
            | Concepts                | Activities            | /library/activities/activities                 |
            | Concepts                | Units                 | /library/units                                 |
            | Concepts                | CRFs                  | /library/crfs/templates                        |
            | Syntax Templates        | Objectives            | /library/objective_templates                   |
            | Syntax Templates        | Endpoints             | /library/endpoint_templates                    |
            | Syntax Templates        | Time Frames           | /library/timeframe_templates                   |
            | Syntax Templates        | Criteria              | /library/criteria_templates                    |
            | Syntax Templates        | Activity Instructions | /library/activity_instruction_templates        |
            | Syntax Templates        | Footnote              | /library/footnote_templates            |
            | Template Instantiations | Objectives            | /library/objectives                            |
            | Template Instantiations | Endpoints             | /library/endpoints                             |
            | Template Instantiations | Time Frames           | /library/timeframe_instances                   |
            | Template Instantiations | Criteria              | /library/criteria_instances                    |
            | Template Instantiations | Activity Instructions | /library/activity_instruction_instances        |
            | Template Instantiations | Footnote              | /library/footnote_instances            |
            | Template Collections    | Project Templates     | /library/project_templates                     |
            | Template Collections    | Shared Templates      | /library/shared_templates                      |
            | Template Collections    | Supporting Templates  | /library/supporting_templates                  |
            | Overview Pages          | Study Structures      | /library/overviews/study_structures            |
            | Data Exchange Standards | CDASH                 | /library/cdash                                 |
            | Data Exchange Standards | SDTM                  | /library/sdtm                                  |
            | Data Exchange Standards | ADaM                  | /library/adam                                  |
            | List                    | CDASH Standards       | /library/cdash_standards                       |
            | List                    | SDTM Standards (CST)  | /library/sdtm_standards_cst                    |
            | List                    | SDTM Standards (DMW)  | /library/sdtm_standards_dmw                    |
            | List                    | ADaM Standards (CST)  | /library/adam_standards_cst                    |
            | List                    | ADaM Standards (New)  | /library/adam_standards_new                    |
