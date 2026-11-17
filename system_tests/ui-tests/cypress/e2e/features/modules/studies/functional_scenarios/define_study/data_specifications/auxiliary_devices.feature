@REQ_ID:XXX
Feature: Studies - Define Study - Data Specificaitons - Auxiliary Devices

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to Study Auxiliary Devices page using side menu
        And The '/studies' page is opened
        When The 'Data Specifications' submenu is clicked in the 'Define Study' section
        And The 'Auxiliary Devices' tab is selected
        Then The current URL is '/data_specifications/auxiliary_devices'

    Scenario: [Table][Columns][Names] User must be able to see the Study Auxiliary Devices table with following columns
        Given The page 'data_specifications/auxiliary_devices' is opened for current study
        Then A table is visible with following headers
            | headers            |
            | Device             |
            | Submission value   |
            | NCI preferred name |
            | Definition         |
            | Algorith           |

    Scenario: [Table][Options] User must be able to see the Study Auxiliary Devices table with following options
        Given The page 'data_specifications/auxiliary_devices' is opened for current study
        Then A table is visible with following options
            | options                 |
            | columns-layout-button   |
            | table-export-button     |
            | create-auxiliary-device |
            | search-field            |
            | History                 |

    Scenario: [Table][Columns][Visibility] User must be able to use column selection option
        Given The page 'data_specifications/auxiliary_devices' is opened for current study
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column
    

    Scenario: [Actions][Populate] User must be presented with data for selected auxiliary device in form
        Given The page 'data_specifications/auxiliary_devices' is opened for current study
        When The 'create-auxiliary-device' button is clicked
        Then The user selects Auxiliary Device
        Then The form contains auxiliary device details

    Scenario: [Actions][Create] User must be able to add Auxiliary Devices for study
        Given [API] The selected study Auxiliary Devices are cleared
        Given The page 'data_specifications/auxiliary_devices' is opened for current study
        When The 'create-auxiliary-device' button is clicked
        And The user selects Auxiliary Device
        And Form save button is clicked
        Then The auxiliary device is added to the table

    Scenario: [Actions][Edit] User must be able to remove Auxiliary Devices from study
        Given [API] The auxiliary device exists for current study
        Given The page 'data_specifications/auxiliary_devices' is opened for current study
        When The user intercepts the auxiliary device delete request
        When The 'Remove device' option is clicked from the three dot menu list
        And Action is confirmed by clicking continue
        Then The auxiliary device is removed from the table

    Scenario: [Export][CSV] User must be able to export the data in CSV format
        Given The page 'data_specifications/auxiliary_devices' is opened for current study
        When User clicks table export button
        And User selects 'CSV' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'AuxiliaryDevices' file is downloaded in 'csv' format

    Scenario: [Export][Json] User must be able to export the data in JSON format
        Given The page 'data_specifications/auxiliary_devices' is opened for current study
        When User clicks table export button
        And User selects 'JSON' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'AuxiliaryDevices' file is downloaded in 'json' format

    Scenario: [Export][Xml] User must be able to export the data in XML format
        Given The page 'data_specifications/auxiliary_devices' is opened for current study
        When User clicks table export button
        And User selects 'XML' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'AuxiliaryDevices' file is downloaded in 'xml' format

    Scenario: [Export][Excel] User must be able to export the data in EXCEL format
        Given The page 'data_specifications/auxiliary_devices' is opened for current study
        When User clicks table export button
        And User selects 'EXCEL' format to export the table content
        And Action is confirmed by clicking continue
        Then The study specific 'AuxiliaryDevices' file is downloaded in 'xlsx' format

    Scenario: [Audit Trail] User must be able to view audit trail for auxiliary device table
        Given [API] The auxiliary device exists for current study
        Given The page 'data_specifications/auxiliary_devices' is opened for current study
        When The user intercepts audit trail request
        When The history button is clicked
        Then The audit trail panel for auxiliary devices is displaying relevant audit information

    Scenario: [Audit Trail] User must be able to view audit trail for particular auxiliary device
        Given [API] The auxiliary device exists for current study
        Given The page 'data_specifications/auxiliary_devices' is opened for current study
        When The user intercepts audit trail request
        When The 'History' option is clicked from the three dot menu list for auxiliary device
        Then The audit trail panel for auxiliary devices is displaying relevant audit information