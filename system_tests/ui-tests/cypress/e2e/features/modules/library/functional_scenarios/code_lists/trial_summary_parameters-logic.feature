@REQ_ID:1070679
Feature: Library - Code Lists - Trial Summary Parameters - Logic

    As a user, I want to verify that Trial Summary Parameters can be created, read, and updated correctly.

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Actions][View or edit details] User must be able to open the details of a Trial Summary Parameter
        Given The '/library/trial_summary_parameters' page is opened
        When The 'View or edit details' option is clicked from the three dot menu list
        Then Trial summary parameter details page is opened

    Scenario: [Overview][Edit][Sponsor values][Positive case] User must be able to edit the Term sponsor values of a Trial Summary Parameter
        Given The '/library/trial_summary_parameters' page is opened
        And User searches for 'Draft'
        And The 'View or edit details' option is clicked from the three dot menu list
        When The sponsor values edit button is clicked
        And The Term sponsor values are edited
        And Form save button is clicked
        Then The pop up displays 'Trial Summary Parameter updated'
        And The updated sponsor values are shown in the overview page

    Scenario: [Overview][Edit][Sponsor values][Cancel] User must be able to cancel editing the Term sponsor values
        Given The '/library/trial_summary_parameters' page is opened
        And User searches for 'Draft'
        And The 'View or edit details' option is clicked from the three dot menu list
        When The sponsor values edit button is clicked
        And Modal window form is closed by clicking cancel button
        Then The form is no longer available

    Scenario: [Overview][Edit][Attributes values][Positive case] User must be able to edit the Term attributes values of a Trial Summary Parameter
        Given The '/library/trial_summary_parameters' page is opened
        And User searches for 'Draft'
        And The 'View or edit details' option is clicked from the three dot menu list
        When The attributes values edit button is clicked
        And User fills trial summary parameter defintion as 'E2E Trial Summary Parameter definition update'
        And Form save button is clicked
        Then The pop up displays 'Trial Summary Parameter updated'
        And The updated attributes values are shown in the overview page

    Scenario: [Overview][Edit][Attributes values][Cancel] User must be able to cancel editing the Term attributes values
        Given The '/library/trial_summary_parameters' page is opened
        And User searches for 'Draft'
        And The 'View or edit details' option is clicked from the three dot menu list
        When The attributes values edit button is clicked
        And Modal window form is closed by clicking cancel button
        Then The form is no longer available

    Scenario: [Overview][CT codelists context][Edit order][Positive case] User must be able to edit order and submission value for a codelist context entry
        Given The '/library/trial_summary_parameters' page is opened
        And User searches for 'Draft'
        And The 'View or edit details' option is clicked from the three dot menu list
        When The edit order button is clicked from the CT term codelists context table row
        And The order and submission value are updated
        And Form save button is clicked
        Then The pop up displays 'Order and/or submission value updated'
        And The updated values are shown in the 'CT term codelists context' table

    Scenario: [Overview][CT codelists context][Edit order][Cancel] User must be able to cancel editing the order and submission value
        Given The '/library/trial_summary_parameters' page is opened
        And User searches for 'Draft'
        And The 'View or edit details' option is clicked from the three dot menu list
        When The edit order button is clicked from the CT term codelists context table row
        And Modal window form is closed by clicking cancel button
        Then The form is no longer available

    @smoke_test
    Scenario: [Create][Positive case] User must be able to add a new Trial Summary Parameter
        Given The '/library/trial_summary_parameters' page is opened
        When The plus button is clicked
        And User selects first library for trial summary parameter
        And User fills trial summary parameter sponsor name with random, unique value
        And User fills trial summary parameter submission code value with random, unique value
        And User fills trial summary parameter submission name value with random, unique value
        And User selects first required level for trial summary parameter
        And User fills trial summary parameter order as '1'
        And User fills trial summary parameter defintion as 'E2E Trial Summary Parameter definition'
        And Form save button is clicked
        Then The new Trial Summary Parameter is visible in the table
        And The name status is set to 'Draft'
        And The attributes status is set to 'Draft'

    Scenario: [Create][Negative case] User must not be able to save a new Trial Summary Parameter without the Sponsor name
        Given The '/library/trial_summary_parameters' page is opened
        When The plus button is clicked
        And User selects first library for trial summary parameter
        And User fills trial summary parameter submission code value with random, unique value
        And User fills trial summary parameter submission name value with random, unique value
        And User selects first required level for trial summary parameter
        And User fills trial summary parameter order as '1'
        And User fills trial summary parameter defintion as 'E2E Trial Summary Parameter definition'
        And Form save button is clicked
        Then The form displays a validation error for the Sponsor name

    Scenario: [Create][Negative case] User must not be able to save a new Trial Summary Parameter without the Submission Name
        Given The '/library/trial_summary_parameters' page is opened
        When The plus button is clicked
        And User fills trial summary parameter submission code value with random, unique value
        And User selects first required level for trial summary parameter
        And User fills trial summary parameter sponsor name with random, unique value
        And User fills trial summary parameter order as '1'
        And User fills trial summary parameter defintion as 'E2E Trial Summary Parameter definition'
        And Form save button is clicked
        Then The form displays a validation error for the submission name

    Scenario: [Create][Negative case] User must not be able to save a new Trial Summary Parameter without Submission Code
        Given The '/library/trial_summary_parameters' page is opened
        When The plus button is clicked
        And User selects first library for trial summary parameter
        And User selects first required level for trial summary parameter
        And User fills trial summary parameter sponsor name with random, unique value
        And User fills trial summary parameter submission name value with random, unique value
        And User fills trial summary parameter order as '1'
        And User fills trial summary parameter defintion as 'E2E Trial Summary Parameter definition'
        And Form save button is clicked
        Then The form displays a validation error for the Code

    Scenario: [Create][Negative case] User must not be able to save a new Trial Summary Parameter without the Required level
        Given The '/library/trial_summary_parameters' page is opened
        When The plus button is clicked
        And User selects first library for trial summary parameter
        And User fills trial summary parameter submission code value with random, unique value
        And User fills trial summary parameter submission name value with random, unique value
        And User fills trial summary parameter sponsor name with random, unique value
        And User fills trial summary parameter order as '1'
        And User fills trial summary parameter defintion as 'E2E Trial Summary Parameter definition'
        And Form save button is clicked
        Then The form displays a validation error for the Required level

    Scenario: [Create][Negative case] User must not be able to save a Trial Summary Parameter with a non-unique Sponsor name
        Given The '/library/trial_summary_parameters' page is opened
        When The plus button is clicked
        And User selects first library for trial summary parameter
        And User fills trial summary parameter sponsor name with already used value
        And User fills trial summary parameter submission code value with random, unique value
        And User fills trial summary parameter submission name value with random, unique value
        And User selects first required level for trial summary parameter
        And User fills trial summary parameter order as '1'
        And User fills trial summary parameter defintion as 'E2E Trial Summary Parameter definition'
        And Form save button is clicked
        Then The pop up displays 'already has a Term with name'

    Scenario: [Create][Cancel] User must be able to cancel creating a new Trial Summary Parameter
        Given The '/library/trial_summary_parameters' page is opened
        When The plus button is clicked
        And Overlay cancel button is clicked
        Then The form is no longer available