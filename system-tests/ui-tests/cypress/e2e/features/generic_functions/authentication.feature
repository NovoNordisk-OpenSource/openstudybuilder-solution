Feature: Authentication

    As a system user I want to be able to log into the system using the login options so that I can verify 
    my identity and work within the protected environment.

    Scenario: User must be able to login via top navigation bar
        Given The user is logged out
        And The homepage is opened
        Then The 'topbar-login' element is visible
        And The user can navigate to authentication provider via top bar login button
        And The 'Studies' button is not visible
        And The 'Library' button is not visible

    Scenario: User must be able to access the system after authenticating
        Given The user is logged in
        And The homepage is opened
        Then The 'topbar-admin-icon' element is visible
        And The 'topbar-help' element is visible
        And The 'topbar-login' button is not visible

    Scenario: User must be able to log out of the system
        Given The user is logged in
        And The homepage is opened
        Then The top bar button has logout option available