@REQ_ID:1070683 @smoke_test

Feature: Library - Concepts - Activities - Navigation
    As a user I want to navigate to each page

    Background: User must be logged in
        Given The user is logged in
        Then The '/library' page is opened

    Scenario: [Navigation] User must be able to navigate to the Activities pages
        When The 'Activities' submenu is clicked in the 'Concepts' section
        And The 'Activities' tab is selected
        Then The current URL is '/library/activities/activities'
        And The 'Activity Groups' tab is selected
        Then The current URL is '/library/activities/activity-groups'
        And The 'Activity Subgroups' tab is selected
        Then The current URL is '/library/activities/activity-subgroups'
        And The 'Activities by Grouping' tab is selected
        Then The current URL is '/library/activities/activities-by-grouping'
        And The 'Activity Instances' tab is selected
        Then The current URL is '/library/activities/activity-instances'
        And The 'Activity Instance Classes' tab is selected
        Then The current URL is '/library/activities/activity-instance-classes'
        And The 'Activity Item Classes' tab is selected
        Then The current URL is '/library/activities/activity-item-classes'

    Scenario: [Navigation] User must be able to navigate to the Units page
        When The 'Units' submenu is clicked in the 'Concepts' section
        Then The current URL is '/library/units'