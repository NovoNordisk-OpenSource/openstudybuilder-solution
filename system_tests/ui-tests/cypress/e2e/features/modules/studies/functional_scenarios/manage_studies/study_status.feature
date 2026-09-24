@REQ_ID:1741028
Feature: Studies - Manage Study - Study Status

    Background: User must be logged in
        Given The user is logged in

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to the Study Status page
        Given User selects study with id 'CDISC DEV-9876'
        Given The '/studies' page is opened
        When The 'Study' submenu is clicked in the 'Manage Study' section
        And The 'Study Status' tab is selected
        Then The current URL is '/study_status/study_status'

    @smoke_test
    Scenario: [Table][Columns][Names] User must be able to see the Study Status page table with correct columns
        Given User selects study with id 'CDISC DEV-9876'
        Given The page 'study_status/study_status' is opened for current study
        Then A table is visible with following headers
            | headers                               |
            | Study status                          |
            | Reason for unlocking study            |
            | Other reason for unlocking            |
            | Reason for locking or releasing study |
            | Change description                    |
            | Protocol Version                      |
            | Metadata version                      |
            | Modified                              |
            | Modified by                           |

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option
        Given User selects study with id 'CDISC DEV-9876'
        Given The page 'study_status/study_status' is opened for current study
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    @pending_implementation
    Scenario: User must not be able to Lock a Study when study number is not defined
        Given A study in draft status without study number is selected
        Given The page 'study_status/study_status' is opened for current study
        And User clicks lock study button
        And The user provides release description
        And Form save button is clicked
        And The form is no longer available
        Then The pop up displays 'Cannot lock study without study_number nor study_title'
        And The form is not closed

    @pending_implementation
    Scenario: User must not be able to Lock a Study when study title is not defined
        Given A study in draft status without title is selected
        Given The page 'study_status/study_status' is opened for current study
        And User clicks lock study button
        And The user provides release description
        And Form save button is clicked
        And The form is no longer available
        Then The pop up displays 'Cannot lock study without study_number nor study_title'
        And The form is not closed

    @pending_implementation
    Scenario: User must not be able to Lock a Study when the study is a subpart study
        Given A study in draft status defined as a study subpart
        Given The page 'study_status/study_status' is opened for current study
        Then The action button to lock the study is disabled

    Scenario: [Lock] User must be able to lock study for study specification updates reason
        And User selects study with id 'CDISC DEV-9901'
        And [API] Study title is set for selected study
        And [API] User fetches term uid for reason for unlocking 'Other'
        And [API] Status of study is checked and unlocked, keeping the existing version
        And User selects study with id 'CDISC DEV-9901'
        And The page 'study_status/study_status' is opened for current study
        When The lock study request is intercepted
        And User clicks lock study button
        And User waits for 1 seconds
        And User sets reson for change of study status to 'Study Specification Updates'
        And The user provides protocol major version '1'
        And The user provides protocol minor version '2'
        And Action is confirmed by clicking save
        And User waits for lock study request
        Then The study is displayed as locked with 'Study Specification Updates' as a reason
        And The procotol version is displayed in table as '1.2'

    Scenario: [Lock] User must be able to lock study for final protocol reason
        And User selects study with id 'CDISC DEV-9901'
        And [API] Study title is set for selected study
        And [API] User fetches term uid for reason for unlocking 'Other'
        And [API] Status of study is checked and unlocked, keeping the existing version
        And User selects study with id 'CDISC DEV-9901'
        And The page 'study_status/study_status' is opened for current study
        When The lock study request is intercepted
        And User clicks lock study button
        And User waits for 1 seconds
        And User sets reson for change of study status to 'Final Protocol'
        And The user provides protocol major version '1'
        And Action is confirmed by clicking save
        And User waits for lock study request
        Then The study is displayed as locked with 'Final Protocol' as a reason
        And The procotol version is displayed in table as '1.0'

    Scenario: [Lock] User must not be able to lock study for final protocol reason without major version defined
        And User selects study with id 'CDISC DEV-9901'
        And [API] Study title is set for selected study
        And [API] User fetches term uid for reason for unlocking 'Other'
        And [API] Status of study is checked and unlocked, keeping the existing version
        And User selects study with id 'CDISC DEV-9901'
        And The page 'study_status/study_status' is opened for current study
        When The lock study request is intercepted
        And User clicks lock study button
        And User waits for 1 seconds
        And User sets reson for change of study status to 'Final Protocol'
        And Action is confirmed by clicking save
        Then The form is not closed

    Scenario: [Lock] User must be able to lock study for other reason
        And User selects study with id 'CDISC DEV-9901'
        And [API] Study title is set for selected study
        And [API] User fetches term uid for reason for unlocking 'Other'
        And [API] Status of study is checked and unlocked, keeping the existing version
        And User selects study with id 'CDISC DEV-9901'
        And The page 'study_status/study_status' is opened for current study
        When The lock study request is intercepted
        And User clicks lock study button
        And User waits for 1 seconds
        And User sets reson for change of study status to 'Other'
        And The user provides protocol major version '1'
        And The user provides protocol minor version '2'
        And The user provides explanation for other reason
        And Action is confirmed by clicking save
        And User waits for lock study request
        Then The study is displayed as locked with 'Other' as a reason
        And The procotol version is displayed in table as '1.2'

    Scenario: [Lock] User must not be able to lock study for other reason without reason provided
        And User selects study with id 'CDISC DEV-9901'
        And [API] Study title is set for selected study
        And [API] User fetches term uid for reason for unlocking 'Other'
        And [API] Status of study is checked and unlocked, keeping the existing version
        And User selects study with id 'CDISC DEV-9901'
        And The page 'study_status/study_status' is opened for current study
        When The lock study request is intercepted
        And User clicks lock study button
        And User waits for 1 seconds
        And User sets reson for change of study status to 'Other'
        And The user provides protocol major version '1'
        And The user provides protocol minor version '2'
        And Action is confirmed by clicking save
        Then The form is not closed

    Scenario: [Lock] User must be able to lock study for PORT approval reason
        And User selects study with id 'CDISC DEV-9901'
        And [API] Study title is set for selected study
        And [API] User fetches term uid for reason for unlocking 'Other'
        And [API] Status of study is checked and unlocked, keeping the existing version
        And User selects study with id 'CDISC DEV-9901'
        And The page 'study_status/study_status' is opened for current study
        When The lock study request is intercepted
        And User clicks lock study button
        And User waits for 1 seconds
        And User sets reson for change of study status to 'PORT Approval'
        And The user provides protocol major version '1'
        And The user provides protocol minor version '2'
        And Action is confirmed by clicking save
        And User waits for lock study request
        Then The study is displayed as locked with 'PORT Approval' as a reason
        And The procotol version is displayed in table as '1.2'

    Scenario: [Lock] User must be able to lock study for PORT submission reason
        And User selects study with id 'CDISC DEV-9901'
        And [API] Study title is set for selected study
        And [API] User fetches term uid for reason for unlocking 'Other'
        And [API] Status of study is checked and unlocked, keeping the existing version
        And User selects study with id 'CDISC DEV-9901'
        And The page 'study_status/study_status' is opened for current study
        When The lock study request is intercepted
        And User clicks lock study button
        And User waits for 1 seconds
        And User sets reson for change of study status to 'PORT Submission'
        And The user provides protocol major version '1'
        And The user provides protocol minor version '2'
        And Action is confirmed by clicking save
        And User waits for lock study request
        Then The study is displayed as locked with 'PORT Submission' as a reason
        And The procotol version is displayed in table as '1.2'

    Scenario: [Lock] User must be able to lock study for protocol QC reason
        And User selects study with id 'CDISC DEV-9901'
        And [API] Study title is set for selected study
        And [API] User fetches term uid for reason for unlocking 'Other'
        And [API] Status of study is checked and unlocked, keeping the existing version
        And User selects study with id 'CDISC DEV-9901'
        And The page 'study_status/study_status' is opened for current study
        When The lock study request is intercepted
        And User clicks lock study button
        And User waits for 1 seconds
        And User sets reson for change of study status to 'Protocol QC'
        And The user provides protocol major version '1'
        And The user provides protocol minor version '2'
        And Action is confirmed by clicking save
        And User waits for lock study request
        Then The study is displayed as locked with 'Protocol QC' as a reason
        And The procotol version is displayed in table as '1.2'

    Scenario: [Unlock] User must be able to unlock study for amendment reason
        And User selects study with id 'CDISC DEV-9901'
        And [API] Study title is set for selected study
        And [API] User fetches term uid for reason for locking 'Study Specification Updates'
        And [API] Status of study is checked and locked, keeping the existing version
        And User selects study with id 'CDISC DEV-9901'
        And The page 'study_status/study_status' is opened for current study
        When The unlock study request is intercepted
        And User clicks unlock study button
        And User waits for 1 seconds
        And User sets reson for change of study status to 'Protocol Amendment Updates'
        And Action is confirmed by clicking save
        And User waits for unlock study request
        Then The study is displayed as unlocked with 'Amendment' as a reason

    Scenario: [Unlock] User must be able to unlock study for other reason
        And User selects study with id 'CDISC DEV-9901'
        And [API] Study title is set for selected study
        And [API] User fetches term uid for reason for locking 'Study Specification Updates'
        And [API] Status of study is checked and locked, keeping the existing version
        And User selects study with id 'CDISC DEV-9901'
        And The page 'study_status/study_status' is opened for current study
        When The unlock study request is intercepted
        And User clicks unlock study button
        And User waits for 1 seconds
        And User sets reson for change of study status to 'Other'
        And Action is confirmed by clicking save
        And User waits for unlock study request
        Then The study is displayed as unlocked with 'Other' as a reason

    Scenario: [Unlock] User must be able to unlock study for study specification updates reason
        And User selects study with id 'CDISC DEV-9901'
        And [API] Study title is set for selected study
        And [API] User fetches term uid for reason for locking 'Study Specification Updates'
        And [API] Status of study is checked and locked, keeping the existing version
        And User selects study with id 'CDISC DEV-9901'
        And The page 'study_status/study_status' is opened for current study
        When The unlock study request is intercepted
        And User clicks unlock study button
        And User waits for 1 seconds
        And User sets reson for change of study status to 'Study Specification Updates'
        And Action is confirmed by clicking save
        And User waits for unlock study request
        Then The study is displayed as unlocked with 'Study Specification Updates' as a reason

    Scenario: [Unlock] User must be notified when unlocking a study with protocol version submitted
        And User selects study with id 'CDISC DEV-9902'
        And [API] Study title is set for selected study
        And [API] User fetches term uid for reason for locking 'Final Protocol'
        And [API] Status of study is checked and locked in major version '1' and minor version '0'
        And User selects study with id 'CDISC DEV-9902'
        And The study snapshot request is intercepted
        And The study protocol request is intercepted
        And The page 'study_status/study_status' is opened for current study
        And User waits for study snapshot request
        And User waits for study protocol request
        And User waits for the table
        When The 'unlock-study' button is clicked
        Then The user is prompted with a notification message 'Note, that this study has been locked to a protocol version. If the study has passed FPFV, you accept that you carry the risk of modifying the study metadata related to the protocol and downstream processing by proceeding. How do you want to proceed?'