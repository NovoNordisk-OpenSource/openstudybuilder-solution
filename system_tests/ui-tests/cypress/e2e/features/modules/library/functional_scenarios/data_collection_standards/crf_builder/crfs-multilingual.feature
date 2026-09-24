@REQ_ID:1070683 @pending_implementation

Feature: Top Admin - Multilingual CRFs

    As a system user I must be able to switch between mutlilingual and single language for CRFs
    
    Background: User is logged in the system
        Given The user is logged in
        And The homepage is opened
        And The multilingual CRFs option is toggled on in the settings menu

    Scenario: [Multilingual][Toggle][On] User must be able to switch to multilingual CRFs
        Given The homepage is opened
        And The multilingual CRFs option is toggled off in the settings menu
        When The multilingual CRFs option is toggled on in the settings menu
        Then The system is showing Translations section for the CRF Forms
        And The system is showing Translations section for the CRF Item Groups
        And The system is showing Translations section for the CRF Items

    Scenario: [Multilingual][Toggle][Off] User must be able to switch to single language CRFs
        And The '/library/crf-builder/templates' page is opened
        When The multilingual CRFs option is toggled off in the settings menu
        Then The system is not showing Translations section for the CRF Forms
        And The system is not showing Translations section for the CRF Item Groups
        And The system is not showing Translations section for the CRF Items

    Scenario: [Create][Positive case][Form] User must be able to create multilingual CRF Form
        Given The '/library/crf-builder/forms' page is opened
        When The new CRF Form is created with description providied
        And Form continue button is clicked
        And Form continue button is clicked
        And Form continue button is clicked
        And Form save button is clicked
        Then The CRF Form description is saved within the system

    Scenario: [Create][Positive case][Group] User must be able to create multilingual CRF Item Group
        Given The '/library/crf-builder/item-groups' page is opened
        When The new CRF Item Group is created with description providied
        And Form continue button is clicked
        And Form continue button is clicked
        And Form continue button is clicked
        And Form save button is clicked
        Then The CRF Item Group description is saved within the system

    Scenario: [Create][Positive case][Item] User must be able to create multilingual CRF Item
        Given The '/library/crf-builder/items' page is opened
        When The new CRF Item is created with description providied
        And Form continue button is clicked
        And Form continue button is clicked
        And Form continue button is clicked
        And Form continue button is clicked
        And Form save button is clicked
        Then The CRF Item description is saved within the system

