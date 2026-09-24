@REQ_ID:2866954

Feature: Administration - Feature Flags

  Background: User is logged in
    Given The user is logged in

  Scenario: [Navigation] User must be able to navigate to the feature flags page in the Administration Page
      Given The '/administration' page is opened
      When The 'Feature Flags' button is clicked
      Then The current URL is '/administration/featureflags'

  Scenario: [Table][Columns][Names] User must be able to see the columns list on the main page as below
     Given The '/administration/featureflags' page is opened
     Then A table is visible with following headers
        |  header            |
        |  Feature           |
        |  Name              |

  Scenario: [Feature flags] User must be able to toggle off feature flags
    Given The '/administration/featureflags' page is opened
    And User switch to 'Studies' feature flags
    And User disables 'studies_view_listings_analysis_study_metadata_new' feature flag
    When The '/studies' page is opened
    And Click the View Listings side-menu
    Then The sub-menu Analysis Study Metadata should not exist

  Scenario Outline: [Feature flags] User must not be able to use disabled page
    And User selects study with id 'CDISC DEV-9876'
    When The '/studies' page is opened
    And The '<page>' is not listed after the dropdown '<name>' is clicked
    
    Examples:
      | page                          | name                |
      | Analysis Study Metadata (New) | View Listings       |

  Scenario: [Feature flags] User must be able to toggle on feature flags
    Given The '/administration/featureflags' page is opened
    And User switch to 'Studies' feature flags
    And User enables 'studies_view_listings_analysis_study_metadata_new' feature flag
    When The '/studies' page is opened
    And Click the View Listings side-menu
    Then The sub-menu Analysis Study Metadata should exist

  Scenario Outline: [Feature flags] User must be able to use enabled page
    And User selects study with id 'CDISC DEV-9876'
    And The '/studies' page is opened
    When The '<page>' is clicked in the dropdown of '<name>' tile
    And User waits for 1 seconds
    Then The current URL is '<url>'

    Examples:
      | page                          | name                | url                                  |
      | Analysis Study Metadata (New) | View Listings       | /analysis_study_metadata_new/mdvisit |

