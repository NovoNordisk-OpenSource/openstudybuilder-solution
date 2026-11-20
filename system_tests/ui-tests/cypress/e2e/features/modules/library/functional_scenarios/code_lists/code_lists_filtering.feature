@REQ_ID:1070674
Feature: Library - Code Lists - Search

	Background: User must be logged in
		Given The user is logged in

        Scenario Outline: [Table][Filtering] User must be able to filter in the ct catalogues page
                Given The '/library/ct_catalogues/All' page is opened
                When The user filters field '<name>'
                Then The table is filtered correctly

                Examples:
                | name                  |
                | Library               |
                | Sponsor preferred name|
                | Type                  |
                | Template parameter    |
                | Ordinal               |
                | Code list status      |
                #| Name modified         |
                | Concept ID            |
                | Submission value      |
                | Code list name        |
                | NCI Preferred name    |
                | Paired with           |
                | Extensible            |
                | Attributes status     |

	Scenario: [Table][Filtering] User must be able to filter in the ct packages page
                Given The '/library/ct_packages' page is opened
                When The user filters field '<name>'
                Then The table is filtered correctly

                Examples:
                | name                  |
                | Library               |
                | Sponsor preferred name|
                | Type                  |
                | Template parameter    |
                | Ordinal               |
                | Code list status      |
                #| Name modified         |
                | Concept ID            |
                | Submission value      |
                | Code list name        |
                | NCI Preferred name    |
                | Paired with           |
                | Extensible            |
                | Attributes status     |

	Scenario: [Table][Filtering] User must be able to filter in the sponsor page
                Given The '/library/sponsor/All' page is opened
                When The user filters field '<name>'
                Then The table is filtered correctly

                Examples:
                | name                  |
                | Library               |
                | Sponsor preferred name|
                | Type                  |
                | Template parameter    |
                | Ordinal               |
                | Code list status      |
                #| Name modified         |
                | Concept ID            |
                | Submission value      |
                | Code list name        |
                | NCI Preferred name    |
                #| Paired with           |
                | Extensible            |
                | Attributes status     |

	Scenario: [Table][Filtering] User must be able to filter in the terms page
                Given The '/library/terms' page is opened
                When The user filters field '<name>'
                Then The table is filtered correctly

                Examples:
                | name                          |
                | Library                       |
                | Sponsor name                  |
                | Name status                   |
                #| Name date                     |
                | Concept ID                    |
                | Code list names               |
                | Code list submission values   |
                | Submission values             |
                | NCI Preferred name            |
                | Definition                    |
                | Attributes status             |

