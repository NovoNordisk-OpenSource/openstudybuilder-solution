@REQ_ID:1070683
Feature: Library - Data Collection Standards - CRF Builder - CRF Viewer

  As a user, I want to view CRFs from the data collections standards library as blank CRFs or with various annotations,
  So I can efficiently manage and maintain CRFs within the StudyBuilder Library.

  Background: User must be logged in
    Given The user is logged in

  Scenario: [Navigation] User must be able to navigate to CRF View page
    Given The '/library' page is opened
    When The 'CRF Builder' submenu is clicked in the 'Data Collection Standards' section
    And The 'CRF Viewer' tab is selected
    Then The current URL is '/library/crf-builder/odm-viewer'
 
   Scenario: Verify the HTML option in the Stylesheet dropdown works as expected
    Given The '/library/crf-builder/odm-viewer' page is opened
    When User selects first value from the Form Name dropdown
    And User opens stylesheets dropdown
    And User selects HTML option from the Stylesheet dropdown list
    And User intercepts ODM document generation request
    And User clicks the GENERATE button
    Then User waits for ODM document generation request

  Scenario: Verifying that the Falcon downloadable option in the Stylesheet dropdown works as expected
    Given The '/library/crf-builder/odm-viewer' page is opened
    When User selects first value from the Form Name dropdown
    And User opens stylesheets dropdown
    And User selects Downloadable Falcon in the Stylesheet dropdown list
    And User intercepts ODM XMLS document generation request
    And User clicks the GENERATE button
    Then User waits for ODM XMLS document generation request
  