@REQ_ID:1074260 
Feature: Studies - Define Study - Study Activities - Schedule of Activities - Protocol

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study SoA for the protocol.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    Scenario: [Navigation] User must be able to navigate to Protocol SoA page using side menu
        Given The '/studies' page is opened
        When The 'Study Activities' submenu is clicked in the 'Define Study' section
        And The 'Schedule of Activities' tab is selected
        And User switches to the 'protocol' view
        Then The current URL is '/activities/soa'

    Scenario: [Table][Options] User must be able to see The Protocol SoA options
        Given The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        And Protocol page has following options available: Split SoA, Show epochs, Show milestones
        Then The download button is available

    Scenario: [Navigation] User must be able to swich between Protocol and Detailed SoA view
        Given The page 'activities/soa' is opened for current study
        When User switches to the 'protocol' view
        Then The user is presented with 'Protocol' layout
        When User switches to the 'detailed' view
        Then The user is presented with 'Detailed' layout

    @manual_test
    Scenario: [Table][Overview] User must be able to view The study activities in The Protocol SoA table
        Given The page 'activities/soa' is opened for current study
        When The test study activities is selected for the study
        And The test study activities is marked to be displayed in the Protocol SoA including all groupings
        Then The Protocol SoA table matrix display rows for each test study activity grouped by activity group, activity subgroup and SoA group
    # Note The specific display/hide options for The Protocol SoA is specified in study-detailed-soa.feature

    @manual_test
    Scenario: [Settings] User must be able to define SoA settings for time unit and show baseline as time 0
        Given The page 'activities/soa' is opened for current study
        When The user selects The SoA settings control icon
        Then The SoA Settings form opens

    @manual_test
    Scenario Outline: [Display][Time unit] User must be able to control display of time in SoA by selecting time unit and option to display basline time as 0 or 1
        Given The page 'activities/soa' is opened for current study
        When User select <time unit> and <option for baseline shown as time 0> on The SoA Settings form
        Then The SoA time row will show <time unit>
        And SoA time values will be according to <study time>
        Examples:
            | time unit | option for baseline shown as time 0 | study time                 |
            | Days      | True                                | Study duration days value  |
            | Weeks     | True                                | Study duration weeks value |
            | Days      | False                               | Study day value            |
            | Weeks     | False                               | Study week value           |

    @manual_test
    Scenario Outline: [Display][Epochs][Milestones] User must be able to control display of study epoch and study visit milestone in protocol SoA
        Given The page 'activities/soa' is opened for current study
        When user select show epochs as <Show epochs> and show milestone as <Show milestones>
        Then The study epoch display is <Show epochs> in the protocol SoA header row
        And The study visit milestone display is <Show milestones> in the protocol SoA header row
        Examples:
            | Show epochs | Show milestones |
            | enabled     | enabled         |
            | enabled     | disabled        |
            | disabled    | enabled         |
            | disabled    | disabled        |

    @manual_test
    Scenario: [Export][Docx] User must be able to export The Protocol SoA table including an empty column for protocol section references
        Given The page 'activities/soa' is opened for current study
        When The export in DOCX format is selected
        Then Protocol SoA is downloaded as a DOCX file
        And DOCX file contains the Protocol SoA table matrix including an empty column for protocol section references

    @manual_test
    Scenario: [Display][Week] User must be able to select week view of Protocol SoA
        Given The page 'activities/soa' is opened for current study
        When The user selects preffered time unit as week
        Then The Protocol SoA is presented with Study Weeks as time representation

    @manual_test
    Scenario: [Display][Day] User must be able to select day view of Protocol SoA
        Given The page 'activities/soa' is opened for current study
        When The user selects preffered time unit as day
        Then The Protocol SoA is presented with Study Days as time representation

    @manual_test
    Scenario: [Baseline] User must be able to mark baseline visit as time 0
        Given The page 'activities/soa' is opened for current study
        When The user selects 'Baseline shown as time 0'
        Then The Protocol SoA present the baseline visit (radnomisation) as time 0
