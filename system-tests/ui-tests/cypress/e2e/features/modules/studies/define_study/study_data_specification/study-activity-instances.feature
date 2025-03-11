@REQ_ID:1074260 @pending_implementation
Feature: Studies - Study Activity Instances

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study activity instances.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And A test study is selected

    Scenario: User must be able to navigate to Study Activity Instance page using side menu
        Given The '/studies' page is opened
        When The 'Data Specification' submenu is clicked in the 'Define Study' section
        Then The current URL is '/studies/Study_000001/data_specification/activity_instances'
        And the tab 'Study Activity Instances' is displayed

    # Note, not all columns are implemented in current release, columns for next release is marked by a comment tag
    Scenario: User must be able to see the Study Activity Instances table with State/Action options listed
        Given The '/studies/Study_000001/data_specification/activity_instances' page is opened
        Then A table is visible with following options
            # Note, this page do not have an add study activity instances, as all study activities and related study activity instances is listed, and instances is added via edit
            | options                                                         |
            | Filters                                                         |
            | Columns                                                         |
            | Export                                                          |
            | Show version history                                            |
            | Add select boxes to table to allow selection of rows for export |
        And A table is visible with following headers
            | headers           |
            | #                 |
            | Library           |
            | SoA group         |
            | Activity group    |
            | Activity subgroup |
            | Activity          |
            | Data Collection   |
            | Activity instance |
            | Topic Code        |
            #| SDTM domain         |
            # 'State/Action' will cover a classification, is described below as well as in API specification.
            | State/Actions     |
        And The following columns available to be displayed
            # Details is a concatination of a number of attributes and related ActivityItems, will be described below
            #| Details             |
            | ADaM Param code |
    #| Activity concept ID |
    #| Instance concept ID |
    #| Required            |
    #| Default             |
    #| Multiple selection  |
    #| Legacy              |
    # Instance Class is the relationship to ActivityInstaceClass node
    #| Instance class      |
    # The following columns is based on relationship for ActivityItemClass, via ActivityItem, to CTTerms/Concepts
    #| Test code           |
    #| Test name           |
    #| Unit dimension      |
    #| Standard Unit       |
    #| Specimen            |
    #| Modified            |
    #| Modified by         |

    # The table list all combinations of study activities and study activity insrances.
    # One row is presentated for all selected study activity instances and the related study activity related to data collection.
    # If study activity is not related to data collection it will be listed with the state describing it is not related to data collection.
    # If no activity instance is selected for an study activity then the row is displayed for the study activity with blank activity instance columns.
    # If multiple selections is possible, and addisional selections can be made - then a row for the study activity with blank activity instance columns is available to support additional selections.
    # If no additional selections is possible, no extra row with blank activity instance columns should be listed.

    Scenario: User must be able to use column selection option
        Given The '/studies/Study_000001/data_specification/activity_instances' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: User must be able to see the Study Activities without any related Study Activity Instances
        Given The '/studies/Study_000001/data_specification/activity_instances' page is opened
        When Study Activities exists without any related Study Activity Instances
        Then these Study Activities is included in the table with values for the following columns
            | column | header            |
            | 1      | #                 |
            | 2      | Library           |
            | 3      | SoA group         |
            | 4      | Activity group    |
            | 5      | Activity subgroup |
            | 6      | Activity          |
            | 7      | Data Collection   |
            | 12     | State/Actions     |
        #| 21     | Modified          |
        #| 22     | Modified by       |
        And all other columns contains no content

    ### Add more scenarios to cover the listings....



    Scenario Outline: State/Actions must be displayed for all study activities and related study activity instances
        Given The '/studies/Study_000001/data_specification/activity_instances' page is opened
        When the table of Activity Instances is displayed including the column 'State/Actions'
        Then the the row values for 'State/Actions' must be as <State Action Value> depending on the <Rule> rules for the Study Activity Instance
        Then the the row values for 'Actions' must list <Action> depending on the value of the status of Activity Instance in Library and Boolean attributes according to <Rule>
        And an <Indicator> is displayed next to the row action icon
        Examples:
            | Indicator            | Higllight colour | State/Action                                         | Rule                                                                                                                         |
            |                      | Green            | Required                                             | Activity Instance is required_for_activity and currently selected for the Activity                                           |
            |                      | Green            | Defaulted                                            | Activity Instance is default_for_activity and currently selected for the Activity                                            |
            |                      | Green            | Defaulted                                            | Activity Instance is the only available instance within the grouping combination for related Activity and currently selected |
            | Red exclamation mark | Red              | Add missing selection                                | No Activity Instance has been selected for Activity related to data collection                                               |
            | Red exclamation mark | Red              | Add missing selection or add reason for deviation... | Required Activity Instance for Activity has not been selected                                                                |
            |                      | Yellow           | Add optional selection if relevant                   | Additional optional Activity Instances can be made as this Activity support multiple selections                              |
            | Red exclamation mark | Red              | Multiple selections, Remove selection                | Multiple Activity Instances has been selected for Activity requiring a single selection                                      |
            |                      | Green            | No data collection                                   | Activity is marked with 'No' for data collection and no Activity Instance can be related                                     |
            | Red bell             | Yellow           | Use new available version                            | Activity Instance is available in a newer version than currently selected, and user has not selected to use old version      |
            | Grey bell            | Yellow           | Keep old version or use new available version        | Activity Instance is available in a newer version than currently selected, and user has selected to use old version          |
            | Red bell             | Yellow           | Retired, change selection                            | Activity Instance is retired                                                                                                 |
            | Grey bell            | Yellow           | Retired, keep retired version                        | Activity Instance is retired but user has selected to keep reference to retired version                                      |


    # Version only for State
    #Scenario Outline: State must be displayed as combination of Activity Instance Boolean attributes and current selections of study activity instances
    #    Given The '/studies/Study_000001/data_specification/activity_instances' page is opened
    #    When the table of Activity Instances is displayed including the column 'State'
    #    Then the the row values for 'State' must be as <State> depending on the value of the Activity Instance Boolean attributes and current selections of study activity instances
    #    Examples:
    #        | Indicator            | State                             | Rule                                                                                                                         |
    #        |                      | Required                          | Activity Instance is required_for_activity and currently selected for the Activity                                           |
    #        |                      | Defaulted                         | Activity Instance is default_for_activity and currently selected for the Activity                                            |
    #        |                      | Defaulted                         | Activity Instance is the only available instance within the grouping combination for related Activity and currently selected |
    #        | Red exclamation mark | Missing selection                 | No Activity Instance has been selected for Activity related to data collection                                               |
    #        | Red exclamation mark | Missing selection                 | Required Activity Instance for Activity has not been selected                                                                |
    #        |                      | Add selection                     | Additional optional Activity Instances can be made as this Activity support multiple selections                              |
    #        | Red exclamation mark | Multiple selections not supported | Multiple Activity Instances has been selected for Activity requiring a single selection                                      |
    #        |                      | No data collection                | Activity is marked with 'No' for data collection and no Activity Instance can be related                                     |
    #        | Red bell             | New version available             | Activity Instance is available in a newer version than currently selected, and user has not selected to use old version      |
    #        | Grey bell            | New version available             | Activity Instance is available in a newer version than currently selected, and user has selected to use old version          |
    #        | Red bell             | Activity is retired               | Activity Instance is retired                                                                                                 |


    # Version only for Actions
    #Scenario Outline: Actions must be displayed based on Activity Instance status and rules related to Boolean variables
    #    Given The '/studies/Study_000001/data_specification/activity_instances' page is opened
    #    When the table of Activity Instances is displayed including the column 'Actions'
    #    Then the the row values for 'Actions' must list <Action> depending on the value of the status of Activity Instance in Library and Boolean attributes according to <Rule>
    #    And an <Indicator> is displayed next to the row action icon
    #        | Indicator            | Action           | Rule                                                                                                                         |
    #        |                      |                  | Activity Instance is required_for_activity and currently selected for the Activity                                           |
    #        |                      |                  | Activity Instance is default_for_activity and currently selected for the Activity                                            |
    #        |                      |                  | Activity Instance is the only available instance within the grouping combination for related Activity and currently selected |
    #        | Red exclamation mark | Add selection    | No Activity Instance has been selected for Activity related to data collection                                               |
    #        | Red exclamation mark | Add selection    | Required Activity Instance for Activity has not been selected                                                                |
    #        |                      | Add selection    | Additional optional Activity Instances can be made as this Activity support multiple selections                              |
    #        | Red exclamation mark | Remove selection | Multiple Activity Instances has been selected for Activity requiring a single selection                                      |
    #        |                      |                  | Activity is marked with 'No' for data collection and no Activity Instance can be related                                     |
    #        | Red bell             | Use new version  | Activity Instance is available in a newer version than currently selected, and user has not selected to use old version      |
    #        | Grey bell            | Use new version  | Activity Instance is available in a newer version than currently selected, and user has selected to use old version          |
    #        | Red bell             | Change selection | Activity Instance is retired                                                                                                 |



    # Old version - we will not use
    #Scenario Outline: Type must be displayed as combination of Activity Instance Boolean attributes
    #    Given The '/studies/Study_000001/data_specification/activity_instances' page is opened
    #    When the table of Activity Instances is displayed including the column 'Type'
    #    Then the the row values for 'Type' must be as <Type Value> depending on the value of the Activity Instance Boolean attributes
    #    Examples:
    #        | required_for_activity | default_for_activity | legacy_usage | Type Value |
    #        | True                  | *                    | False        | Required   |
    #        | False                 | True                 | False        | Default    |
    #        | *                     | *                    | True         | Legacy     |

    # Old version - we will not use
    #Scenario Outline: Actions must be displayed based on Activity Instance status and rules related to Boolean variables
    #    Given The '/studies/Study_000001/data_specification/activity_instances' page is opened
    #    When the table of Activity Instances is displayed including the column 'Actions'
    #    Then the the row values for 'Actions' must list <Action> depending on the value of the status of Activity Instance in Library and Boolean attributes according to <Rule>
    #    And an <Indicator> is displayed next to the row action icon
    #    Examples:
    #        | Indicator            | Action           | Rule                                                                                                                    |
    #        | Red bell             | Use new version  | Activity Instance is available in a newer version than currently selected, and user has not selected to use old version |
    #        | Grey bell            | Use new version  | Activity Instance is available in a newer version than currently selected, and user has selected to use old version     |
    #        | Red bell             | Change selection | Activity Instance is retired                                                                                            |
    #        | Red exclamation mark | Add selection    | No Activity Instance has been made for Activity related to data collection                                              |
    #        | Red exclamation mark | Add selection    | Required Activity Instance for Activity has not been selected                                                           |
    #        | Red exclamation mark | Remove selection | Multiple Activity Instances has been selected for Activity requiring a single selection                                 |


    # Keep in E2E
    #Scenario Outline: Details must be displayed based on Activity Instance and selected information from Activity Items
    #    Given The '/studies/Study_000001/data_specification/activity_instances' page is opened
    #    When the table of Activity Instances is displayed including the column 'Details'
    #    Then the the row values for 'Details' must list <Detail Label> and <Detail Value> depending on the <Detail Source> value of the status of Activity Instance and selected related Activity Items in the Library
    #    Examples:
    #        | Detail Label    | Detail Value                     | Detail Source                                                             |
    #        | Class           | ActivityInstanceClass.name       | ActivityInstanceClass                                                     |
    #        | Topic code      | ActivityInstance.topic_code      | ActivityInstanceClass                                                     |
    #        | ADaM param code | ActivityInstance.adam_param_code | ActivityInstanceClass                                                     |
    #        | SDTM test name  | CTTerm.name_submission_value     | ActivityItem related CTTerm for ActivityItemClass 'test_name_code'        |
    #        | SDTM test code  | CTTerm.code_submission_value     | ActivityItem related CTTerm for ActivityItemClass 'test_name_code'        |
    #        | SDTM domain     | CTTerm.code_submission_value     | ActivityItem related CTTerm for ActivityItemClass 'domain'                |
    #        | Unit dimension  | CTTerm.sponsor_name              | ActivityItem related CTTerm for ActivityItemClass 'unit_dimension'        |
    #        | Standard unit   | UnitDefinition.name              | ActivityItem related UnitDefinition for ActivityItemClass 'standard_unit' |
    #        | Specimen        | CTTerm.sponsor_name              | ActivityItem related CTTerm for ActivityItemClass 'specimen'              |

    ### End of section potentially for API
    ######################################


    Scenario: User must be able to edit a Study Activity Instance selections for a Study Activity
        Given The '/studies/Study_000001/data_specification/activity_instances' page is opened
        When The Study Activity and related Study Activity Instances is edited
        Then The edited Study Activity Instance selections is reflected within the Study Activity Instance table

    Scenario: User must be able to read change history of Study Activity Instances
        Given The '/studies/Study_000001/data_specification/activity_instances' page is opened
        When The user opens page level version history
        Then The user is presented with version history of the output containing timestamp and username

    Scenario: User must be able to read change history of selected Study Activity Instance
        Given The '/studies/Study_000001/data_specification/activity_instances' page is opened
        When The user clicks on History for particular Study Activity Instance row
        Then The user is presented with history of changes for that Study Activity Instance
        And The history contains timestamps and usernames


### Additional notes for things not yet covered in Gherkin specs
# No fitering for 'Details' column - but filtering can be made for the individual specific columns
# Enable filtring on <blanks>/<null>
# Process for selecting new version of Activity Instance
# Process for accepting old version of Activity Instance
# Process of removing selection of retired Activity Instance
# Define Review Workflow process, and a way to 'sign-off' / 'soft-lock' Study Activity Instances