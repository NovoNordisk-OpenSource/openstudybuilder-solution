@REQ_ID:914606
Feature: Studies - Define Study - Study Properties - Other Study Attributes

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'

    @smoke_test
    Scenario: [Navigation] User must be able to navigate to Other Study Attributes
        Given The '/studies' page is opened
        When The 'Study Properties' submenu is clicked in the 'Define Study' section
        And The 'Other Study Attributes' tab is selected
        Then The current URL is '/study_properties/other_study_attributes'

    Scenario: [Table][Columns][Names] User must be able to see Other Study Attributes columns
        Given The page 'study_properties/other_study_attributes' is opened for current study
        Then A table is visible with following headers
            | headers             |
            | Code                |
            | Parameter           |
            | Reference           |
            | Required level      |
            | Semantic data type  |
            | Code list           |
            | Parameter value     |
            | Notes               |
            | Null flavor         |
            | Modified            |
            | Modified by         |

    Scenario: [Actions][Edit] User must be able to open and cancel Other Study Attributes editing
        Given The page 'study_properties/other_study_attributes' is opened for current study
        When The Other Study Attributes edit form is opened
        Then The required and optional study attribute sections are visible
        When The Other Study Attributes edit form is closed
        Then The form is no longer available

    Scenario: [Actions][Edit] User must be able to edit an Other Study Attribute
        Given [API] All Other Study Attributes assigned to the selected study are deleted
        Given The page 'study_properties/other_study_attributes' is opened for current study
        When The Other Study Attributes edit form is opened
        And User selects the first required Other Study Attribute parameter
        And User selects the first optional Other Study Attribute parameter
        And User edits the first required Other Study Attribute value
        And User intercepts the Other Study Attributes update request
        And Form save button is clicked
        And User waits for the Other Study Attributes update request
        Then The Other Study Attributes update request contains a POST operation
        And The form is no longer available
        And The pop up displays 'Other Study Attributes updated'

    Scenario: [Actions][Remove] User must be able to remove an existing Other Study Attribute
        Given [API] All Other Study Attributes assigned to the selected study are deleted
        And The page 'study_properties/other_study_attributes' is opened for current study
        When The Other Study Attributes edit form is opened
        And User selects the first required Other Study Attribute parameter
        And User selects the first optional Other Study Attribute parameter
        And User edits the first required Other Study Attribute value
        And User intercepts the Other Study Attributes update request
        And Form save button is clicked
        And User waits for the Other Study Attributes update request
        And The form is no longer available
        And User waits for Other Study Attributes table to refresh
        And The Other Study Attributes edit form is opened
        And User removes the first optional Other Study Attribute
        And User intercepts the Other Study Attributes delete request
        And Form save button is clicked
        And User waits for the Other Study Attributes delete request
        Then The Other Study Attributes delete request contains a DELETE operation
        And The form is no longer available
        And The pop up displays 'Other Study Attributes updated'

    Scenario: [Validation] User must select a parameter before saving an attribute
        Given [API] All Other Study Attributes assigned to the selected study are deleted
        And The page 'study_properties/other_study_attributes' is opened for current study
        When The Other Study Attributes edit form is opened
        And User intercepts the Other Study Attributes update request
        And Form save button is clicked
        Then The required and optional parameter validations are displayed
        And The Other Study Attributes update request was not sent

    Scenario: [Actions][Null flavor] User can use a null flavor instead of a parameter value
        Given [API] All Other Study Attributes assigned to the selected study are deleted
        And The page 'study_properties/other_study_attributes' is opened for current study
        When The Other Study Attributes edit form is opened
        And User selects the first required Other Study Attribute parameter
        And User selects the first optional Other Study Attribute parameter
        And User selects the first required Other Study Attribute null flavor
        Then The first required Other Study Attribute value is disabled and empty
        And User intercepts the Other Study Attributes update request
        And Form save button is clicked
        And User waits for the Other Study Attributes update request
        Then The Other Study Attributes update request contains a null flavor operation
        And The form is no longer available

    Scenario: [Actions][Edit and Remove] User can edit one attribute and remove another
        Given [API] All Other Study Attributes assigned to the selected study are deleted
        And The page 'study_properties/other_study_attributes' is opened for current study
        When The Other Study Attributes edit form is opened
        And User selects the first required Other Study Attribute parameter
        And User selects the first optional Other Study Attribute parameter
        And User edits the first required Other Study Attribute value
        And User intercepts the Other Study Attributes update request
        And Form save button is clicked
        And User waits for the Other Study Attributes update request
        And The form is no longer available
        And User waits for Other Study Attributes table to refresh
        And The Other Study Attributes edit form is opened
        And User edits the first required Other Study Attribute value
        And User removes the first optional Other Study Attribute
        And User intercepts the Other Study Attributes update request
        And Form save button is clicked
        And User waits for the Other Study Attributes update request
        Then The Other Study Attributes update request contains PATCH and DELETE operations
        And The form is no longer available

    Scenario: [Test data] Other Study Attributes are cleaned up after the scenarios
        Given [API] All Other Study Attributes assigned to the selected study are deleted