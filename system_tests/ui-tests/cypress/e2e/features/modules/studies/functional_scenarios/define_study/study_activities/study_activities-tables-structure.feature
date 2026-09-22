@REQ_ID:1074260
Feature: Studies - Define Study - Study Activities - Schedule of Activities - Detailed - Structure

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study SoA.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    Scenario: [TestData] Study visits, epochs and activities are created
        And [API] The epoch with type 'Pre Treatment' and subtype 'Run-in' exists in selected study
        And [API] The epoch with type 'Treatment' and subtype 'Intervention' exists in selected study
        And [API] Study vists uids are fetched for selected study
        When [API] Study visits in selected study are cleaned-up
        And [API] The static visit data is fetched
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Pre-screening', epoch 'Run-in'
        And [API] The visit with following attributes is created: isGlobalAnchor 1, visitWeek 0
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 1, minVisitWindow -1, maxVisitWindow 1
        And [API] The dynamic visit data is fetched: contact mode 'On Site Visit', time reference 'Global anchor visit', type 'Randomisation', epoch 'Intervention'
        And [API] The visit with following attributes is created: isGlobalAnchor 0, visitWeek 2, minVisitWindow 3, maxVisitWindow 7
        And [API] All Activities are deleted from selected study
        And [API] Study Activity is created and approved
        And [API] Get SoA Group 'INFORMED CONSENT' id
        And [API] Activity is added to the selected study
        And Activity, Group And Subgroup names are fetch to be used in SoA
    
    @smoke_test
    Scenario: [Activity List][Table][Columns][Names] User must be able to see the Study Activities table with options listed in this scenario
        Given The page 'activities/list' is opened for current study
        Then A table is visible with following headers
            | headers           |
            | Library           |
            | SoA group         |
            | Activity group    |
            | Activity subgroup |
            | Activity          |
            | Data collection   |
            | Modified          |
            | Modified by       |

    Scenario: [Activity List][Table][Columns][Visibility] User must be able to use column selection option
        Given The page 'activities/list' is opened for current study
        And Study activities for selected study are loaded
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    @smoke_test
    Scenario: [SoA][View] User must be presented with option to switch between Detailed and Protocol view
        Given The page 'activities/soa' is opened for current study
        When 'Detailed' view is available in SoA
        When 'Protocol' view is available in SoA

    @smoke_test
    Scenario: [SoA][View] User must not be presented with option to switch to Operational view
        Given The page 'activities/soa' is opened for current study
        When 'Operational' view is not available in SoA

    Scenario: [SoA][Table][Options] User must be able to see the Detailed SoA table with options listed in this scenario
        Given The page 'activities/soa' is opened for current study
        Then SoA table is available with Bulk actions, Export and Show version history
        And Search is available in SoA table
        And Button for Expanding SoA table is available

    Scenario: [SoA][Table][Options] User must be able to see the Detailed SoA Footnotes table with options listed in this scenario
        Given The page 'activities/soa' is opened for current study
        When Add footnote button is available in the detailed SoA
        Then A table is visible with following options
            | options                    |
            | add-study-footnote         |
            | filters-button             |
            | History                    |
            | search-field               |
            
    @smoke_test
    Scenario: [SoA][Table][Columns][Names] User must be able to see the Footnotes table with specified headers
        Given The page 'activities/soa' is opened for current study
        And A table is visible with following headers
            | headers      |
            | #            |
            | Footnote     |
            | Linked to    |

    @smoke_test
    Scenario: [Table][Columns][Names] User must be able to see the SoA table with specified headers
        Given The page 'activities/soa' is opened for current study
        And SoA table is visible with following headers
            | headers       |
            | Epoch         |
            | Visit         |
            | Study week    |
            | Visit window  |

    Scenario: [Table][Protocol Lab Table][Structure] User must be presented with lab assesments activities in the Lab Table view
        Given The page 'activities/soa' is opened for current study
        When User switches to the 'protocol_lab_table' view
        Then The laboratory assements activities are present in protocol lab table

    Scenario: [Table][Detailed SoA][Structure][Activity] User must be able to view the study activities in the detailed SoA table matrix
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        Then Activity SoA group, group, subgroup and name are visible in the detailed view

    Scenario: [Table][Detailed SoA][Structure][Epochs] User must be able to view the study epochs in the protocol SoA table matrix
        Given The page 'activities/soa' is opened for current study
        Then Epoch 'Run-in' and epoch 'Intervention' are visible in the detailed view

    Scenario: [Table][Detailed SoA][Structure][Visits] User must be able to view the study visits in the protocol SoA table matrix
        Given The page 'activities/soa' is opened for current study
        Then Visits 'V1', 'V2', 'V3' are visible in the detailed view

    Scenario: [Table][Detailed SoA][Structure][Study weeks] User must be able to view the study weeks in the protocol SoA table matrix
        Given The page 'activities/soa' is opened for current study
        Then Study weeks 0, 1, 2 are visible in the detailed view

    Scenario: [Table][Detailed SoA][Structure][Study visit windows] User must be able to view the study visit window in the protocol SoA table matrix
        Given The page 'activities/soa' is opened for current study
        Then Study visit windows '0', '±1', '+3/+7' are visible in the detailed view

    @manual_test
    Scenario: User must be presented with time unit of visits the same as defined in first defined study visity
        Given The page 'activities/soa' is opened for current study
        And The test study data contains defined visits
        Then The SoA is displaying the data using correct time unit

    Scenario: [Table][Structure][Hide/Unhide][Group] User must me able to hide/unhide group in SoA
        Given The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        Then Group is visible in the protocol SoA
        And User switches to the 'detailed' view
        And Detailed SoA table is loaded
        And User expand table
        And User clicks eye icon on group level
        And User waits for 1 seconds
        And User switches to the 'protocol' view
        And User waits for the protocol SoA table to load
        Then Group is not visible in the protocol SoA
        And User switches to the 'detailed' view
        And User clicks eye icon on group level
        And User waits for 1 seconds
        And User switches to the 'protocol' view
        Then Group is visible in the protocol SoA

    Scenario: [Table][Structure][Hide/Unhide][Subgroup] User must me able to hide/unhide subgroup in SoA
        Given The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        Then Subgroup is visible in the protocol SoA
        And User switches to the 'detailed' view
        And Detailed SoA table is loaded
        And User expand table
        And User clicks eye icon on subgroup level
        And User waits for 1 seconds
        And User switches to the 'protocol' view
        And User waits for the protocol SoA table to load
        Then Subgroup is not visible in the protocol SoA
        And User switches to the 'detailed' view
        And User clicks eye icon on subgroup level
        And User waits for 1 seconds
        And User switches to the 'protocol' view
        Then Subgroup is visible in the protocol SoA

    Scenario: [Table][Structure][Hide/Unhide][Activity] User must me able to hide/unhide activity in SoA
        Given The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        And User waits for the protocol SoA table to load
        Then Activity is not visible in the protocol SoA
        And User switches to the 'detailed' view
        And Detailed SoA table is loaded
        And User expand table
        And User clicks eye icon on activity level
        And User waits for 1 seconds
        And User switches to the 'protocol' view
        Then Activity is visible in the protocol SoA 
        And User switches to the 'detailed' view
        And User clicks eye icon on activity level
        And User waits for 1 seconds
        And User switches to the 'protocol' view
        And User waits for the protocol SoA table to load
        Then Activity is not visible in the protocol SoA

    Scenario: [Table][Protocol SoA][Structure][Activity] User must be able to view the study activities in the protocol SoA table matrix
        Given The page 'activities/soa' is opened for current study
        And Detailed SoA table is loaded
        And User expand table
        And User clicks eye icon on activity level
        And User clicks eye icon on SoA group level for 'INFORMED CONSENT'
        And User waits for 1 seconds
        And User switches to the 'protocol' view
        And User waits for the protocol SoA table to load
        Then Activity SoA group, group, subgroup and name are visible in the protocol view

    Scenario: [Table][Protocol SoA][Structure][Epochs] User must be able to view the study epochs in the protocol SoA table matrix
        Given The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        And User waits for the protocol SoA table to load
        Then Epoch 'Run-in' and epoch 'Intervention' are visible in the protocol view

    Scenario: [Table][Protocol SoA][Structure][Visits] User must be able to view the study visits in the protocol SoA table matrix
        Given The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        And User waits for the protocol SoA table to load
        Then Visits 'V1', 'V2', 'V3' are visible in the protocol view

    Scenario: [Table][Protocol SoA][Structure][Study weeks] User must be able to view the study weeks in the protocol SoA table matrix
        Given The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        And User waits for the protocol SoA table to load
        Then Study weeks 0, 1, 2 are visible in the protocol view

    Scenario: [Table][Protocol SoA][Structure][Study visit windows] User must be able to view the study visit window in the protocol SoA table matrix
        Given The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        And User waits for the protocol SoA table to load
        Then Study visit windows '0', '±1', '+3/+7' are visible in the protocol view

    Scenario: [Table][Protocol SoA][Split][Single visit] User must be able to split protocol SoA by particular visit
        Given The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        And User waits for 1 seconds
        And The SoA Splitting is enabled
        And User intercepts split soa request
        And The user splits-unsplits the SoA by 'V3'
        And User waits for split soa request
        Then The SoA split is created on 'V3'

    Scenario: [Table][Protocol SoA][Split][Multiple visit] User must be able to split protocol SoA by on multiple visits
        Given The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        And The user splits-unsplits the SoA by 'V3'
        And User intercepts split soa request
        And The user splits-unsplits the SoA by 'V3'
        And User waits for split soa request
        Then The SoA split is created on 'V3'
        And User intercepts split soa request
        When The user splits-unsplits the SoA by 'V2'
        And User waits for split soa request
        Then The SoA split is created on 'V2'

    Scenario: [Table][Protocol SoA][Unsplit] User must be able to unsplit SoA
        Given The page 'activities/soa' is opened for current study
        And User switches to the 'protocol' view
        And User intercepts unsplit soa request
        And The user splits-unsplits the SoA by 'V3'
        And User waits for split soa request
        Then The SoA split on 'V3' is removed