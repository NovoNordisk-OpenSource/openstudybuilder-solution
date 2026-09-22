@REQ_ID:XXX
Feature: Studies - Define Study - Study Activity Instances - E2E verification

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9844'

    Scenario: [Test data] Study data is prepared before start of tests
        And [API] All visit groups uids are fetched
        And [API] All visit groups are removed
        When [API] Study vists uids are fetched for selected study
        When [API] Study visits in selected study are cleaned-up
        And [API] All Activities fotnotes are deleted from selected study
        Given [API] All Activities are deleted from selected study
        And [API] All epochs assigned to the selected study are fetched
        And [API] All epochs assigned to the selected study are deleted
        Given [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        And [API] The epoch with type 'Treatment' and subtype 'Intervention' exists in selected study
        And [API] The static visit data is fetched
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Get class uid for activity instance creation
        And [API] Group and subgroup are created and approved to be used for activity creation
        And [API] Activity with data collection set to 1 and 'FirstActivity' included in the name is created and approved
        And [API] The activity instance with name 'FirstInstance_API_' and isRequriedForActivity set to true is created and approved
        And [API] Activity is added to the selected study
        And [API] Activity is assigned to the visit 0 in selected study
        And [API] Activity is assigned to the visit 1 in selected study
        And [API] Activity with data collection set to 1 and 'SecondActivity' included in the name is created and approved
        And [API] The activity instance with name 'SecondInstance_API_' and isRequriedForActivity set to true is created and approved
        And [API] Activity is added to the selected study
        And [API] Activity is assigned to the visit 1 in selected study
        And [API] Activity with data collection set to 1 and 'MissingInstance' included in the name is created and approved
        And [API] Activity is added to the selected study
        And [API] Activity is assigned to the visit 0 in selected study
        And [API] Activity with data collection set to 0 and 'NoDataCollection' included in the name is created and approved
        And [API] Activity is added to the selected study
        And [API] Activity is assigned to the visit 0 in selected study
        And [API] Activity with data collection set to 1 and 'RequiredForActivity' included in the name is created and approved
        And [API] The activity instance with isRequriedForActivity set to true is created and approved
        And [API] Activity is added to the selected study
        And [API] Activity with data collection set to 1 and 'DefaultForActivity' included in the name is created and approved
        And [API] The activity instance with isDefaultForActivity set to true is created and approved
        And [API] Activity is added to the selected study
        And [API] User gets data of activity with name 'Albumin', group 'Laboratory Assessments', subgroup 'Urinalysis'
        And [API] Activity is added to the selected study
        And [API] Activity is assigned to the visit 0 in selected study
        And [API] Activity is assigned to the visit 1 in selected study
        And [API] User gets data of activity with name 'Albumin', group 'Laboratory Assessments', subgroup 'Biochemistry'
        And [API] Activity is added to the selected study
        And [API] Activity is assigned to the visit 0 in selected study
        And [API] Activity is assigned to the visit 1 in selected study
        And [API] Get SoA Group 'BIOMARKERS' id
        When [API] Create Submitted Requested Activity
        And [API] Requested Activity is added to the study
        When [API] Create Unsubmitted Requested Activity
        And [API] Requested Activity is added to the study

    Scenario: [Study Activity Instances Table] User must be able to see all Study Activities added to the Study, including placeholders
        Given The page 'data_specifications/instances' is opened for current study
        When User searches for 'Placeholder_Submitted_'
        And Activity name column contains value 'Placeholder_Submitted_'
        And Activity instance column is empty
        And The Study Activity Library is displayed as 'Requested' in the table
        And The activity state is 'Not applicable'
        And The reviewed checkbox is disabled
        And The reviewed checkbox is displayed as unchecked
        And SoA Group is set to 'BIOMARKERS'
        And Data collection column is set to 'No'
        When User searches for 'Placeholder_Unsubmitted_'
        And Activity name column contains value 'Placeholder_Unsubmitted_'
        And Activity instance column is empty
        And The Study Activity Library is displayed as 'Requested' in the table
        And The activity state is 'Not applicable'
        And The reviewed checkbox is disabled
        And The reviewed checkbox is displayed as unchecked
        And SoA Group is set to 'BIOMARKERS'
        And Data collection column is set to 'No'
        When User searches for 'Urinalysis'
        Then Activity name column contains value 'Albumin'
        And Activity instance column contains value 'Albumin Urine'
        And The Study Activity Library is displayed as 'Sponsor' in the table
        And The activity state is 'Review needed'
        And The reviewed checkbox is enabled
        And The reviewed checkbox is displayed as unchecked
        And SoA Group is set to 'INFORMED CONSENT'
        And Data collection column is set to 'Yes'
        When User searches for 'Biochemistry'
        Then Activity name column contains value 'Albumin'
        And Activity instance column contains value 'Albumin Serum'
        And The Study Activity Library is displayed as 'Sponsor' in the table
        And The activity state is 'Review needed'
        And The reviewed checkbox is enabled
        And The reviewed checkbox is displayed as unchecked
        And SoA Group is set to 'INFORMED CONSENT'
        And Data collection column is set to 'Yes'
        When User searches for 'DefaultForActivity'
        Then Activity name column contains value 'DefaultForActivity'
        And Activity instance column contains value 'API_ActivityInstance'
        And The Study Activity Library is displayed as 'Sponsor' in the table
        And The activity state is 'Review needed'
        And The reviewed checkbox is enabled
        And The reviewed checkbox is displayed as unchecked
        And SoA Group is set to 'INFORMED CONSENT'
        And Data collection column is set to 'Yes'
        When User searches for 'RequiredForActivity'
        Then Activity name column contains value 'RequiredForActivity'
        And Activity instance column contains value 'API_ActivityInstance'
        And The Study Activity Library is displayed as 'Sponsor' in the table
        And The activity state is 'Review not needed'
        And The reviewed checkbox is enabled
        And The reviewed checkbox is displayed as checked
        And SoA Group is set to 'INFORMED CONSENT'
        And Data collection column is set to 'Yes'
        When User searches for 'NoDataCollection'
        Then Activity name column contains value 'NoDataCollection'
        And Activity instance column is empty
        And The Study Activity Library is displayed as 'Sponsor' in the table
        And The activity state is 'Not applicable'
        And The reviewed checkbox is disabled
        And The reviewed checkbox is displayed as unchecked
        And SoA Group is set to 'INFORMED CONSENT'
        And Data collection column is set to 'No'
        When User searches for 'MissingInstance'
        Then Activity name column contains value 'MissingInstance'
        And Activity instance column is empty
        And The Study Activity Library is displayed as 'Sponsor' in the table
        And The activity state is 'Add instance'
        And The reviewed checkbox is disabled
        And The reviewed checkbox is displayed as unchecked
        And SoA Group is set to 'INFORMED CONSENT'
        And Data collection column is set to 'Yes'
        When User searches for 'FirstActivity'
        Then Activity name column contains value 'FirstActivity'
        And Activity instance column contains value 'FirstInstance_API_'
        And The Study Activity Library is displayed as 'Sponsor' in the table
        And The activity state is 'Review not needed'
        And The reviewed checkbox is enabled
        And The reviewed checkbox is displayed as checked
        And SoA Group is set to 'INFORMED CONSENT'
        And Data collection column is set to 'Yes'
        When User searches for 'SecondActivity'
        Then Activity name column contains value 'SecondActivity'
        And Activity instance column contains value 'SecondInstance_API_'
        And The Study Activity Library is displayed as 'Sponsor' in the table
        And The activity state is 'Review not needed'
        And The reviewed checkbox is enabled
        And The reviewed checkbox is displayed as checked
        And SoA Group is set to 'INFORMED CONSENT'
        And Data collection column is set to 'Yes'

    Scenario: [Operational SoA Table] User must be able to see all Study Activities added to the Study, including placeholders
        Given The page 'data_specifications/operational' is opened for current study
        And The Operational SoA table is loaded
        And User checks 'Expand table' option in the Operational SoA
        And User checks 'Show SoA groups' option in the Operational SoA
        And Activity 'FirstActivity' is visible in the Operational SoA with Instance 'FirstInstance_API_' underneath it
        And Activity 'SecondActivity' is visible in the Operational SoA with Instance 'SecondInstance_API_' underneath it
        And Activity 'RequiredForActivity' is visible in the Operational SoA with Instance 'API_ActivityInstance' underneath it
        And Activity 'DefaultForActivity' is visible in the Operational SoA with Instance 'API_ActivityInstance' underneath it
        And Activity with multible groupings - soa 'INFORMED CONSENT', group 'Laboratory Assessments', subgroup 'Urinalysis', activity 'Albumin' is visible in the Operational SoA with Instance 'Albumin Urine' underneath it
        And Activity with multible groupings - soa 'INFORMED CONSENT', group 'Laboratory Assessments', subgroup 'Biochemistry', activity 'Albumin' is visible in the Operational SoA with Instance 'Albumin Serum' underneath it
        And Activity 'Placeholder_Submitted_' in the Operational SoA does not have Instance underneath it
        And Activity 'Placeholder_Unsubmitted_' in the Operational SoA does not have Instance underneath it
        And Activity 'MissingInstance' in the Operational SoA does not have Instance underneath it
        And Activity 'NoDataCollection' in the Operational SoA does not have Instance underneath it
        And The Activity Instance 'Albumin Urine' is marked on visit 'V2' in the Operational SoA
        And The Activity Instance 'Albumin Urine' is marked on visit 'V3' in the Operational SoA
        And The Activity Instance 'Albumin Serum' is marked on visit 'V2' in the Operational SoA
        And The Activity Instance 'Albumin Serum' is marked on visit 'V3' in the Operational SoA

    Scenario: [Red bell handling] User must be presented with Red Bell and 'Review needed' status if activity instance name gets updated
        Given The page 'data_specifications/instances' is opened for current study
        When User searches for 'FirstInstance_API_'
        And User gets full activity instance name starting with 'FirstInstance_API_'
        And [API] User gets uid of study activity instance with name saved in previous step
        And [API] Activity Instance new version is created
        And [API] Activity instance is updated with new name 'FirstInstance_API_Update'
        Given The page 'data_specifications/instances' is opened for current study
        When User searches for 'FirstInstance_API_'
        And The activity state is 'Review needed'
        And The red alert badge is present

    Scenario: [Red bell handling] User must be presented with Red Bell and 'Review needed' status if activity instance gets retired
        Given The page 'data_specifications/instances' is opened for current study
        When User searches for 'SecondInstance_API_'
        And User gets full activity instance name starting with 'SecondInstance_API_'
        And [API] User gets uid of study activity instance with name saved in previous step
        And [API] Activity Instance is inactivated
        Given The page 'data_specifications/instances' is opened for current study
        When User searches for 'SecondInstance_API_'
        And The activity state is 'Review needed'
        And The red alert badge is present

    Scenario: [Red bell handling] User must be able to accept/decline activity instance changes
        Given The page 'data_specifications/instances' is opened for current study
        And User clicks Review Activity Instance Updates button
        And For Activity Instance 'FirstInstance_API_' name change to 'FirstInstance_API_Update' is displayed in the Bulk Review window
        And For Activity Instance 'FirstInstance_API_' name change both Accept and Decline options are available in the Bulk Review window
        And Activity Instance 'SecondInstance_API_' status change to Retired is displayed in the Bulk Review window
        And For Activity Instance 'SecondInstance_API_' status change to Retired only Decline option is available in the Bulk Review window
        And Activity Instance 'FirstInstance_API_' name change is Accepted in the Bulk Review window
        And Activity Instance 'SecondInstance_API_' status change is Declined in the Bulk Review window
        And User saves changes in the Bulk Review window
        And Action is confirmed by clicking continue
        And User waits for the table
        When User searches for 'FirstInstance_API_Update'
        And The activity state is 'Review not needed'
        And The yellow alert badge is not present
        And The red alert badge is not present
        When User searches for 'SecondInstance_API_'
        And The activity state is 'Review not needed'
        And The yellow alert badge is present
        And The red alert badge is not present

    Scenario: [Edit] User must be able to mark activity instance as 'Reviewed'
        Given The page 'data_specifications/instances' is opened for current study
        When User searches for 'Albumin Urine'
        Then The activity state is 'Review needed'
        And The user checks the reviewed checkbox
        Then The activity state is 'Reviewed'

    Scenario: [Edit] User must be able to Edit/Add Activity instance relationship
        Given The page 'data_specifications/instances' is opened for current study
        When User searches for 'Albumin Serum'
        When The 'Edit Activity - Instance relationship' option is clicked from the three dot menu list
        And User waits for the table
        And Important checkbox is checked in the edition form
        And 'Baseline flags' dropdown is activated in the edition form
        And 'Visit 2' visit is clicked from the dropdown
        And 'Visit 3' visit is clicked from the dropdown
        And The 'Save as reviewed' is clicked during review
        When User searches for 'Albumin Serum'
        And The activity state is 'Reviewed'
        Then Important is set to 'Yes' in the Study Activity Instance table
        Then Baseline flag value is set to 'Visit 2, Visit 3' in the table

    Scenario: [Edit] User must be able to Delete Activity instance relationship
        Given The page 'data_specifications/instances' is opened for current study
        When User searches for 'DefaultForActivity'
        And The 'Delete Activity - Instance relationship' option is clicked from the three dot menu list
        And User is presented with confirmation window regarding removal of activity-instance relationship
        And Action is confirmed by clicking continue
        When User searches for 'DefaultForActivity'
        And The activity state is 'Add instance'