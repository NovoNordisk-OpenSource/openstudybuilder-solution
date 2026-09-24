@REQ_ID:1070684
Feature: Pre-Instantiations and Study Instantiations of template text from Syntax Templates in OpenStudyBuilder API

# This feature describes rules for how template text is to be instantiated from syntax templates
# It covers both pre-instantiations and instantiations made at study level

    Background: Test user must be able to call the OpenStudyBuilder API and test data must exist
        Given The test user can call the OpenStudyBuilder API
        And a test study identified by 'uid' is in status 'Locked' for the 'study_value_version'

Rule: As an API user
      I want the API to generate template text instantiations which follow basic text paragraph grammar
      So that the resulting text can be easily used in specification documents.

Scenario: Rules for instantiating Syntax Templates
  When a syntax template is instantiated
  And template parameter values are provided
  Then replace the template parameter in the resulting template text with the sentence case attribute of the selected template parameter value.
  And capitalize the first letter of the template parameter value if it is the first part of the syntax template.
  And if a template parameter value is not provided for a template parameter, remove the template parameter including any preceding separator and double space from the resulting template text.
  And if multiple template parameter values are selected for a template parameter, replace the template parameter in the resulting template text with the sentence case attributes of the selected template parameter values, separated by the selected separator.
  When a syntax template is instantiated with template parameter values
  Then the resulting text should:
    - Replace the template parameter with the sentence case attribute of the selected template parameter value.
    - Capitalize the first letter of the first part of the syntax template if it is a template parameter value.
    - Remove the template parameter, including any preceding separator and double space, if no template parameter value is provided for it.
    - Replace the template parameter with the sentence case attributes of the selected template parameter values, separated by the selected separator if multiple template parameter values are selected.

Examples:
  | TestID                                                                    |
  | @TestID:test_activity_instruction_pre_instance_template_parameter_rules    |
  | @TestID:test_criteria_pre_instance_template_parameter_rules                |
  | @TestID:test_endpoint_pre_instance_template_parameter_rules                |
  | @TestID:test_footnote_pre_instance_template_parameter_rules                |
  | @TestID:test_objective_pre_instance_template_parameter_rules               |