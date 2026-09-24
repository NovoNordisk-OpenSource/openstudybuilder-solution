@REQ_ID:1070683
Feature: Library - Concepts - CRFs from Veeva EDC

  As a user, I want to verify that the CRFs Library exported from Veeva EDC Libary are correctly displayed
  so that I can ensure the integrity and accuracy of the CRF data within the StudyBuilder CRF Library.

  Background: User must be logged in
    Given The user is logged in

@manual_test
  Scenario: CRFs must be exported exactly the same numbers of forms, items and item groups from Veeva EDC to StudyBuilder CRF Library
    When I view the StudyBuilder CRF 'Forms' tab
    And The number of 'Forms' in the CRF library should match the number in Veeva EDC library
    When I view the StudyBuilder CRF 'Item Groups' tab
    Then The number of 'Item Groups' in the CRF library should match the number in Veeva EDC library
    When I view the StudyBuilder CRF 'Items' tab
    Then The number of 'Items' in the CRF library should match the number in Veeva EDC library

@manual_test
  Scenario: Verify Primary Properties of CRF Items between Veeva EDC and CRF Library
    When I view the StudyBuilder CRF 'Forms' tab
    And The imported form 'Vital Sign' should be visible in the StudyBuilder CRF forms library
    When I view the StudyBuilder CRF 'Items' tab
    And  I search for 'I.PULSE' in the search field
    Then The imported item 'I.PULSE' should have the same values as item in Veeva EDC, including OID, Name, Description, Type and Length. 
    When I select on Edit option from the three dot menu of the item 'I.PULSE'
    Then The item detail page should be opened
    And The item OID, Name and description displayed should match the item name in Veeva EDC library

  @manual_test
  Scenario: Verify Additional Properties of CRF Items between Veeva EDC and CRF Library  
    When I view the StudyBuilder CRF 'Items' tab
    And I search for item with data type: 'Float', such as 'VSORRES_TEMP'
    And I select on Edit option from the three dot menu of this item
    And The item detail page should be opened
    Then The length should be the same as in Veeva EDC library, 
    # e.g. in Veeva, the length is 4 and the decimal is 2; 
    # in CRF library, the length is 4 and the Significant digits is 6 
    # (the Significant digits should be length plus decimal)
    When I search for item with data type: 'Integer', such as 'VSORRES_RESP'
    And I select on Edit option from the three dot menu of this item
    And The item detail page should be opened
    Then The length should be the same as in Veeva EDC library
    # e.g. in Veeva, the length is 2 and the decimal is 0; 
    # in CRF library, the length is 2 and the Significant digits should be not exist

@manual_test
  Scenario: Verify Properties of CRF Item Groups between Veeva EDC and CRF Library
    When I view the StudyBuilder CRF 'Item Groups' tab
    And  I search for 'G.VS.BPP' in the search field
    Then The imported item groups 'G.VS.BPP' should have the same values as in Veeva EDC, including OID, Name, Description and Repeating.

