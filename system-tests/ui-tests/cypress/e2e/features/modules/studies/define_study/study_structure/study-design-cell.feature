@REQ_ID:1074254 @manual_test
Feature: Studies - Study Design Cell

   As a system user,
   I want the system to ensure to [Scenario],
   So that I can make complete and consistent study design specifications.

   #Audit trial - add the specification & discuss 

   Background: User is logged in and study has been selected
      Given The user is logged in   
      And A test study is selected

   Scenario: User must be able to open the page for Study Design Matrix
      Given The '/studies' page is opened
      When The 'Study Structure' submenu is clicked in the 'Define Study' section
      And The 'Design Matrix' tab is clicked
      Then The current URL is '/studies/study_structure/design_matrix'

   Scenario: User must be able to see the page structure for Study Design Matrix
      Given The '/studies/study_structure/design_matrix' page is opened
      Then A table is visible with following headers
         | headers          |
         | Study Arm        |
         #Branch arm or Branches?
         | Study Branch Arm | 
         | [Study Epoch]    |
   # Note, the number of epoch columns are dynamic depending of the data for the study!
   # Should we add an order column?

   Scenario: User must be able to see the structure of Study Design Matrix page
      Given The '/studies/study_desgin/design_matrix' page is opened
      Then The table with search bar, actions and select rows options is visible

   Scenario:  User must be able to see the table options on Study Design Matrix page
      Given The '/studies/study_desgin/design_matrix' page is opened
      When The table actions button is clicked
      Then The filters, export data, version history and Edit Study Design Matrix are visible
   # Note, no Add in this context for Study Design Matrix

   Scenario: User must be able to view the Display guidance when no study arms and epochs has been defined
      Given no Study Arms and Study Epochs has been defined for the study
      Then the page display an empty table with the note: No data available - Create first Study Arms and Study Epochs
      And the Edit and Download function is disabled

   Scenario: User must be able to view Display guidance when only study epochs has been defined
      Given no Study Arms has been defined for the study, only study epochs
      Then the page display an empty table
      And the NOTE: No Study Arms are defined - Create Study Arms
      And the Edit and Download function is disabled

   #Below two are example for breakdown
   Scenario: User must be able to view Display guidance when only study arms has been defined
      Given no Study Epochs has been defined for the study, only Study Arms
      And Study Branch Arm has been defined
      Then the page display an simple table with with one row per study arm listing the following columns:
         | Column               |
         | # (the order number) |
         | Study Arm            |
         | Study Branch Arm     |
      And A row is displayed for each branch arm related to the arm
      And the NOTE: No Study Epochs are defined - Create Study Epochs
      And the Edit and Download function is disabled

   Scenario: User must be able to view Display guidance when only study arms has been defined
      Given no Study Epochs has been defined for the study, only Study Arms
      And no Study Branch Arm has been defined
      Then the page display an simple table with with one row per study arm listing the following columns:
         | Column               |
         | # (the order number) |
         | Study Arm            |
         | Study Branch Arm     |
      And a row is displayed for the Study Arm 
      And the column value for Study Branch Arm is blank
      And the NOTE: No Study Epochs are defined - Create Study Epochs
      And the Edit and Download function is disabled

   Scenario: User must be able to view Display guidance when no Study Elements has been defined
      Given Study Arms and Study Epochs are defined, but no Study Elements
      Then the page display a simple table with one row per study arm first listing the following columns:
         | Column               |
         | # (the order number) |
         | Study Arm            |
         | Study Branch Arm     |
         | [Study Epoch]        |
      And then listing a column for each defined Study Epoch
      And all Study Epoch column values are empty for all rows
      And the NOTE: No Study Elements are defined - Create Study Elements
      And the Edit and Download function is disabled

   Scenario: User must be able to view Display guidance when no Study Design Cell selections has been made
      Given Study Arms, Study Epochs and Study Elements are defined, but no Study Design Cell selections has been made
      Then the page display a simple table with one row per study arm first listing the following columns:
         | Column               |
         | # (the order number) |
         | Study Arm            |
         | Study Branch Arm     |
         | [Study Epoch]        |
      And then listing a column for each defined Study Epoch
      
      
      And all Study Epoch column values are empty for all rows
      And the NOTE: No Study Design Cells are defined - Select Edit to select Study Elements for each Study Design Matrix Cell
      And the Edit and Download function is disabled

