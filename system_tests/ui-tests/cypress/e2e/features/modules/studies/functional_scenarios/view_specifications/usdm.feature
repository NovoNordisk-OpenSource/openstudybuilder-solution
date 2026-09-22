@REQ_ID:2682307

Feature: Studies - View Specification - USDM

    Background: User must be logged in
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'
        
    @smoke_test
    Scenario: [Navigation] User must be able to navigate to the Study USDM page
        Given The '/studies' page is opened
        When The 'USDM' submenu is clicked in the 'View Specifications' section
        Then The current URL is '/usdm'

    Scenario: [Export][Json] User must be able to download USDM in JSON format
        Given The page 'usdm' is opened for current study
        When User clicks export button
        And JSON format is selected
        Then The study specific 'USDM' file without date timestamp is downloaded in 'json' format

    Scenario: [Data][Json] User must be presented with correct USDM data
        Given User intercepts usdm request
        And The page 'usdm' is opened for current study
        When User gets data from usdm request
        Then A JSON text field showing the study definition in USDM format is displayed

    Scenario: [Online help] User must be able to read online help for the General
        Given The page 'usdm' is opened for current study        
        And The online help button is clicked
        Then The online help panel shows 'General' panel with content 'This page display the JSON file generated based on the  Digital Data Flow (DDF) CDISC / TransCelerate Unified Study Definitions Model (USDM). The data available here are extracted and converted into the USDM model, based on mapping rules defined within the OpenStudyBuilder team: Be aware about that.'

    Scenario: [Online help] User must be able to read online help for the Clinical study [C15206]
        Given The page 'usdm' is opened for current study        
        And The online help button is clicked
        Then The online help panel shows 'Clinical study [C15206]' panel with content 'A clinical study involves research using human volunteers (also called participants) that is intended to add to medical knowledge. There are two main types of clinical studies: clinical trials (also called interventional studies) and observational studies. [[http://ClinicalTrials.gov]](CDISC Glossary)'

    Scenario: [Online help] User must be able to read online help for the Official Protocol Title [C132346]
        Given The page 'usdm' is opened for current study        
        And The online help button is clicked
        Then The online help panel shows 'Official Protocol Title [C132346]' panel with content 'The formal descriptive name for the protocol.'

    Scenario: [Online help] User must be able to read online help for the Study Protocol Version [C93490]
        Given The page 'usdm' is opened for current study        
        And The online help button is clicked
        Then The online help panel shows 'Study Protocol Version [C93490]' panel with content 'A plan at a particular point in time for a formal investigation to assess the utility, impact, pharmacological, physiological, and/or psychological effects of a particular treatment, procedure, drug, device, biologic, food product, cosmetic, care plan, or subject characteristic. (BRIDG)'

    Scenario: [Online help] User must be able to read online help for the Protocol Status [C188818]
        Given The page 'usdm' is opened for current study        
        And The online help button is clicked
        Then The online help panel shows 'Protocol Status [C188818]' panel with content 'A condition of the protocol at a point in time with respect to its state of readiness for implementation. See [C188723-CDISC DDF Protocol Status Value Set Terminology]'

    Scenario: [Online help] User must be able to read online help for the Study Design [C15320]
        Given The page 'usdm' is opened for current study        
        And The online help button is clicked
        Then The online help panel shows 'Study Design [C15320]' panel with content 'A plan detailing how a study will be performed in order to represent the phenomenon under examination, to answer the research questions that have been asked, and informing the statistical approach.'

    Scenario: [Online help] User must be able to read online help for the Organization Type [C188820]
        Given The page 'usdm' is opened for current study        
        And The online help button is clicked
        Then The online help panel shows 'Organization Type [C188820]' panel with content 'A characterization or classification of the formalized group of persons or other organizations collected together for a common purpose (such as administrative, legal, political) and the infrastructure to carry out that purpose. See [C188724-CDISC DDF Organization Type Value Set Terminology]'

    Scenario: [Online help] User must be able to read online help for the page
        Given The page 'usdm' is opened for current study        
        And The online help button is clicked
        Then The online help panel shows 'Trial Type [C49660]' panel with content 'The nature of the interventional study for which information is being collected. See [C66739-CDISC SDTM Trial Type Terminology]'

    Scenario: [Online help] User must be able to read online help for the Intervention Model Type [C98746]
        Given The page 'usdm' is opened for current study        
        And The online help button is clicked
        Then The online help panel shows 'Intervention Model Type [C98746]' panel with content 'The general design of the strategy for assigning interventions to participants in a clinical study. (clinicaltrials.gov). See [C99076-CDISC SDTM Intervention Model Terminology]'

    Scenario: [Online help] User must be able to read online help for the Therapeutic Areas [C101302]
        Given The page 'usdm' is opened for current study        
        And The online help button is clicked
        Then The online help panel shows 'Therapeutic Areas [C101302]' panel with content 'A categorization of a disease, disorder, or other condition based on common characteristics and often associated with a medical specialty focusing on research and development of specific therapeutic interventions for the purpose of treatment and prevention.'

    Scenario: [Online help] User must be able to read online help for the Trial Blinding Schema [C49658]
        Given The page 'usdm' is opened for current study        
        And The online help button is clicked
        Then The online help panel shows 'Trial Blinding Schema [C49658]' panel with content 'The type of experimental design used to describe the level of awareness of the study subjects and/ or study personnel as it relates to the respective intervention(s) or assessments being observed, received or administered. See [C66735-CDISC SDTM Trial Blinding Schema Terminology]'
    
    Scenario: [Online help] User must be able to read online help for the Target Study Population [C142728]
        Given The page 'usdm' is opened for current study        
        And The online help button is clicked
        Then The online help panel shows 'Target Study Population [C142728]' panel with content 'The population within the general population to which the study results can be generalized.'