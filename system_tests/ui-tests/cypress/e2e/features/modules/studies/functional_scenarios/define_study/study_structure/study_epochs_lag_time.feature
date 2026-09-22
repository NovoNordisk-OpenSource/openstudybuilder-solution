@study_epoch_lag_time
Feature: Studies - Define Study - Study Structure - Study Epoch Lag Time

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    Scenario: [Test data] User must be able to prepare data before tests execution
        Given [API] All visit groups uids are fetched
        And [API] All visit groups are removed
        And [API] Study vists uids are fetched for selected study
        And [API] Study visits in selected study are cleaned-up
        And [API] All Activities fotnotes are deleted from selected study
        And [API] All Activities are deleted from selected study
        And [API] All epochs assigned to the selected study are fetched
        And [API] All epochs assigned to the selected study are deleted

    Scenario: [Feature flag] Lag-time fields and columns are hidden when disabled
        Given [API] The feature flag 'study_epoch_lag_time' is disabled
        And User intercepts study epochs request
        And The page 'study_structure/epochs' is opened for current study
        Then The study epoch lag-time fields are not visible
        And The study epoch lag-time columns are not visible
        And The study epochs request does not include lag-time data

    Scenario: [Create] User can create an epoch with lag-time values
        Given [API] The feature flag 'study_epoch_lag_time' is enabled
        And The page 'study_structure/epochs' is opened for current study
        When User click create epoch button
        And User continues to next step of study structure stepper
        And User sets epoch 'type' as 'Post Treatment'
        And User sets epoch 'subtype' as 'Elimination'
        Then User can select only plural lag-time units
        And User sets epoch lag time 'ae_lag_time' as '5' with unit 'days'
        And User sets epoch lag time 'hypo_lag_time' as '2' with unit 'weeks'
        And User sets epoch lag time 'ce_lag_time' as '7' with unit 'days'
        And User sets epoch description
        And User intercepts study epochs request
        And User continues to next step of study structure stepper
        When The form is no longer available
        Then The study epoch lag-time columns are visible
        And The study epochs request includes lag-time data
        And The study epoch lag time 'ae_lag_time' is '5 days' in row 0
        And The study epoch lag time 'hypo_lag_time' is '2 weeks' in row 0
        And The study epoch lag time 'ce_lag_time' is '7 days' in row 0

    Scenario: [Edit] User can edit and clear an epoch lag-time value
        Given [API] The feature flag 'study_epoch_lag_time' is enabled
        And [API] An epoch with lag-time values exists in the selected study
        And The page 'study_structure/epochs' is opened for current study
        And The study epoch with subtype 'Elimination' is found
        When The 'Edit' option is clicked from the three dot menu list
        And User waits for 1 seconds
        And User sets epoch lag time 'ae_lag_time' as '10' with unit 'weeks'
        And User clears epoch lag time 'hypo_lag_time'
        And User updates epoch description
        And User intercepts study epochs request
        And User continues to next step of study structure stepper
        When The form is no longer available
        Then The study epoch lag time 'ae_lag_time' is '10 weeks' in row 0
        And The study epoch lag time 'hypo_lag_time' is empty in row 0

    Scenario: [Validation] User cannot submit a negative lag-time value
        Given [API] The feature flag 'study_epoch_lag_time' is enabled
        And The page 'study_structure/epochs' is opened for current study
        When User click create epoch button
        And User continues to next step of study structure stepper
        And User sets epoch 'type' as 'Post Treatment'
        And User sets epoch 'subtype' as 'Elimination'
        And User sets epoch lag time 'ae_lag_time' as '-1' with unit 'days'
        Then The validation message "Value can't be less than 0" is displayed for 'ae_lag_time'

    Scenario: [Validation] User cannot submit a lag-time value without a unit
        Given [API] The feature flag 'study_epoch_lag_time' is enabled
        And The page 'study_structure/epochs' is opened for current study
        When User click create epoch button
        And User continues to next step of study structure stepper
        And User sets epoch 'type' as 'Post Treatment'
        And User sets epoch 'subtype' as 'Elimination'
        And User sets epoch lag time 'ae_lag_time' as '1'
        And User sets epoch description
        And User attempts to continue to next step of study structure stepper
        Then The snackbar message 'Lag time value for' is displayed