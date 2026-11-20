@REQ_ID:1070674
Feature: Library - Code Lists - Search

	Background: User must be logged in
		Given The user is logged in

	Scenario: [Table][Columns][Search] User must be able to use search functionality in the ct catalogues page
        Given The '/library/ct_catalogues/All' page is opened
        When User searches for 'xyz' and confirms no results returned
        When User searches for 'Units' without checking the result
        Then More than one result is found

	Scenario: [Table][Columns][Search] User must be able to use search functionality in the ct packages page
        Given The '/library/ct_packages' page is opened
        When User searches for 'xyz' and confirms no results returned
        When User searches for 'Depression' without checking the result
        Then More than one result is found

	Scenario: [Table][Columns][Search] User must be able to use search functionality in the sponsor page
        Given The '/library/sponsor/All' page is opened
        When User searches for 'xyz' and confirms no results returned
        When User searches for 'Visit' without checking the result
        Then More than one result is found

	Scenario: [Table][Columns][Search] User must be able to use search functionality in the terms page
        Given The '/library/terms' page is opened
        When User searches for 'xxyyzz' and confirms no results returned
        When User searches for 'BMI' without checking the result
        Then More than one result is found
