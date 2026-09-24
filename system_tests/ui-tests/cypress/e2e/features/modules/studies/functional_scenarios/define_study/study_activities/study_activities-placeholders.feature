    @REQ_ID:1074260
    Feature: Studies - Define Study - Study Activities - Study Activities Placeholders

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study activities.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    Scenario: [TestData] Old placeholder activity workflow feature flag is disabled and all activities are deleted from study
        Then [API] The feature flag 'streamline_placeholder_activities' is enabled
        And [API] All Activities are deleted from selected study

    @smoke_test
    Scenario: [Create][Placeholder] User must be able to create a Study Activity placeholder as an activity concept request
        Given The page 'activities/list' is opened for current study
        When Study activity add button is clicked
        And Activity from placeholder is selected
        And Form continue button is clicked
        And User sets Activity Placeholder name
        And User selects Activity SoA group as 'INFORMED CONSENT'
        And User selects first group for placeholder
        And User selects first subgroup for placeholder
        And User sets Activity rationale
        And User gets selected activity group name
        And User gets selected activity subgroup name
        And Form save button is clicked
        And The form is no longer available
        And The Study Activity is found
        Then The Study Activity name, group and subgroup are visible in table
        And The Study Activity Library is displayed as 'Requested' in the table
        And The Study Activity SoA Group is displayed as 'INFORMED CONSENT' in the table

    Scenario: [Actions][Delete][Placeholder] User must be able to delete a Study Activity placeholder
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        When The 'Remove Activity' option is clicked from the three dot menu list
        And Action is confirmed by clicking continue
        Then The Study Activity is not found

    Scenario: [Create][Placeholder] User must be able to create a Study Activity placeholder with already existing name if group/subgroup is different
        Given The page 'activities/list' is opened for current study
        When Study activity add button is clicked
        And Activity from placeholder is selected
        And Form continue button is clicked
        And User sets Activity Placeholder name
        When User selects first group for placeholder
        And User selects first subgroup for placeholder
        And User selects Activity SoA group as 'EFFICACY'
        And User sets Activity rationale
        And Form save button is clicked
        Then The pop up displays 'Study activity added'
        When Study activity add button is clicked
        And Activity from placeholder is selected
        And Form continue button is clicked
        And User sets Activity Placeholder name that is already used
        When User selects first group for placeholder
        And User selects second subgroup for placeholder
        And User selects Activity SoA group as 'EFFICACY'
        And User sets Activity rationale
        And Form save button is clicked
        Then The pop up displays 'Study activity added'
        When Study activity add button is clicked
        And Activity from placeholder is selected
        And Form continue button is clicked
        And User sets Activity Placeholder name that is already used
        When User selects second group for placeholder
        And User selects first subgroup for placeholder
        And User selects Activity SoA group as 'EFFICACY'
        And User sets Activity rationale
        And Form save button is clicked
        Then The pop up displays 'Study activity added'

    Scenario: [Create][Placeholder] User must be able to reuse already existing placeholder
        Given User selects study with id 'CDISC DEV-9877'
        When The page 'activities/list' is opened for current study
        When Study activity add button is clicked
        And Activity from placeholder is selected
        And Form continue button is clicked
        And User sets Activity Placeholder name that is already used
        When User selects first group for placeholder
        And User selects first subgroup for placeholder
        And User selects Activity SoA group as 'EFFICACY'
        And User sets Activity rationale
        And Action is confirmed by clicking save
        Then Pop-up displays that there is already existing placeholder with such name, group and subgroup
        And Action is confirmed by clicking continue
        And The form is no longer available
        And The Study Activity is found

    Scenario: [Actions][Edit][version 0.1][Placeholder] User must be able to edit a Study Activity placeholder
        And [API] Get SoA Group 'BIOMARKERS' id
        When [API] Create Submitted Requested Activity
        And [API] Requested Activity is added to the study
        Given The page 'activities/list' is opened for current study
        And The Study Activity is found
        When The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        When User edits Activity SoA group to 'EFFICACY'
        And Modal window 'Save' button is clicked
        And The form is no longer available
        Then The pop up displays 'Study activity updated'
        And The Study Activity is found
        Then The Study Activity SoA Group is displayed as 'EFFICACY' in the table

    @BUG_ID:2722627
    Scenario: [Actions][Edit][version 0.1][Placeholder] User must be able to edit data collection flag
        Given The page 'activities/list' is opened for current study
        When Study activity add button is clicked
        And Activity from placeholder is selected
        And Form continue button is clicked
        And User sets Activity Placeholder name
        And User selects Activity SoA group as 'INFORMED CONSENT'
        And User selects first group for placeholder
        And User selects first subgroup for placeholder
        And User sets Activity rationale
        And Data collection flag is unchecked
        And Form save button is clicked
        And The form is no longer available
        And The Study Activity is found
        When The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        And Data collection flag is checked
        And Modal window 'Save' button is clicked
        And The form is no longer available
        Then The pop up displays 'Study activity updated'
        And The Study Activity is found
        Then The Study Activity Data Collection is displayed as 'Yes' in the table

    Scenario: [Create][Mandatory fields][Placeholder] User must not be able to create Study Activity placeholder without SoA group selected
       Given The page 'activities/list' is opened for current study
        And Study activity add button is clicked
        And Activity from placeholder is selected
        And Form continue button is clicked
        And User sets Activity Placeholder name
        And User sets Activity rationale
        And Form save button is clicked
        Then The validation appears under empty SoA group selection
