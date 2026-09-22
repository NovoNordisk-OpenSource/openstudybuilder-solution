@REQ_ID:1074260
Feature: Studies - Define Study - Study Data Specifications - Study Activity Instances

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study activity instances.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'
 
    Scenario: [Test data] User creates test data via API and sets feature flags
        And [API] The feature flag 'streamline_placeholder_activities' is enabled
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        And [API] The epoch with type 'Treatment' and subtype 'Intervention' exists in selected study
        And [API] All visit groups uids are fetched
        And [API] All visit groups are removed
        And [API] Study vists uids are fetched for selected study
        When [API] Study visits in selected study are cleaned-up
        And [API] The static visit data is fetched
        Given [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2
        And [API] All Activities are deleted from selected study

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to Study Data Specification page for selected study when using side menu
        And The '/studies' page is opened
        When The 'Data Specifications' submenu is clicked in the 'Define Study' section
        Then The current URL is '/data_specifications/instances'

    @smoke_test
    Scenario: [Table][Columns][Names] User must be able to see the Study Activity Instances table with options listed in this scenario
        Given The page 'data_specifications/instances' is opened for current study
        Then A table is visible with following headers
            | headers           |
            | Library           |
            | SoA group         |
            | Activity group    |
            | Activity subgroup |
            | Activity          |
            | Data collection   |
            | Activity instance |
            | Topic code        |
            | Test name         |
            | Specimen          |
            | Standard unit     |
            | State/Actions     |
            | ADaM param code   |
            | Important         |

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option for Study Activity Instances table
        Given The page 'data_specifications/instances' is opened for current study
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Options] User must be able to see the Study Activity Instances table with options listed in the scenario
        Given The page 'data_specifications/instances' is opened for current study
        Then A table is visible with following options
            | options                                            |
            | filters-button                                     |
            | columns-layout-button                              |
            | table-export-button                                |
            | select-rows                                        |
            | search-field                                       |
            | History                                            |

    Scenario: [Placeholder][Submitted] User must be able to see submitted placeholder in the Activity Instances table
        And [API] Get SoA Group 'BIOMARKERS' id
        When [API] Create Submitted Requested Activity
        And [API] Requested Activity is added to the study
        Given The page 'data_specifications/instances' is opened for current study
        And The Study Activity is found
        And Activity name column contains value 'Placeholder_Submitted_'
        And Activity instance column is empty
        And The Study Activity Library is displayed as 'Requested' in the table
        Then The activity state is 'Not applicable'
        And The reviewed checkbox is disabled

    Scenario: [Placeholder][Not-Submitted] User must be able to see not-submitted placeholder in the Activity Instances table
        And [API] Get SoA Group 'BIOMARKERS' id
        When [API] Create Unsubmitted Requested Activity
        And [API] Requested Activity is added to the study
        Given The page 'data_specifications/instances' is opened for current study
        And The Study Activity is found
        And Activity name column contains value 'Placeholder_Unsubmitted_'
        And Activity instance column is empty
        And The Study Activity Library is displayed as 'Requested' in the table
        Then The activity state is 'Not applicable'
        And The reviewed checkbox is disabled

    Scenario: User must be able to selected one activity instance for study activity and save without review
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        Given The page 'data_specifications/instances' is opened for current study
        When The Study Activity is found
        And The 'Edit Activity - Instance relationship' option is clicked from the three dot menu list
        And The user selects activity instance
        And The 'cancel-button' button is clicked
        Then The activity state is 'Add instance'

    Scenario: User must be able to selected one activity instance for study activity and save as reviewed
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        Given The page 'data_specifications/instances' is opened for current study
        When The Study Activity is found
        And The 'Edit Activity - Instance relationship' option is clicked from the three dot menu list
        And The user selects activity instance
        And The 'Save as reviewed' is clicked during review
        Then The activity state is 'Reviewed'

    Scenario: User must be able to selected multiple activity instances for study activity save without review
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        Given The page 'data_specifications/instances' is opened for current study
        When The Study Activity is found
        And The 'Edit Activity - Instance relationship' option is clicked from the three dot menu list
        And The user selects multiple activity instances
        And The 'cancel-button' button is clicked
        Then The activity state is 'Add instance'

    Scenario: User must be able to selected multiple activity instances for study activity and save as reviewed
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        Given The page 'data_specifications/instances' is opened for current study
        When The Study Activity is found
        And The 'Edit Activity - Instance relationship' option is clicked from the three dot menu list
        And The user selects multiple activity instances
        And The 'Save as reviewed' is clicked during review
        Then The activity state is 'Reviewed'
        # And The instance is linked to that activity

    Scenario: User must be able to delete one of multiple activity instances from selected study activity
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        Given The page 'data_specifications/instances' is opened for current study
        When The Study Activity is found
        And The 'Edit Activity - Instance relationship' option is clicked from the three dot menu list
        And The user selects multiple activity instances
        And The 'save-button' button is clicked
        And The user removes the additional activities
        Then The pop up displays 'Study Activity Instance deleted'

    Scenario: User must be presented with 'Not applicable' for every non-data collection study activity
        And [API] No data collection Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        Given The page 'data_specifications/instances' is opened for current study
        When The Study Activity is found
        Then The activity state is 'Not applicable'

    @pending_implementation
    Scenario: User must be presented with 'Review needed' when activity instace selected for study activity are in undefined state
        Given The study activity in undefined state is presented in the study
        Given The page 'data_specifications/instances' is opened for current study
        Then The activity state is 'Review needed'

    Scenario: User must be presented with 'Review needed' when activity instace selected for study activity are in default state
        And [API] Study Activity is created and approved
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'true' exists
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        Given The page 'data_specifications/instances' is opened for current study
        When The Study Activity is found
        Then The activity state is 'Review needed'

    Scenario: User must be presented with 'Review not needed' and checked Reviewed checkbox when activity instance selected for study activity is mandatory
        And [API] Study Activity is created and approved
        And The activity instance with data-sharing set to 'false', required for activity set to 'true' and default for activity set to 'false' exists
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        Given The page 'data_specifications/instances' is opened for current study
        When The Study Activity is found
        Then The activity state is 'Review not needed'
        And The reviewed checkbox is displayed as checked

    Scenario: User must be presented with 'Add instance' and disabled Reviewed checkbox when study activity is not linked to any activity instance
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        Given The page 'data_specifications/instances' is opened for current study
        When The Study Activity is found
        Then The activity state is 'Add instance'
        And The reviewed checkbox is disabled

    Scenario: User must be presented with 'Remove instance' and disabled Reviewed checkbox when study activity has more linked activity instances than allowed for that study activity
        And [API] Study Activity with no mutliple instances allowed is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        Given The page 'data_specifications/instances' is opened for current study
        When The Study Activity is found
        And The 'Edit Activity - Instance relationship' option is clicked from the three dot menu list
        And The user selects multiple activity instances
        And Form save button is clicked
        Then The activity state is 'Remove instance'
        And The reviewed checkbox is disabled 
        
    Scenario: Reviewed checkbox must be disabled for activity in 'Not applicable' state
        And [API] No data collection Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        Given The page 'data_specifications/instances' is opened for current study
        When The Study Activity is found
        Then The activity state is 'Not applicable'
        And The reviewed checkbox is disabled 

    Scenario: User must be able to review study activity in 'Review needed' state
        And [API] Study Activity is created and approved
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'true' exists
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        Given The page 'data_specifications/instances' is opened for current study
        When The Study Activity is found
        Then The activity state is 'Review needed'
        When The user checks the reviewed checkbox
        Then The activity state is 'Reviewed'
    
    Scenario: Study activity must be put into 'Review needed' state when user unchecks 'Reviewed' checkbox for activity in 'Review not needed' state
        And [API] Study Activity is created and approved
        And The activity instance with data-sharing set to 'false', required for activity set to 'true' and default for activity set to 'false' exists
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        Given The page 'data_specifications/instances' is opened for current study
        When The Study Activity is found
        Then The activity state is 'Review not needed'
        And The user unchecks the reviewed checkbox
        Then The activity state is 'Review needed'

    Scenario: Study activity must be put into 'Review needed' state when user unchecks 'Reviewed' checkbox for activity in 'Reviewed' state
        And [API] Study Activity is created and approved
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        Given The page 'data_specifications/instances' is opened for current study
        When The Study Activity is found
        And The user checks the reviewed checkbox
        Then The activity state is 'Reviewed'
        And The user unchecks the reviewed checkbox
        Then The activity state is 'Review needed'

    @pending_implementation
    Scenario: Study activity must be set as 'Review needed' after too many instances has been removed and undefined was true
        Given The study activity with multiple activity instances and undefined state is present in selected study
        Given The page 'data_specifications/instances' is opened for current study
        And The user clicks 'Edit' for that activity
        And The user removes all activity instances selection
        Then The activity state is 'Review needed'

    @pending_implementation
    Scenario: Study activity must be set as 'Review needed' after too many instances has been removed and was set as default instance
        Given The default state study activity with multiple activity instances is present in selected study
        Given The page 'data_specifications/instances' is opened for current study
        And The user clicks 'Edit' for that activity
        And The user removes all activity instances selection
        Then The activity state is 'Review needed'

    @pending_implementation
    Scenario: Study activity must be set as 'Review not needed' after too many instances has been removed and mandatory was true
        Given The mandatory study activity with multiple activity instances is present in selected study
        Given The page 'data_specifications/instances' is opened for current study
        And The user clicks 'Edit' for that activity
        And The user removes all activity instances selection
        Then The activity state is 'Review needed'

    @pending_implementation
    Scenario: Study activity must be set as 'Review needed' after necessary instance has been added and undefined was true
        Given The study activity without activity instances and undefined status is present in selected study
        Given The page 'data_specifications/instances' is opened for current study
        And The user clicks 'Edit' for that activity
        And The user selects activity instance
        Then The activity state is 'Review needed'

    @pending_implementation
    Scenario: Study activity must be set as 'Review needed' after necessary instance has been added and was in default state
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'true' exists
        Given The page 'data_specifications/instances' is opened for current study
        When The Study Activity is found
        And The 'Edit Activity - Instance relationship' option is clicked from the three dot menu list
        And The user selects activity instance
        And The 'Save as reviewed' is clicked during review
        Then The activity state is 'Review needed'

    Scenario: Study activity must be set as 'Review not needed' after necessary instance has been added and mandatory was true
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And The activity instance with data-sharing set to 'false', required for activity set to 'true' and default for activity set to 'false' exists
        Given The page 'data_specifications/instances' is opened for current study
        When The Study Activity is found
        And The 'Edit Activity - Instance relationship' option is clicked from the three dot menu list
        And The user selects activity instance
        And The 'Save as reviewed' is clicked during review
        Then The activity state is 'Review not needed'

    Scenario: User must not be presented with 'Save as reviewed' when activity instances has not been selected
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And The activity instance with data-sharing set to 'false', required for activity set to 'true' and default for activity set to 'false' exists
        Given The page 'data_specifications/instances' is opened for current study
        When The Study Activity is found
        And The 'Edit Activity - Instance relationship' option is clicked from the three dot menu list
        Then The button 'Save as reviewed' is disabled

    @pending_implementation
    Scenario: User must not be presented with 'Save as reviewed' when activity has 'Remove instance' status
        Given The study activity in 'Remove instance' state exists for the study
        Given The page 'data_specifications/instances' is opened for current study
        And The user clicks 'Edit' for that activity
        Then The button 'Save as reviewed' is not present

    Scenario: User must not be presented with 'Save as reviewed' for activity in state 'Not applicable'
        And [API] No data collection Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        Given The page 'data_specifications/instances' is opened for current study
        When The Study Activity is found
        Then The activity state is 'Not applicable'
        And The 'Edit Activity - Instance relationship' option is clicked from the three dot menu list
        Then The button 'Save as reviewed' is disabled

    Scenario: User must be presented with red exclamation mark icon when a change has occured for instance name
        Given [API] Study Activity is created and approved
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And [API] Activity Instance new version is created
        And [API] Activity instance is updated with new name
        Given The page 'data_specifications/instances' is opened for current study
        And The Study Activity is found
        Then The red alert badge is present

    Scenario: User must be presented with yellow exclamation mark when study activity updates has been declined
        Given [API] Study Activity is created and approved
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And [API] Activity Instance new version is created
        And [API] Activity instance is updated with new name
        Given The page 'data_specifications/instances' is opened for current study
        And The Study Activity is found
        And The user declines the activity instance changes
        Then The yellow alert badge is present

    Scenario: Red exclamation mark must be removed when study activity updates has been accepted 
        Given [API] Study Activity is created and approved
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And [API] Activity Instance new version is created
        And [API] Activity instance is updated with new name
        Given The page 'data_specifications/instances' is opened for current study
        And The Study Activity is found
        And The user accepts the activity instance changes
        Then The red alert badge is not present

    Scenario: Study activity is set to 'Review needed' when a change has occured for instance name
        Given [API] Study Activity is created and approved
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And [API] Activity Instance new version is created
        And [API] Activity instance is updated with new name
        Given The page 'data_specifications/instances' is opened for current study
        And The Study Activity is found
        Then The activity state is 'Review needed'

    Scenario: Study activity is set to 'Review needed' when the instance has been retired
        And [API] Study Activity is created and approved
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And [API] Activity Instance is inactivated
        Given The page 'data_specifications/instances' is opened for current study
        And The Study Activity is found
        Then The activity state is 'Review needed'

    Scenario: User must be able to mark study as 'Reviewed' when accepting all changes to instance
        Given [API] Study Activity is created and approved
        And The activity instance with data-sharing set to 'false', required for activity set to 'false' and default for activity set to 'false' exists
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And [API] Activity Instance new version is created
        And [API] Activity instance is updated with new name
        Given The page 'data_specifications/instances' is opened for current study
        And The Study Activity is found
        And The user accepts the activity instance changes
        Then The red alert badge is not present
        Then The activity state is 'Reviewed'

    @pending_implementation
    Scenario: User must be able to review instance updates
        Given The study activity with linked activity instance exists for the study
        And The activity instance has been edited
        Given The page 'data_specifications/instances' is opened for current study
        And The user opens the review instance updates view
        Then The changes are presented to the user

    @pending_implementation
    Scenario: Bulk action - User must be able to mark study as 'Reviewed' when accepting all changes to instance
        Given The study activity with linked activity instance exists for the study
        And The activity instance topic code has been edited
        Given The page 'data_specifications/instances' is opened for current study
        And The user accepts the changes
        Then The activity state is 'Reviewed'

    @pending_implementation
    Scenario: Bulk action - User must be able to review instance updates
        Given The study activity with linked activity instance exists for the study
        And The activity instance has been edited
        Given The page 'data_specifications/instances' is opened for current study
        And The user opens the review instance updates view
        Then The changes are presented to the user

    @pending_implementation
    Scenario: Bulk action - User must not be presented with review instance updates when no updates are present
        Given The study activity with linked activity instance exists for the study
        And The activity instance has not been edited
        Given The page 'data_specifications/instances' is opened for current study
        Then The 'Review instance changes' nbtton is not present

    @pending_implementation
    Scenario: Bulk action - User must be presented with 'accept' button when instance name has been updated
        Given The study activity with linked activity instance exists for the study
        And The activity instance name has been edited
        Given The page 'data_specifications/instances' is opened for current study
        And The user accepts the changes
        Then The changes are applied to study activity

    @pending_implementation
    Scenario: Bulk action - User must be presented with 'accept' button when instance class has been updated
        Given The study activity with linked activity instance exists for the study
        And The activity instance class has been edited
        Given The page 'data_specifications/instances' is opened for current study
        And The user accepts the changes
        Then The changes are applied to study activity

    @pending_implementation
    Scenario: Bulk action - User must be presented with 'accept' button when instance topic code has been updated
        Given The study activity with linked activity instance exists for the study
        And The activity instance topic code has been edited
        Given The page 'data_specifications/instances' is opened for current study
        And The user accepts the changes
        Then The changes are applied to study activity

    @pending_implementation
    Scenario: Bulk action - User must be presented with 'declined' button when instance name has been updated
        Given The study activity with linked activity instance exists for the study
        And The activity instance name has been edited
        Given The page 'data_specifications/instances' is opened for current study
        And The user declines the changes
        Then The changes are not applied to study activity

    @pending_implementation
    Scenario: Bulk action - User must be presented with 'declined' button when instance class has been updated
        Given The study activity with linked activity instance exists for the study
        And The activity instance class has been edited
        Given The page 'data_specifications/instances' is opened for current study
        And The user declines the changes
        Then The changes are not applied to study activity

    @pending_implementation
    Scenario: Bulk action - User must be presented with 'declined' button when instance topic code has been updated
        Given The study activity with linked activity instance exists for the study
        And The activity instance topic code has been edited
        Given The page 'data_specifications/instances' is opened for current study
        And The user declines the changes
        Then The changes are not applied to study activity

    @pending_implementation
    Scenario: Bulk action - User must be presented with 'decline' button when instance is retired
        Given The study activity with linked activity instance exists for the study
        And The activity instance has been retired
        Given The page 'data_specifications/instances' is opened for current study
        And The user declines the changes
        Then The changes are not applied to study activity

    @pending_implementation
    Scenario: Bulk action - User must not be presented with 'accept' button when instance is retired
        Given The study activity with linked activity instance exists for the study
        And The activity instance has been retired
        Given The page 'data_specifications/instances' is opened for current study
        And The user accepts the changes
        Then The changes are applied to study activity

    Scenario Outline: [Table][Filtering] User must be able to filter the Study Activity Instances table by text fields
        Given The page 'data_specifications/instances' is opened for current study
        When The user filters field '<name>'
        Then The table is filtered correctly
        Examples:
        | name               |
        | Library           |
        | SoA group         |
        | Activity group    |
        | Activity subgroup |
        | Activity          |
        | Data collection   |
        | Activity instance |
        | Topic code        |
        #| Test name         |
        #| Specimen          |
        #| Standard unit     |
        | State/Actions     |
        | ADaM param code   |
        | Important         |