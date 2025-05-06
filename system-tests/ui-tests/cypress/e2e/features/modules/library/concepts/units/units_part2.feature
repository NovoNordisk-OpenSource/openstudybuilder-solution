@REQ_ID:1070683
Feature: Library - Units (Part 2)
    As a user, I want to manage the Unit feature in the Library Concept, 
    for Unit Conversion and Conversion Factor Management functionalities.

    Background: User must be logged in
        Given The user is logged in

    Scenario: Verify Toggle Off for Complex Unit Conversion
        Given The '/library/units' page is opened
        When Add unit button is clicked
        Then A form for unit creation is opened
        And The Use complex unit conversion toggle is set to false

    Scenario: Verify Toggle On for Complex Unit Conversion
        Given The '/library/units' page is opened
        When Add unit button is clicked
        Then A form for unit creation is opened
        When Unit mandatory data is filled in
        Then Use complex unit conversion option is enabled
        And Unit creation is saved without errors

    Scenario: Enable/Disable Complex Unit Conversion for Existing Unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        And Unit is found
        And The 'Edit' option is clicked from the three dot menu list
        Then A form for unit edition is opened
        And Use complex unit conversion option is enabled
        And Unit editon is saved without errors
        And The 'Edit' option is clicked from the three dot menu list
        And The Use complex unit conversion toggle is set to true
        And Use complex unit conversion option is disabled
        And Unit editon is saved without errors
        And The 'Edit' option is clicked from the three dot menu list
        And The Use complex unit conversion toggle is set to false

    Scenario: Verify empty Conversion Factor to Master for New Unit
        Given The '/library/units' page is opened
        When Add unit button is clicked
        Then A form for unit creation is opened
        And The Conversion factor to master field is blank
        When Unit mandatory data is filled in
        Then Unit creation is saved without errors
        And The created unit is found in table  

    Scenario: Enter Numeric Value for Conversion Factor to Master for Existing Unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        And Unit is found
        And The 'Edit' option is clicked from the three dot menu list
        Then A form for unit edition is opened
        When Conversion factor to master is filled with numeric value
        And Unit editon is saved without errors  

    Scenario: Verify numeric Conversion Factor to Master for New Unit
        Given The '/library/units' page is opened
        When Add unit button is clicked
        Then A form for unit creation is opened
        When Unit mandatory data is filled in
        And Conversion factor to master is filled with numeric value
        Then Unit creation is saved without errors
  
    Scenario: Verify Error for Non-Numeric Conversion Factor to Master for Existing Unit
        Given The '/library/units' page is opened
        When [API] Unit in status Draft exists
        And Unit is found
        And The 'Edit' option is clicked from the three dot menu list
        Then A form for unit edition is opened
        When Conversion factor to master is filled with text value
        Then An error message appears when I save the unit

    Scenario: Verify Error for Non-Numeric Conversion Factor to Master for New Unit
        Given The '/library/units' page is opened
        And Add unit button is clicked
        Then A form for unit creation is opened
        When Unit mandatory data is filled in
        And Conversion factor to master is filled with text value
        Then An error message appears when I save the unit
        And The unit is not saved
