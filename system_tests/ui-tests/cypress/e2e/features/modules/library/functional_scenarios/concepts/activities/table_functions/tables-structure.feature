@REQ_ID:1070683

Feature: Library - Concepts - Activities - Tables
    As a user I want to navigate to each page

    Background: User must be logged in
        Given The user is logged in

    Scenario: [Table][Options] User must be able to see activities table with correct options
        Given The '/library/activities/activities' page is opened
        Then A table is visible with following options
            | options                                            |
            | add-activity                                       |
            | filters-button                                     |
            | columns-layout-button                              |
            | table-export-button                                |
            | select-rows                                        |
            | search-field                                       |
            | History                                            |

    Scenario: [Table][Options] User must be able to see activity groups table with correct options
        Given The '/library/activities/activity-groups' page is opened
        Then A table is visible with following options
            | options                                            |
            | add-activity                                       |
            | filters-button                                     |
            | columns-layout-button                              |
            | table-export-button                                |
            | select-rows                                        |
            | search-field                                       |
            | History                                            |

    Scenario: [Table][Options] User must be able to see activity subgroups table with correct options
        Given The '/library/activities/activity-subgroups' page is opened
        Then A table is visible with following options
            | options                                            |
            | add-activity                                       |
            | filters-button                                     |
            | columns-layout-button                              |
            | table-export-button                                |
            | select-rows                                        |
            | search-field                                       |
            | History                                            |

    Scenario: [Table][Options] User must be able to see activity instances table with correct options
        Given The '/library/activities/activity-instances' page is opened
        Then A table is visible with following options
            | options                                            |
            | add-activity                                       |
            | filters-button                                     |
            | columns-layout-button                              |
            | table-export-button                                |
            | select-rows                                        |
            | search-field                                       |
            | History                                            |

    Scenario: [Table][Options] User must be able to see requested activities table with correct options
        Given The '/library/activities/requested-activities' page is opened
        Then A table is visible with following options
            | options                                            |
            | filters-button                                     |
            | columns-layout-button                              |
            | table-export-button                                |
            | select-rows                                        |
            | search-field                                       |
            | History                                            |

    Scenario: [Table][Options] User must be able to see activity instance classes table with correct options
        Given The '/library/activities/activity-instance-classes' page is opened
        Then A table is visible with following options
            | options                                            |
            | table-export-button                                |
            | History                                            |

    Scenario: [Table][Options] User must be able to see activity item classes table with correct options
        Given The '/library/activities/activity-item-classes' page is opened
        Then A table is visible with following options
            | options                                            |
            | filters-button                                     |
            | columns-layout-button                              |
            | table-export-button                                |
            | select-rows                                        |
            | search-field                                       |
            | History                                            |

     Scenario: [Table][Columns][Names] User must be able to see activities table with correct columns
        Given The '/library/activities/activities' page is opened
        And A table is visible with following headers
            | headers            |
            | Library            |
            | Activity group     |
            | Activity subgroup  |
            | Activity name      |
            | Sentence case name |
            | Synonyms           |     
            | NCI Concept ID     |
            | NCI Concept Name   |
            | Abbreviation       |
            | Data collection    |
            | Legacy usage       |
            | Modified           |
            | Modified by        |
            | Status             |
            | Version            |

    Scenario: [Table][Columns][Names] User must be able to see activity groups table with correct columns
        Given The '/library/activities/activity-groups' page is opened
        Then A table is visible with following headers
            | headers            |
            | Activity group     |
            | Sentence case name |
            | Abbreviation       |
            | Definition         |
            | Modified           |
            | Status             |
            | Version            |

    Scenario: [Table][Columns][Names] User must be able to see activity subgroups table with correct columns
        Given The '/library/activities/activity-subgroups' page is opened
        Then A table is visible with following headers
            | headers            |
            | Activity subgroup  |
            | Sentence case name |
            | Abbreviation       |
            | Definition         |
            | Modified           |
            | Status             |
            | Version            |

    Scenario: [Table][Columns][Names] User must be able to see activity instances table with correct columns
        Given The '/library/activities/activity-instances' page is opened
        Then A table is visible with following headers
            | headers                       |
            | Library                       |
            | Activity instance class       |
            | Activity                      |
            | Activity Instance             |
            | NCI Concept ID                |
            | NCI Concept Name              |
            | Research Lab                  |
            | Molecular Weight              |
            | Topic code                    |
            | ADaM parameter code           |
            | Required for activity         |
            | Default selected for activity |
            | Data sharing                  |
            | Legacy usage                  |
            | Modified                      |
            | Modified by                   |
            | Status                        |
            | Version                       |

    Scenario: [Table][Columns][Names] User must be able to see requested activities table with correct columns
        Given The '/library/activities/requested-activities' page is opened
        Then A table is visible with following headers
            | headers                        |
            | Activity group                 |
            | Activity subgroup              |
            | Activity                       |
            | Sentence case name             |
            | Abbreviation                   |
            | Definition                     |
            | Rationale for activity request |
            | Modified                       |
            | Modified by                    |
            | Status                         |
            | Version                        |

    Scenario: [Table][Columns][Names] User must be able to see activity instance classes table with correct columns
        Given The '/library/activities/activity-instance-classes' page is opened
        Then A table is visible with following headers
            | headers          |
            | Name             |
            | Definition       |
            | Domain specific  |
            | Library          |
            | Modified         |
            | Modified by      |     
            | Version          |
            | Status           |

     Scenario: [Table][Columns][Names] User must be able to see activity item classes table with correct columns
        Given The '/library/activities/activity-item-classes' page is opened
        Then A table is visible with following headers
            | headers          |
            | Name             |
            | Definition       |
            | NCI Code         |
            | Modified         |
            | Modified by      |     
            | Version          |
            | Status           |

    Scenario: [Table][Columns][Visibility] User must be able to select visibility of columns in the activities table
        Given The '/library/activities/activities' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visibility] User must be able to select visibility of columns in the activity groups table
        Given The '/library/activities/activity-groups' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visibility] User must be able to select visibility of columns in the activity subgroup table
        Given The '/library/activities/activity-subgroups' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visibility] User must be able to select visibility of columns in the activity instances table
        Given The '/library/activities/activity-instances' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visibility] User must be able to select visibility of columns in the requested activities table 
        Given The '/library/activities/requested-activities' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Columns][Visibility] User must be able to select visibility of columns in the activity item classes table
        Given The '/library/activities/activity-item-classes' page is opened
        When The first column is selected from Select Columns option for table with actions
        Then The table contain only selected column and actions column

    Scenario: [Table][Pagination] User must be able to use activities table pagination
        Given The '/library/activities/activities' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    Scenario: [Table][Pagination] User must be able to use activity groups table pagination
        Given The '/library/activities/activity-groups' page is opened
        When The user switches pages of the table
        Then The table page presents correct data
    
    Scenario: [Table][Pagination] User must be able to use activity subgroups table pagination
        Given The '/library/activities/activity-subgroups' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    Scenario: [Table][Pagination] User must be able to use activity instances table pagination
        Given The '/library/activities/activity-instances' page is opened
        When The user switches pages of the table
        Then The table page presents correct data

    Scenario: [Table][Pagination] User must be able to use activity item classes table pagination
        Given The '/library/activities/activity-item-classes' page is opened
        When The user switches pages of the table
        Then The table page presents correct data