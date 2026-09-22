@REQ_ID:1070683
Feature: Library - Data Collection Standards - CRF Viewer

  As a user, I want to view CRFs from the data collections standards library as blank CRFs or with various annotations,
  So I can efficiently use CRFs within the StudyBuilder Library.

  Background: User must be logged in
    Given The user is logged in

  Scenario: [Navigation] User must be able to navigate to CRF View page
    Given The '/library' page is opened
    When The 'CRF Viewer' submenu is clicked in the 'Data Collection Standards' section
    Then The current URL is '/library/crf-viewer/odm-viewer'
  
  Scenario: Verifying Falcon downloadable option in the Stylesheet dropdown works as expected in the CRF Viewer menu
    Given The '/library/crf-viewer/odm-viewer' page is opened
    When User selects first value from CRF Collection dropdown
    And User selects last value from CRF Forms dropdown
    And User opens stylesheets dropdown
    Then CRF with annotations and Downloadable Falcon are available in the Stylesheet dropdown list
    And User selects Downloadable Falcon in the Stylesheet dropdown list
    And User intercepts ODM XMLS document generation request
    And User clicks the GENERATE button
    And User waits for ODM XMLS document generation request
    Then The iframe containing generated data is displayed
   
@manual_test
  Scenario: Verifying Falcon downloadable option in the Stylesheet dropdown works as expected in the CRF Viewer menu
    Given The '/library/crf-viewer/odm-viewer' page is opened
    When I select more values from the CRF collection dropdown
    And I select more values from the CRF Forms dropdown
    And I select 'Downloadable Falcon (Word)' in the Stylesheet dropdown list
    And User clicks the GENERATE button
    Then The iframe containing generated data is displayed
    When I click the 'Export data in HTML format' option
    Then The file should be downloaded successfully on the local machine
    When I open the downloaded file in Word format
    And Compare the downloaded file with the CRF view page
    Then The content and the format in both places should look exactly the same
