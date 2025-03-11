@REQ_ID:1074254 @manual_test
Feature: Studies - Study Design

As a system user,
I want to specify [Scenario],
So that I can make study design specification fot this type of study.

# This is describtion of the overall end-to-end test cases for study design
# Additional test cases are to be described covering more types and classess of study design
# This should at a later stage be linked to a derived classification and describtion of the specified study design
# The study design classification must be linked to SDTM.TS parameters

    Background: User is logged in and study has been selected
        Given The user is logged in   
        And A test study is selected

  Scenario: A simple parallel group design
    When 2 arms, 3 epochs, 4 elements and study design cells are defined as:
      | Arm/Epoch | Screening | Treatment | Follow-up |
      | Arm 1     | Screening | Drug A    | Follow-up |
      | Arm 2     | Screening | Drug B    | Follow-up |
    And the 'SDTM Study Design Datasets' page is opened
    Then the SDTM.TA and SDTM.TE datasets correspond to the defined simple parallel group study design

# This scenario is for later as we not yet support dose escalation
  Scenario: A parallel group design with dose escalation
    When 2 arms, 4 epochs, 4 elements and study design cells are defined as:
      | Arm/Epoch | Screening | Dose Escalation | Treatment | Follow-up |
      | Arm 1     | Screening | Drug A          | Drug A    | Follow-up |
      | Arm 2     | Screening | Drug B          | Drug B    | Follow-up |
    And the 'SDTM Study Design Datasets' page is opened
    Then the SDTM.TA and SDTM.TE datasets correspond to the defined parallel group study design with dose escalation

  Scenario: A simple crossover design
    When 2 arms, 5 epochs, 5 elements and study design cells are defined as:
      | Arm/Epoch | Screening | Treatment 1 | Wash-out | Treatment 2 | Follow-up |
      | Arm 1     | Screening | Drug A      | Wash-out | Drug B      | Follow-up |
      | Arm 2     | Screening | Drug B      | Wash-out | Drug A      | Follow-up |
    And the 'SDTM Study Design Datasets' page is opened
    Then the SDTM.TA and SDTM.TE datasets correspond to the defined simple crossover design study design