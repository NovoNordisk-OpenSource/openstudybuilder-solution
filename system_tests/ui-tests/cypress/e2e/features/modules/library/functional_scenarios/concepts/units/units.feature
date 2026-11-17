@REQ_ID:1070683
Feature: Library - Concepts - Units
    As a user, I want to manage every Unit in the Concepts Library
    Background: User must be logged in
        Given The user is logged in

    @smoke_test
    Scenario: [Create][Positive case] User must be able to add a new Unit
        Given The '/library/units' page is opened
        And Add unit button is clicked
        When The new unit is added
        And Create unit request is intercepted
        And Form save button is clicked
        And The pop up displays 'Unit added'
        And User waits for unit request to finish
        Then Unit is found
        And The newly added unit is visible within the Units table
        And The item has status 'Draft' and version '0.1'

    Scenario: [Create][Uniqueness check][Name] User must not be able to add a new Unit with already existing name
        Given The '/library/units' page is opened
        And [API] Unit in status Draft exists
        And Add unit button is clicked
        When The new unit with already existing name is added
        And Form save button is clicked
        Then The validation message appears for already existing unit name

    Scenario: [Create][Mandatory fields] User must not be able to save new unit without mandatory data provided
        Given The '/library/units' page is opened
        When Add unit button is clicked
        And Form save button is clicked
        Then The validation message appears for unit name field
        And The validation message appears for codelist term field
        And The form is not closed

    Scenario: [Actions][Edit][version 0.1] User must be able to edit the drafted version of the unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        And Unit is found
        And The 'Edit' option is clicked from the three dot menu list
        And The unit edition form is filled with data
        And Update unit request is intercepted
        And Form save button is clicked
        And The pop up displays 'Unit updated'
        And User waits for unit request to finish
        And Unit is found
        Then The item has status 'Draft' and version '0.2'

    Scenario: [Actions][Approve] User must be able to Approve the drafted version of the unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        And Unit is found
        When The 'Approve' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'

    Scenario: [Actions][Inactivate] User must be able to inactivate the approved version of the unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        When [API] Unit is approved
        And Unit is found
        When The 'Inactivate' option is clicked from the three dot menu list
        Then The item has status 'Retired' and version '1.0'

    Scenario: [Actions][Reactivate] User must be able to reactivate the inactivated version of the unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        When [API] Unit is approved
        When [API] Unit is inactivated
        And Unit is found
        When The 'Reactivate' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '1.0'

    Scenario: [Actions][New version] User must be able to add a new version for the approved unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        When [API] Unit is approved
        And Unit is found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'

    Scenario: [Actions][Edit][version 1.0] User must be able to edit and approve new version of unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        When [API] Unit is approved
        And Unit is found
        When The 'New version' option is clicked from the three dot menu list
        Then The item has status 'Draft' and version '1.1'
        When The 'Edit' option is clicked from the three dot menu list
        And The unit edition form is filled with data
        And Update unit request is intercepted
        And Form save button is clicked
        And The pop up displays 'Unit updated'
        And User waits for unit request to finish
        Then The item has status 'Draft' and version '1.2'
        When The 'Approve' option is clicked from the three dot menu list
        Then The item has status 'Final' and version '2.0'

    Scenario: [Cancel][Creation] User must be able to Cancel creation of the unit
        Given The '/library/units' page is opened
        And Add unit button is clicked
        And Unit mandatory data is filled in
        When Modal window form is closed by clicking cancel button
        And Action is confirmed by clicking continue
        Then The form is no longer available
        And The unit is not saved

    Scenario: [Cancel][Edition] User must be able to Cancel edition of the unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        And Unit is found
        When The 'Edit' option is clicked from the three dot menu list
        When The unit edition form is filled with data
        And Modal window form is closed by clicking cancel button
        And Action is confirmed by clicking continue
        Then The form is no longer available
        And The unit is not saved

    Scenario: [Actions][Availability] User must only have access correct actions depending on item state
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        And Unit is found
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Draft item are displayed
        When [API] Unit is approved
        And Unit is found
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Final item are displayed
        When [API] Unit is inactivated
        And Unit is found
        And The item actions button is clicked
        Then Only actions that should be avaiable for the Retired item are displayed

    Scenario: [Complex Unit Conversion][Toggle][Off] Verify Toggle Off for Complex Unit Conversion
        Given The '/library/units' page is opened
        When Add unit button is clicked
        Then A form for unit creation is opened
        And The Use complex unit conversion toggle is set to false

    Scenario: [Create][Toggle][On] Verify Toggle On for Complex Unit Conversion
        Given The '/library/units' page is opened
        When Add unit button is clicked
        Then A form for unit creation is opened
        When Unit mandatory data is filled in
        Then Use complex unit conversion option is enabled
        And Create unit request is intercepted
        And Form save button is clicked
        And The pop up displays 'Unit added'
        And User waits for unit request to finish

    Scenario: [Actions][Edit][Toggle][On/Off] Enable/Disable Complex Unit Conversion for Existing Unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        And Unit is found
        And The 'Edit' option is clicked from the three dot menu list
        Then A form for unit edition is opened
        And Use complex unit conversion option is enabled
        And Update unit request is intercepted
        And Form save button is clicked
        And The pop up displays 'Unit updated'
        And User waits for unit request to finish
        And The 'Edit' option is clicked from the three dot menu list
        And The Use complex unit conversion toggle is set to true
        And Use complex unit conversion option is disabled
        And Update unit request is intercepted
        And Form save button is clicked
        And The pop up displays 'Unit updated'
        And User waits for unit request to finish
        And The 'Edit' option is clicked from the three dot menu list
        And The Use complex unit conversion toggle is set to false

    Scenario: [Create][Empty conversion factor] Verify empty Conversion Factor to Master for New Unit
        Given The '/library/units' page is opened
        When Add unit button is clicked
        Then A form for unit creation is opened
        And The Conversion factor to master field is blank
        When Unit mandatory data is filled in
        And Create unit request is intercepted
        And Form save button is clicked
        And The pop up displays 'Unit added'
        And User waits for unit request to finish
        And The created unit is found in table  

    Scenario: [Actions][Edit][Numeric conversion factor] Enter Numeric Value for Conversion Factor to Master for Existing Unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        And Unit is found
        And The 'Edit' option is clicked from the three dot menu list
        And User sets convertible unit to true
        Then A form for unit edition is opened
        When Conversion factor to master is filled with numeric value
        And Update unit request is intercepted
        And Form save button is clicked
        And The pop up displays 'Unit updated'
        And User waits for unit request to finish

    Scenario: [Create][Numeric conversion factor] Verify numeric Conversion Factor to Master for New Unit
        Given The '/library/units' page is opened
        When Add unit button is clicked
        Then A form for unit creation is opened
        When Unit mandatory data is filled in
        And User sets convertible unit to true
        And Conversion factor to master is filled with numeric value
        And Create unit request is intercepted
        And Form save button is clicked
        And The pop up displays 'Unit added'
        And User waits for unit request to finish
  
    Scenario: [Actions][Edit][Non-numeric conversion factor] Verify Error for Non-Numeric Conversion Factor to Master for Existing Unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        And Unit is found
        And The 'Edit' option is clicked from the three dot menu list
        Then A form for unit edition is opened
        And User sets convertible unit to true
        When Conversion factor to master is filled with text value
        Then Conversion factor to master field is empty
        And Form save button is clicked
        And Unit is found
        Then Concersion factor to master is empty in the unit table

    Scenario: [Create][Non-numeric conversion factor] Verify Error for Non-Numeric Conversion Factor to Master for New Unit
        Given The '/library/units' page is opened
        And Add unit button is clicked
        Then A form for unit creation is opened
        When Unit mandatory data is filled in
        And User sets convertible unit to true
        And Conversion factor to master is filled with text value
        Then Conversion factor to master field is empty
        And Form save button is clicked
        And Unit is found
        Then Concersion factor to master is empty in the unit table