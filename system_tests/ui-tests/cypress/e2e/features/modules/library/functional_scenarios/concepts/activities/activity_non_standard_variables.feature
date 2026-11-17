@REQ_ID:1070683
Feature: Library - Concepts - Activities - Non Standard Variables
    As a user, I want to manage the Activity Instances in the Concepts Library with Wizard Stepper 
    process to ensure the data is saved and displayed correctly.

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Feature flag] User must be able to turn on feature flag for non-standard variables
        When [API] The feature flag 'nsvs_library' is enabled

    Scenario: [Create][Positve case] User must be able to add a new non-standard variable
        Given The '/library/activities/non-standard-variables' page is opened
        And The plus button is clicked
        When Non-standard variable activity instance class value is selected as 'NumericFindings'
        And Non-standard variable code is set as random value
        And Non-standard variable label is set as 'NSV E2E label'
        And Non-standard variable role is selected as 'Identifier'
        And Non-standard variable data type is selected as 'CT Term'
        And Non-standard variable length is set as '30'
        And Form save button is clicked
        Then Non-standard variable is searched by code and found
        And Non-standard variable 'Multiple' is visible as 'No' in the table
        And Non-standard variable 'CDISC defined' is visible as 'No' in the table
        And Non-standard variable 'Semantic data type' is visible as 'CT Term' in the table
        And Non-standard variable 'Length' is visible as '30' in the table
        And Non-standard variable code, label and name are visible in the table with correct values
        And User goes to non-standard variable overview page by clicking its name
        And Non-standard variable sentence case name has correct value in the overview page
        And Non-standard variable label has correct value in the overview page
        And Non-standard variable is connected to Activity Instance Class 'NumericFindings'

    Scenario: [Create][Positve case][Multiple instance class] User must be able to add a new non-standard variable with more than one activity instance class
        Given The '/library/activities/non-standard-variables' page is opened
        And The plus button is clicked
        And User switches toggle on to allow mutilple selection of non-standard variable activity instace class
        And Non-standard variable activity instane class is cleared
        And User exapnds-collapse list of available activity instance classes
        And User selects 'NumericFindings' as one of non-standard activity instance classes
        And User selects 'Events' as one of non-standard activity instance classes
        And User selects 'CategoricFindings' as one of non-standard activity instance classes
        And User exapnds-collapse list of available activity instance classes
        And Non-standard variable code is set as random value
        And Non-standard variable label is set as 'NSV E2E label'
        And Non-standard variable role is selected as 'Identifier'
        And Non-standard variable data type is selected as 'CT Term'
        And Non-standard variable length is set as '30'
        And Form save button is clicked
        Then Non-standard variable is searched by code and found
        And Non-standard variable 'Multiple' is visible as 'Yes' in the table
        And Non-standard variable 'CDISC defined' is visible as 'No' in the table
        And Non-standard variable 'Semantic data type' is visible as 'CT Term' in the table
        And Non-standard variable 'Length' is visible as '30' in the table
        And Non-standard variable code, label and name are visible in the table with correct values
        And User goes to non-standard variable overview page by clicking its name
        And Non-standard variable sentence case name has correct value in the overview page
        And Non-standard variable label has correct value in the overview page
        And Non-standard variable is connected to Activity Instance Class 'NumericFindings'
        And Non-standard variable is connected to Activity Instance Class 'Events'
        And Non-standard variable is connected to Activity Instance Class 'CategoricFindings'

    Scenario: [Create][Code uniqueness check] User must not be able to use already used code for non-standard variable
        Given The '/library/activities/non-standard-variables' page is opened
        And The plus button is clicked
        When Non-standard variable activity instance class value is selected as 'NumericFindings'
        And Non-standard variable code is set with already used value
        And Non-standard variable label is set as 'NSV E2E label'
        And Non-standard variable role is selected as 'Identifier'
        And Non-standard variable data type is selected as 'CT Term'
        And Non-standard variable length is set as '30'
        And Form save button is clicked
        Then Warning is displayed that the non-standad variable code is already used

    Scenario: [Create][Fields validation] User must not be able to save without providing values to all required fields during non-standard variable creation
        Given The '/library/activities/non-standard-variables' page is opened
        And The plus button is clicked
        And Non-standard variable activity instane class is cleared
        And Non-standard variable role is cleared
        And Form save button is clicked
        Then Warning is displayed that filed 'activity-instance-class' is required for non-standard variable
        And Warning is displayed that filed 'code' is required for non-standard variable
        And Warning is displayed that filed 'label' is required for non-standard variable
        And Warning is displayed that filed 'name' is required for non-standard variable
        And Warning is displayed that filed 'role' is required for non-standard variable
        And Warning is displayed that filed 'data-type' is required for non-standard variable
        And Warning is displayed that filed 'length' is required for non-standard variable

    Scenario: [Create][Positve case][Optional fields] User must be able to add a new non-standard variable with all optional fields
        Given The '/library/activities/non-standard-variables' page is opened
        And The plus button is clicked
        When Non-standard variable activity instance class value is selected as 'Interventions'
        And Non-standard variable code is set as random value
        And Non-standard variable label is set as 'NSV E2E label'
        And Non-standard variable role is selected as 'Identifier'
        And Non-standard variable data type is selected as 'CT Term'
        And Non-standard variable length is set as '30'
        And Non-standard variable optional input field 'Add algorithm (optional)' is set to 'E2E algorithm'
        And Non-standard variable optional dropdown field 'Default origin type (optional)' is set to 'Other'
        And Non-standard variable optional dropdown field 'Default origin source (optional)' is set to 'Clinical Study Sponsor'
        And Non-standard variable optional input field 'Definition (optional)' is set to 'E2E definition'
        And Non-standard variable optional input field 'Derivation rule (optional)' is set to 'E2E derivation'
        And Non-standard variable optional input field 'NCI Code (optional)' is set to 'E2E nci code'
        And Non-standard variable optional input field 'NCI Concept Name (optional)' is set to 'E2E nci name'
        And Form save button is clicked
        Then Non-standard variable is searched by code and found
        And Non-standard variable 'NCI code' is visible as 'E2E nci code' in the table
        And Non-standard variable 'NCI concept name' is visible as 'E2E nci name' in the table
        And Non-standard variable 'Multiple' is visible as 'No' in the table
        And Non-standard variable 'CDISC defined' is visible as 'No' in the table
        And Non-standard variable 'Semantic data type' is visible as 'CT Term' in the table
        And Non-standard variable 'Length' is visible as '30' in the table
        And Non-standard variable 'Origin type' is visible as 'Other' in the table
        And Non-standard variable 'Origin source' is visible as 'Clinical Study Sponsor' in the table
        And Non-standard variable 'Algorithm' is visible as 'E2E algorithm' in the table
        And Non-standard variable 'Definition' is visible as 'E2E definition' in the table
        And Non-standard variable 'Derivation rule' is visible as 'E2E derivation' in the table
        And Non-standard variable code, label and name are visible in the table with correct values
        And User goes to non-standard variable overview page by clicking its name
        And Non-standard variable sentence case name has correct value in the overview page
        And Non-standard variable label has correct value in the overview page
        And Non-standard variable is connected to Activity Instance Class 'Interventions'
        And Non-standard variable 'NCI Concept ID' has value 'E2E nci code' in the overview page
        And Non-standard variable 'NCI Concept Name' has value 'E2E nci name' in the overview page
        And Non-standard variable 'Definition' has value 'E2E definition' in the overview page

    Scenario: [Approve] User must be able to approve non-standard variable
        Given The '/library/activities/non-standard-variables' page is opened
        Then Non-standard variable is searched by code and found
        When The 'Approve' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'

    Scenario: [Inactivate] User must be able to retire non-standard variable
        Given The '/library/activities/non-standard-variables' page is opened
        Then Non-standard variable is searched by code and found
        When The 'Inactivate' option is clicked from the three dot menu list
        Then The item has status 'Retired' and version '1.0'
    
    Scenario: [Reactivate] User must be able to reactivate non-standard variable
        Given The '/library/activities/non-standard-variables' page is opened
        Then Non-standard variable is searched by code and found
        When The 'Reactivate' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'

    Scenario: [New version] User must be able to reactivate non-standard variable
        Given The '/library/activities/non-standard-variables' page is opened
        Then Non-standard variable is searched by code and found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'

    Scenario: [Edit] User must be able to edit non-standard variable
        Given The '/library/activities/non-standard-variables' page is opened
        Then Non-standard variable is searched by code and found
        When The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        And Non-standard variable activity instance class value is selected as 'NumericFindings'
        And Non-standard variable code is set as random value
        And Non-standard variable label is set as 'NSV E2E label update'
        And Non-standard variable role is selected as 'Grouping Qualifier'
        And Non-standard variable data type is selected as 'Text'
        And User waits for 1 seconds
        And Non-standard variable length is set as '150'
        And Non-standard variable optional input field 'Add algorithm (optional)' is set to 'E2E algorithm update'
        And Non-standard variable optional dropdown field 'Default origin type (optional)' is set to 'Derived Value'
        And Non-standard variable optional dropdown field 'Default origin source (optional)' is set to 'Vendor'
        And Non-standard variable optional input field 'Definition (optional)' is set to 'E2E definition update'
        And Non-standard variable optional input field 'Derivation rule (optional)' is set to 'E2E derivation update'
        And Non-standard variable optional input field 'NCI Code (optional)' is set to 'E2E nci code update'
        And Non-standard variable optional input field 'NCI Concept Name (optional)' is set to 'E2E nci name update'
        And Non-standard variable optional input field 'Change description' is set to 'test'
        And Form save button is clicked
        Then Non-standard variable is searched by code and found
        Then The item has status 'Draft' and version '1.2'
        And Non-standard variable 'NCI code' is visible as 'E2E nci code update' in the table
        And Non-standard variable 'NCI concept name' is visible as 'E2E nci name update' in the table
        And Non-standard variable 'Multiple' is visible as 'No' in the table
        And Non-standard variable 'CDISC defined' is visible as 'No' in the table
        And Non-standard variable 'Semantic data type' is visible as 'Text' in the table
        And Non-standard variable 'Length' is visible as '150' in the table
        And Non-standard variable 'Origin type' is visible as 'Derived Value' in the table
        And Non-standard variable 'Origin source' is visible as 'Vendor' in the table
        And Non-standard variable 'Algorithm' is visible as 'E2E algorithm update' in the table
        And Non-standard variable 'Definition' is visible as 'E2E definition update' in the table
        And Non-standard variable 'Derivation rule' is visible as 'E2E derivation update' in the table
        And Non-standard variable code, label and name are visible in the table with correct values
        And User goes to non-standard variable overview page by clicking its name
        And Non-standard variable sentence case name has correct value in the overview page
        And Non-standard variable label has correct value in the overview page
        And Non-standard variable is connected to Activity Instance Class 'NumericFindings'
        And Non-standard variable 'NCI Concept ID' has value 'E2E nci code update' in the overview page
        And Non-standard variable 'NCI Concept Name' has value 'E2E nci name update' in the overview page
        And Non-standard variable 'Definition' has value 'E2E definition update' in the overview page

    Scenario: [Delete][Positve case] User must be able to delete a new non-standard variable
        Given The '/library/activities/non-standard-variables' page is opened
        And The plus button is clicked
        When Non-standard variable activity instance class value is selected as 'NumericFindings'
        And Non-standard variable code is set as random value
        And Non-standard variable label is set as 'NSV E2E label'
        And Non-standard variable role is selected as 'Identifier'
        And Non-standard variable data type is selected as 'CT Term'
        And Non-standard variable length is set as '30'
        And Form save button is clicked
        Then Non-standard variable is searched by code and found
        When The 'Delete' option is clicked from the three dot menu list
        And Action is confirmed by clicking continue
        Then Non-standard variable is searched by code and not found
