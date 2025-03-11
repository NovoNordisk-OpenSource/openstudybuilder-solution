@REQ_ID:XXXX 

Feature: Administration - System Announcement

  Background: User is logged in
    Given The user is logged in with all.in profile

  Scenario: User must be able to choose type of announcement
    Given The '/administration/announcements' page is opened
    And the administration annoucement page is initialized
    And the user chooses the type of announcement as Informative
    Then the preview box at the bottom should change color to blue
    When the user chooses the type of announcement as Warning
    Then the preview box at the bottom should change color to yellow
    When the user chooses the type of announcement as Error
    Then the preview box at the bottom should change color to red

  Scenario: User must be able to fill in announcement details
    Given The '/administration/announcements' page is opened
    And Toggle on announcement and verify visibility
    When the user fills in the announcement title
    And the user fills in the announcement description
    And the user presses SAVE CHANGES
    And navigates to any other page in StudyBuilder
    And presses CTRL-R to reload the page
    Then the announcement box should be shown

  Scenario: User must be able to remove the notification
    Given The '/administration/announcements' page is opened
    And Toggle on announcement and verify visibility
    When The homepage is opened
    Then the announcement box should be shown
    When the user removes the notification window by clicking on the cross in the right side
    And The '/studies' page is opened
    Then the notification should not reappear
    When The '/library' page is opened
    Then the notification should not reappear
    When presses CTRL-R to reload the page
    Then the announcement box should be shown

  Scenario: Toggle off announcement and verify visibility
    Given The '/administration/announcements' page is opened
    When the user toggles Show announcement off
    And the user presses SAVE CHANGES
    And The homepage is opened
    And presses CTRL-R to reload the page
    Then the notification should not reappear
