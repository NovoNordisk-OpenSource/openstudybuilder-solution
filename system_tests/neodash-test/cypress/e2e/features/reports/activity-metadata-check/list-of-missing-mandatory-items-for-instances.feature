@REQ_ID:1070686
@neodash_tests
Feature: Activity Metadata Check - List of Missing Mandatory Items for Instances

    As a user, I want to be able to ensure activity metadata within StudyBuilder is mapped correctly

    Background: User must be logged into the dashboard
        Given The user is logged in
        And The 'Activity Metadata Check' page is opened

    Scenario: User must be able to view different metrics in List of Missing Mandatory Items for Instances
        Given The neoDash 'List of Missing Mandatory Items for Instances' tab is selected
        Then The following set of neoDash reports are displayed
            | report                             |
            | Results                            |
            | Used terms for Activity Item Class |

    Scenario: User must be able to view all activities missing mandatory items
        Given The neoDash 'List of Missing Mandatory Items for Instances' tab is selected
        Then The table 'Results' displays the following items
            | Activity Group | Activity Subgroup | Activity | Activity Instance | Activity Instance Class | Missing Activity Item | Class of Missing Activity Item |

    Scenario: User must be able to filter down activities missing mandatory items
        Given The neoDash 'Activity Lib (Search Top-Down)' tab is selected
        When The user selects 'Finding' from the 'activityinstanceclassvalue_name' dropdown
        And The user selects 'TextualFindings' from the 'activityinstanceclassvalue_name_subtype' dropdown
        And The user switches to the 'List of Missing Mandatory Items for Instances' page
        Then The table 'List of Activities' displays the following items
            | column            | value                        |
            | Activity Type     | Finding                      |
            | Activity Subtype  | TextualFindings              |
            | Activity Group    | AE Requiring Additional Data |
            | Activity Subgroup | Acute Kidney Injury          |
            | Activity          | Acute Kidney Injury Biopsy   |

    @pending_implementation
    Scenario: User must be able to filter down activities missing mandatory items
        Given The neoDash 'Activity Lib (Search Top-Down)' tab is selected
        When The user selects 'Finding' from the 'activityinstanceclassvalue_name' dropdown
        And The user selects 'TextualFindings' from the 'activityinstanceclassvalue_name_subtype' dropdown
        And The user switches to the 'List of Missing Mandatory Items for Instances' page
        Then The Used terms for Activity Item Class table displays possible terms to use for Missing Activity Item