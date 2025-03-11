@REQ_ID:2682307

Feature: Studies - USDM

    Background: User must be logged in
        Given The user is logged in

    Scenario:  User must be able to navigate to the Study USDM page
        Given A test study is selected
        Given The '/studies' page is opened
        When The 'USDM' submenu is clicked in the 'View Specifications' section
        Then The current URL is '/studies/Study_000001/usdm'

    Scenario: User must be able to view and download USDM
        Given The '/studies/Study_000001/usdm' page is opened        
        Then Export button is available
        And A JSON text field showing the study definition in USDM format is displayed