@REQ_ID:1070683

Feature: Library - Concepts - Activities - Activity Item Class Overview Page
    As a user, I want to verify that the Activity Item Class Overview Page in the Concepts Library, can display correctly.

    Background: 
        Given The user is logged in
        When The '/library/activities/activity-item-classes' page is opened

    Scenario: [Navigation][ActivityItemClass] User must be able to navigate to activity item class overview page by clicking its name in the ActivityItemClass table
        When User goes to activity instance class 'domain' overview page by clicking its name
        Then 'domain' overview page is opened

    Scenario: [Navigation][ActivityInstanceClass] User must be able to navigate to activity instance class overview page by clicking its name in the activity item class overview page
        When User goes to activity instance class 'domain' overview page by clicking its name
        Then 'domain' overview page is opened
        When 'GeneralObservation' overview page can be opened by clicking the link in overview page
        Then 'GeneralObservation' overview page is opened

    Scenario: [Sections] Verify that the activity group overview page displays correctly
        Given User intercepts linked activity instance classes request
        When User goes to activity instance class 'domain' overview page by clicking its name
        Then 'domain' overview page is opened
        And User waits for linked activity instance classes request
        And The 'Activity Instance Classes' table is displaying correct columns
        |  header                           |
        |  NAME                             |
        |  ADAM PARAM SPECIFIC ENABLED      |
        |  MANDATORY                        |
        |  MODIFIED                         |
        |  MODIFIED BY                      |
        | VERSION                           |
        | STATUS                            |
        And The free text search field should be displayed in the 'Activity Instance Classes' table

    Scenario: [Versioning] User must be able to see the parent Activity Item Class
        When User goes to activity instance class 'domain' overview page by clicking its name
        Then 'domain' overview page is opened
        When Version '0.1' is selected from the Version dropdown list
        Then The status displayed on the summary has value 'Draft' and version is '0.1'
        When Version '1.0' is selected from the Version dropdown list
        Then The status displayed on the summary has value 'Final' and version is '1.0'
    
    Scenario: [Actions][Availability] User must only have access correct actions depending on item state
        When User goes to activity instance class 'domain' overview page by clicking its name
        Then 'domain' overview page is opened
        Then The pencil button is not available
        Then The approve button is not available
        Then The inactivate button is not available
        Then The new version plus button is not available

    Scenario: [Table][Search][Negative case] User must be able to search not existing activity item class and table will be correctly filtered
        When User goes to activity instance class 'domain' overview page by clicking its name
        Then 'domain' overview page is opened
        When User searches for non-existing item in 'Activity Instance Classes' table
        Then The Activity Instance Classes table is empty

    @smoke_test
    Scenario: [Table][Search][Postive case] User must be able to search activity item class connected to activity instance class
        When User goes to activity instance class 'domain' overview page by clicking its name
        Then 'domain' overview page is opened
        And User searches for activity instance class 'GeneralObservation' in linked activity instance class table
        Then 1 result is present in the 'Activity Instance Classes' table
        And Activity Instance Class 'GeneralObservation' is present in first row of the Activity Instance Class table
        And User searches for activity instance class 'General' in linked activity instance class table
        Then 1 result is present in the 'Activity Instance Classes' table

    @manual_test
    Scenario: Verify that the pagination works in the Activity subgroups table
        When I select 5 rows per page from dropdown list in the Activity subgroups table
        Then The Activity subgroups table should be displayed with 5 rows per page
        When I click on the next page button in the Activity subgroups table
        Then The Activity subgroups table should display the next page within 5 rows per page
         When I select 10 rows per page from dropdown list in the Activity subgroups table
        Then The Activity subgroups table should be displayed with 10 rows per page
        When I click on the next page button in the Activity subgroups table
        Then The Activity subgroups table should display the next page within 10 rows per page

    @manual_test
    Scenario: Verify that the export functionality work in the Activity subgroups table
        And The Export functionality works in the Activity subgroups table