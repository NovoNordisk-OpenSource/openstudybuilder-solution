@REQ_ID:1070684 @smoke_test

Feature: Library - Syntax Templates - Tables
    As a user I want to navigate to each page

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Table][Columns][Names] User must be able to see the Parent Objective Templates table with correct columns
        Given The '/library/objective_templates/parent' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the Pre-instnace Objective Templates table with correct columns
        Given The '/library/objective_templates/pre-instances' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the User Defined Objective Templates table with correct columns
        Given The '/library/objective_templates/user' page is opened
        Then A table is visible with following headers
            | headers         |
            | Template        |
            | Modified        |
            | Modified by     |

    Scenario: [Table][Columns][Names] User must be able to see the Parent Endpoint Templates table with correct columns
        Given The '/library/endpoint_templates/parent' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the Pre-instnace Endpoint Templates table with correct columns
        Given The '/library/endpoint_templates/pre-instances' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the User Defined Endpoint Templates table with correct columns
        Given The '/library/endpoint_templates/user' page is opened
        Then A table is visible with following headers
            | headers         |
            | Template        |
            | Modified        |
            | Modified by     |

    Scenario: [Table][Columns][Names] User must be able to see the Parent Timeframe Templates table with correct columns
        Given The '/library/timeframe_templates/parent' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Template        |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the User Defined Timeframe Templates table with correct columns
        Given The '/library/timeframe_templates/user' page is opened
        Then A table is visible with following headers
            | headers         |
            | Template        |
            | Modified        |
            | Modified by     |


    Scenario: [Table][Columns][Names] User must be able to see the Parent Dosing Criteria Templates table with correct columns
        Given The '/library/criteria_templates/Dosing/parent' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the Pre-instnace Dosing Criteria Templates table with correct columns
        Given The '/library/criteria_templates/Dosing/pre-instances' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the User Defined Dosing Criteria Templates table with correct columns
        Given The '/library/criteria_templates/Dosing/user' page is opened
        Then A table is visible with following headers
            | headers         |
            | Template        |
            | Modified        |
            | Modified by     |

    Scenario: [Table][Columns][Names] User must be able to see the Parent Exclusion Criteria Templates table with correct columns
        Given The '/library/criteria_templates/Exclusion/parent' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the Pre-instnace Exclusion Criteria Templates table with correct columns
        Given The '/library/criteria_templates/Exclusion/pre-instances' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the User Defined Exclusion Criteria Templates table with correct columns
        Given The '/library/criteria_templates/Exclusion/user' page is opened
        Then A table is visible with following headers
            | headers         |
            | Template        |
            | Modified        |
            | Modified by     |

    Scenario: [Table][Columns][Names] User must be able to see the Parent Inclusion Criteria Templates table with correct columns
        Given The '/library/criteria_templates/Inclusion/parent' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the Pre-instnace Inclusion Criteria Templates table with correct columns
        Given The '/library/criteria_templates/Inclusion/pre-instances' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the User Defined Inclusion Criteria Templates table with correct columns
        Given The '/library/criteria_templates/Inclusion/user' page is opened
        Then A table is visible with following headers
            | headers         |
            | Template        |
            | Modified        |
            | Modified by     |
            
    Scenario: [Table][Columns][Names] User must be able to see the Parent Randomisation Criteria Templates table with correct columns
        Given The '/library/criteria_templates/Randomisation/parent' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the Pre-instnace Randomisation Criteria Templates table with correct columns
        Given The '/library/criteria_templates/Randomisation/pre-instances' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the User Defined Randomisation Criteria Templates table with correct columns
        Given The '/library/criteria_templates/Randomisation/user' page is opened
        Then A table is visible with following headers
            | headers         |
            | Template        |
            | Modified        |
            | Modified by     |

    Scenario: [Table][Columns][Names] User must be able to see the Parent Run-in Criteria Templates table with correct columns
        Given The '/library/criteria_templates/Run-in/parent' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the Pre-instnace Run-in Criteria Templates table with correct columns
        Given The '/library/criteria_templates/Run-in/pre-instances' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the User Defined Run-in Criteria Templates table with correct columns
        Given The '/library/criteria_templates/Run-in/user' page is opened
        Then A table is visible with following headers
            | headers         |
            | Template        |
            | Modified        |
            | Modified by     |

    Scenario: [Table][Columns][Names] User must be able to see the Parent Withdrawal Criteria Templates table with correct columns
        Given The '/library/criteria_templates/Withdrawal/parent' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the Pre-instnace Withdrawal Criteria Templates table with correct columns
        Given The '/library/criteria_templates/Withdrawal/pre-instances' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the User Defined Withdrawal Criteria Templates table with correct columns
        Given The '/library/criteria_templates/Withdrawal/user' page is opened
        Then A table is visible with following headers
            | headers         |
            | Template        |
            | Modified        |
            | Modified by     |
            
    Scenario: [Table][Columns][Names] User must be able to see the Parent Withdrawal Criteria Templates table with correct columns
        Given The '/library/activity_instruction_templates/parent' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the Pre-instnace Withdrawal Criteria Templates table with correct columns
        Given The '/library/activity_instruction_templates/pre-instances' page is opened
        Then A table is visible with following headers
            | headers         |
            | Sequence number |
            | Parent template |
            | Modified        |
            | Status          |
            | Version         |

    Scenario: [Table][Columns][Names] User must be able to see the User Defined Withdrawal Criteria Templates table with correct columns
        Given The '/library/activity_instruction_templates/user' page is opened
        Then A table is visible with following headers
            | headers         |
            | Template        |
            | Modified        |
            | Modified by     |

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/objective_templates/parent' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/objective_templates/pre-instances' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/objective_templates/user' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/endpoint_templates/parent' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/endpoint_templates/pre-instances' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/endpoint_templates/user' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/timeframe_templates/parent' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/timeframe_templates/user' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/criteria_templates/Dosing/parent' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/criteria_templates/Dosing/pre-instances' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/criteria_templates/Dosing/user' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/criteria_templates/Exclusion/parent' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/criteria_templates/Exclusion/pre-instances' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/criteria_templates/Exclusion/user' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/criteria_templates/Inclusion/parent' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/criteria_templates/Inclusion/pre-instances' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/criteria_templates/Inclusion/user' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column
        
    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/criteria_templates/Randomisation/parent' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/criteria_templates/Randomisation/pre-instances' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/criteria_templates/Randomisation/user' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/criteria_templates/Run-in/parent' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/criteria_templates/Run-in/pre-instances' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/criteria_templates/Run-in/user' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/criteria_templates/Withdrawal/parent' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/criteria_templates/Withdrawal/pre-instances' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/criteria_templates/Withdrawal/user' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/activity_instruction_templates/parent' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/activity_instruction_templates/pre-instances' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visiblity] User must be able to select visibility of columns in the table
        Given The '/library/activity_instruction_templates/user' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column

    Scenario: [Table][Pagination] User must be able to use table pagination        
        Given The '/library/objective_templates/parent' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    Scenario: [Table][Pagination] User must be able to use table pagination        
        Given The '/library/endpoint_templates/parent' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    Scenario: [Table][Pagination] User must be able to use table pagination        
        Given The '/library/timeframe_templates/parent' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    Scenario: [Table][Pagination] User must be able to use table pagination        
        Given The '/library/criteria_templates/Dosing/parent' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    Scenario: [Table][Pagination] User must be able to use table pagination        
        Given The '/library/criteria_templates/Exclusion/parent' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    Scenario: [Table][Pagination] User must be able to use table pagination        
        Given The '/library/criteria_templates/Inclusion/parent' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    Scenario: [Table][Pagination] User must be able to use table pagination        
        Given The '/library/criteria_templates/Randomisation/parent' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    Scenario: [Table][Pagination] User must be able to use table pagination        
        Given The '/library/criteria_templates/Run-in/parent' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    Scenario: [Table][Pagination] User must be able to use table pagination        
        Given The '/library/criteria_templates/Withdrawal/parent' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    Scenario: [Table][Pagination] User must be able to use table pagination        
        Given The '/library/activity_instruction_templates/parent' page is opened
        When The user switches pages of the table
        Then The table page presents correct data