#Decide if study design cell could be connected to arm or branch arm or at least one of them
#What's the approach on saving the cells incomplete (defaults, validation or something else)
   Scenario: User must be able to view Display guidance when incomplete Study Design Cell selections has been made
      Given Study Arms, Study Epochs and Study Elements are defined, but not all Study Design Cell selections has been made
      Then the page display a simple table with one row per study arm first listing the following columns:
         | Column               |
         | # (the order number) |
         | Study Arm            |
         | Study Branch Arm     |
         | [Study Epoch]        |
      And then listing a column for each defined Study Epoch
      And some Study Epoch column values show selected Study Element when these has been selected for a Study Design Matrix Cell
      And the NOTE: Not all Study Design Cells are defined - Select Edit to select Study Elements for each Study Design Matrix Cell
      And the Edit and Download function is disabled

   Scenario: User must be able to view Display guidance when complete Study Design Cell selections has been made
      Given Study Arms, Study Epochs and Study Elements are defined and all Study Design Cell selections has been made
      Then the page display a simple table with one row per study arm first listing the following columns:
         | Column               |
         | # (the order number) |
         | Study Arm            |
         | Study Branch Arm     |
         | [Study Epoch]        |
      And then listing a column for each defined Study Epoch
      And all Study Epoch column values show selected Study Element for each Study Design Matrix Cell
      And the NOTE: All Study Design Cells are defined - Select Edit to change a Study Element for Study Design Matrix Cell
      And the Edit and Download function is disabled

   Scenario: User must be able to enable edit of Study Design Matrix Cell selections
      Given Study Arms, Study Epochs and Study Elements are defined
      When the user selects the Edit Study Design Matrix Cell function
      Then the Edit Study Design Matrix Cell page is displayed
      And the page display a editable form table with one row per study arm first listing the following columns:
      ###### We need to clarify how we display and edit transition rules (a simple text field) ######
         | Column               |
         | # (the order number) |
         | Study Arm            |
         | Study Branch Arm     |
         | [Study Epoch]        |
      And then listing a column for each defined Study Epoch
      And all Study Epoch column values show selected Study Element in drop down box for each Study Design Matrix Cell
      # Later we will add rules so not all combinations can be made!
      And each drop down selection box contains all valid Study Elements defined for the study
      And the user can change selections of Study Element value in any Study Design Matrix Cell
      And the CANCEL button will give the option to leave the page without saving data changes returning to the data display
      And the SAVE button will give the option to save the data changes and return to the data display

   Scenario: User must be able to save updated Study Design Matrix Cell
      Given the user is on the Edit Study Design Matrix Cell page
      And have updated the Study Design Matrix Cell values
      When the user selects SAVE
      Then the updated the Study Design Matrix Cell values must be saved in the repository
      And the page display a simple table with one row per study arm first listing the following columns:
         | Column               |
         | # (the order number) |
         | Study Arm            |
         | Study Branch Arm     |
         | [Study Epoch]        |
      And then listing a column for each defined Study Epoch
      And all Study Epoch column values show the updated selected Study Element for each Study Design Matrix Cell
      And if all Study Design Cells have values then the NOTE: All Study Design Cells are defined - Select Edit to change a Study Element for Study Design Matrix Cell
      And if all Study Design Cells not have values then the NOTE: Not all Study Design Cells are defined - Select Edit to select Study Elements for each Study Design Matrix Cell
      And the Edit and Download function is disabled

   Scenario: User must be able to cancel updated Study Design Matrix Cell
      Given the user is on the Edit Study Design Matrix Cell page
      And the user have updated the Study Design Matrix Cell values
      When the user selects CANCEL
      Then an notification message should be displayed to the user
      And if user selects Continue then then the Edit Study Design Matrix Cell page is closed with out saving
      And the page display a simple table with one row per study arm first listing the following columns:
         | Column               |
         | # (the order number) |
         | Study Arm            |
         | [Study Epoch]        |
      And then listing a column for each defined Study Epoch
      And all Study Epoch column values show the previous selected Study Element for each Study Design Matrix Cell
      And if all Study Design Cells have values then the NOTE: All Study Design Cells are defined - Select Edit to change a Study Element for Study Design Matrix Cell
      And if all Study Design Cells not have values then the NOTE: Not all Study Design Cells are defined - Select Edit to select Study Elements for each Study Design Matrix Cell
      And the Edit and Download function is disabledz
