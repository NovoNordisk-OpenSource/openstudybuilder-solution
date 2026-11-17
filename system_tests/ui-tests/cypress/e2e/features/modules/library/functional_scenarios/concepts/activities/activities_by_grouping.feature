@REQ_ID:1070683
Feature: Library - Concepts - Activities - Activities by grouping
    As a user, I want to manage every Activities by Grouping items in the Concepts Library
    
    Background: User must be logged in
        Given The user is logged in

    Scenario: User must be able to expand display of rows for the Group/subgroup/activity column
        Given The '/library/activities/activities-by-grouping' page is opened
        When User expands activity groupings for group 'Adverse Event' and subgroup 'Adverse Event'
        Then User sees linked activity 'Adverse Event' in the activities by grouping table

    @manual_test @BUG_ID:2770368
    Scenario:[BUG] Activities by Grouping should present correct group/subgroup combinations
