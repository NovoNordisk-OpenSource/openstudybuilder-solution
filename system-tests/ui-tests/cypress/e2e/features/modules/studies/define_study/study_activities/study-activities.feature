@REQ_ID:1074260
Feature: Studies - Study Activities

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study activities.

    Background: User is logged in and study has been selected
        Given The user is logged in

    Scenario: User must be able to navigate to Study Activity page using side menu
        Given A test study is selected
        And The '/studies' page is opened
        When The 'Study Activities' submenu is clicked in the 'Define Study' section
        Then The current URL is '/studies/Study_000001/activities/list'

    Scenario: User must be able to see the Study Activities table with options listed in this scenario
        Given The '/studies/Study_000001/activities/list' page is opened
        Then A table is visible with following headers
            | headers           |
            | #                 |
            | Library           |
            | SoA group         |
            | Activity group    |
            | Activity subgroup |
            | Activity          |
            | Data collection   |
            | Modified          |
            | Modified by       |

    Scenario: User must be able to use column selection option
        Given The '/studies/Study_000001/activities/list' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: User must be able to create a Study Activity from an existing study by study id
        And The '/studies/Study_000001/activities/list' page is opened
        When The Study Activity is added from an existing study by study id
        Then The Study Activity copied from existing study is visible within the Study Activities table

    Scenario: User must be able to delete a Study Activity
        Given The '/studies/Study_000001/activities/list' page is opened
        When The Study Activity is deleted
        Then The Study Activity is no longer available

    Scenario: User must be able to create a Study Activity from an existing study by study acronym
        And The '/studies/Study_000001/activities/list' page is opened
        When The Study Activity is added from an existing study by study acronym
        Then The Study Activity copied from existing study is visible within the Study Activities table

    Scenario: User must be able to create a Study Activity from the library
        And The activity exists in the library
        And The '/studies/Study_000001/activities/list' page is opened
        When The Study Activity is added from the library
        Then The Study Activity created from library is visible within the Study Activities table

    Scenario: User must be able to create a Study Activity placeholder as an activity concept request
        And The '/studies/Study_000001/activities/list' page is opened
        When The Study Activity is added as a placeholder for new activity request
        Then The Study Activity placeholder is visible within the Study Activities table

    Scenario: User must be able to delete a Study Activity placeholder
        Given The '/studies/Study_000001/activities/list' page is opened
        When The Study Activity Placeholder is deleted
        Then The Study Activity Placeholder is no longer available

    Scenario: User must be able to edit a Study Activity
        Given The '/studies/Study_000001/activities/list' page is opened
        When Study Activity edition is initiated
        And The SoA group can be changed
        Then The edited Study Activity data is reflected within the Study Activity table

    # Note, currently only the SoA group can be changed, not the request, will be specified and updated in later release
    Scenario: User must be able to edit a Study Activity placeholder
        Given The '/studies/Study_000001/activities/list' page is opened
        When The Study Activity is added as a placeholder for new activity request
        When Study Activity Placeholder edition is initiated
        And The SoA group can be changed
        Then The edited Study Activity data is reflected within the Study Activity table

    Scenario: User must not be able to create Study Activity from studies without study selected
        Given The '/studies/Study_000001/activities/list' page is opened
        When The Study Activity select from study form is opened on second step
        And The user tries to go to Activity Selection without study chosen
        Then The validation appears and Create Activity form stays on Study Selection

    Scenario: User must not be able to create Study Activity from library without SoA group selected
        Given The '/studies/Study_000001/activities/list' page is opened
        When The Study Activity select from library form is opened on second step
        And The user tries to go further without SoA group chosen
        Then The validation appears and Create Activity form stays on SoA group selection

    Scenario: User must not be able to create Study Activity placeholder without SoA group selected
        Given The '/studies/Study_000001/activities/list' page is opened
        When The Study Activity create placeholder form is opened on second step
        And The user tries to go further in activity placeholder creation without SoA group chosen
        Then The validation appears under empty SoA group selection