Feature: Topbar help menu

    As a system user I want to have possibility to open supporting documentation and help pages as well as have options to be redirected to related information pages.

    Scenario: User must be able to navigate to 'Need Help?' page from topbar
        Given The user is logged out
        And The homepage is opened
        When The 'topbar-help' button is clicked
        Then The Need Help? button is presented to the user with correct link to sharepoint site
