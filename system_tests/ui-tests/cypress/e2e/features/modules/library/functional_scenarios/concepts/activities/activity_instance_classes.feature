@REQ_ID:1070683

Feature: Library - Concepts - Activities - Activity Instance Classes
    As a user, I want to manage every Activities in the Concepts Library

    Background: User must be logged in
        Given The user is logged in
        And The '/library/activities/activity-instance-classes' page is opened


     Scenario: [Table][Row][Values] User must be able to expand activity intances class to view linked intances
        When User expands view to see linked instance class for 'GeneralObservation'
        Then Activity Instance class 'SubjectObservation' is visible in the table
        Then Activity Instance class 'Observation' is visible in the table
        When User expands view to see linked instance class for 'SubjectObservation'
        Then Activity Instance class 'SpecialPurpose' is visible in the table
        Then Activity Instance class 'Finding' is visible in the table
        Then Activity Instance class 'Event' is visible in the table
        Then Activity Instance class 'Intervention' is visible in the table
        When User expands view to see linked instance class for 'Finding'
        Then Activity Instance class 'CategoricFindings' is visible in the table
        Then Activity Instance class 'NumericFindings' is visible in the table
        Then Activity Instance class 'TextualFindings' is visible in the table