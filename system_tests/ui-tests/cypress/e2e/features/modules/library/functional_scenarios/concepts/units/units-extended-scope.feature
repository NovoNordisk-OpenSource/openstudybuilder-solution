@REQ_ID:1070683
Feature: Library - Concepts - Units (part 2)
    As a user, I want to manage the Unit feature in the Library Concept, 
    for Unit Conversion and Conversion Factor Management functionalities.

    Background: User must be logged in
        Given The user is logged in

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
        And Conversion factor to master is filled with text value
        Then Conversion factor to master field is empty
        And Form save button is clicked
        And Unit is found
        Then Concersion factor to master is empty in the unit table