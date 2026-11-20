@REQ_ID:1074254
Feature: Studies - Define Study - Study Structure - Study Visits - Timeline View

    See shared notes for study visits in file study-visit-intro-notes.txt

    As a system user,
    I want the system to ensure [Scenario],
    So that I can make complete and consistent specification of study visits.

    Background: User is logged in and study has been selected
        Given The user is logged in
        And User selects study with id 'CDISC DEV-9876'
        Given [API] All visit groups uids are fetched
        And [API] All visit groups are removed
        And [API] Study vists uids are fetched for selected study
        When [API] Study visits in selected study are cleaned-up
        Given [API] The epoch with type 'Pre Treatment' and subtype 'Screening' exists in selected study
        Given [API] The epoch with type 'Treatment' and subtype 'Intervention' exists in selected study


    Scenario: [Timeline][Empty State] User must be able to see no visists defined state in timeline view for study with no visits
        And The page 'study_structure/visits' is opened for current study
        Then The study visits timeline view shows no visits defined for the current study with a message "You have not added any Study Visits yet. Click the button to add your first Visit."
        And The create study visit button is visible

    Scenario: [Timeline][Create Visit] User must be able to create a Manually defined visit
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitClass        | Manually defined visit |
            | visitType         | Screening              |
            | contactMode       | Phone Contact          |
            | timeReference     | Global anchor visit    |
            | timing            | 1                      |
            | timeUnit          | days                   |
            | visitName         | Fully Defined Visit    |
            | visitShortName    | V1                     |
            | uniqueVisitNumber | 1                      |
            | visitWindowUnit   | days                   |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved
        Then The visit 'V1' is visible in the Study Visits timeline view:
            | visitType   | Screening |
            | studyDay    | 1         |
            | studyWeek   | 0         |
            | visitWindow | ±0D       |

    Scenario: [Timeline][Create Visit] User must be able to create a Global anchor visit visit
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitClass      | Global anchor visit |
            | visitType       | Screening           |
            | contactMode     | Phone Contact       |
            | timeUnit        | days                |
            | visitWindowUnit | days                |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved
        Then The visit 'P1' is visible in the Study Visits timeline view:
            | visitType   | Screening |
            | studyDay    | 0         |
            | studyWeek   | 0         |
            | visitWindow | ±0D       |

    Scenario: [Timeline][Create Visit] User must be able to create a Anchor visit in visit group
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitClass      | Anchor visit in visit group |
            | visitType       | Screening                   |
            | contactMode     | Phone Contact               |
            | timeReference   | Global anchor visit         |
            | timing          | 1                           |
            | timeUnit        | days                        |
            | visitSuffix     | Group                       |
            | visitWindowUnit | days                        |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved
        Then The visit 'P1Group' is visible in the Study Visits timeline view:
            | visitType   | Screening |
            | studyDay    | 1         |
            | studyWeek   | 0         |
            | visitWindow | ±0D       |

    Scenario: [Timeline][Create Visit] User must be able to create a Repeating visit
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitClass         | Repeating visit |
            | visitType          | Screening       |
            | contactMode        | Phone Contact   |
            | timing             | 1               |
            | timeUnit           | days            |
            | visitSuffix        | REPEAT          |
            | visitWindowUnit    | days            |
            | repeatingFrequency | Daily           |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved
        Then The visit 'P1REPEAT.n' is visible in the Study Visits timeline view:
            | visitType   | Screening |
            | studyDay    | 1         |
            | studyWeek   | 0         |
            | visitWindow | ±0D       |

    Scenario: [Timeline][Create Visit] User must not be able to create visit without required fields of Visit Type, Contact Mode, Timing, Time Unit
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitWindowMin | -1 |
        And The 'save-visit-changes' button is clicked
        Then The field 'visit-timing' shows validation message 'This field is required'
        Then The field 'visit-type' shows validation message 'This field is required'
        Then The field 'contact-mode' shows validation message 'This field is required'
        Then The field 'time-unit' shows validation message 'This field is required'

    Scenario: [Timeline][Create Visit] Visit show in protocol must be enabled by default in the form
        And The page 'study_structure/visits' is opened for current study
        When The 'add-visit-empty-state' button is clicked
        And The 'toggle-visit-details' button is clicked
        Then The field 'show-visit-switch' is checked

    Scenario: [Timeline][Create Visit] SoA Milestone must be disabled by default in the form
        And The page 'study_structure/visits' is opened for current study
        When The 'add-visit-empty-state' button is clicked
        And The 'toggle-visit-details' button is clicked
        Then The field 'soa-milestone-switch' is not checked

    Scenario: [Timeline][Create Visit] User must be able to delete a visit
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitClass      | Global anchor visit |
            | visitType       | Screening           |
            | contactMode     | Phone Contact       |
            | timeUnit        | days                |
            | visitWindowUnit | days                |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved
        And The 'visit-box' button is clicked
        And The 'delete-visit-timeline' button is clicked
        And Action is confirmed by clicking continue
        Then The visit 'P1' is not visible in the Study Visits timeline view

    Scenario: [Timeline][Edit Visit] User must be able to edit a Manually defined visit
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitClass        | Manually defined visit |
            | visitType         | Screening              |
            | contactMode       | Phone Contact          |
            | timeReference     | Global anchor visit    |
            | timing            | 1                      |
            | timeUnit          | days                   |
            | visitName         | Fully Defined Visit    |
            | visitShortName    | V1                     |
            | uniqueVisitNumber | 1                      |
            | visitWindowUnit   | days                   |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved
        When The user edits visit 'V1' in the timeline view with following data:
            | epoch       | Intervention  |
            | visitType   | Surgery       |
            | contactMode | On Site Visit |
            | timing      | 2             |
            | timeUnit    | weeks         |
        And The user intercepts study visit 'edit' request
        And The 'edited' visit is saved
        Then The visit 'V1' is visible in the Study Visits timeline view:
            | epoch       | Intervention |
            | visitType   | Surgery      |
            | studyDay    | 14           |
            | studyWeek   | 2            |
            | visitWindow | ±0D          |

    Scenario: [Timeline][Edit Visit] User must be able to edit an epoch in a Global anchor visit
        And The page 'study_structure/visits' is opened for current study
        When The user defines a visit in the timeline view with following data:
            | visitClass      | Global anchor visit |
            | visitType       | Screening           |
            | contactMode     | Phone Contact       |
            | timeUnit        | days                |
            | visitWindowUnit | days                |
        And The user intercepts study visit 'create' request
        And The 'created' visit is saved
        When The user edits visit 'P1' in the timeline view with following data:
            | visitType      | Treatment     |
            | contactMode    | On Site Visit |
            | timeUnit       | weeks         |
            | visitWindowMax | 10            |
            | epoch          | Screening     |
        And The user intercepts study visit 'edit' request
        And The 'edited' visit is saved
        Then The visit 'V1' is visible in the Study Visits timeline view:
            | epoch       | Screening |
            | visitType   | Treatment |
            | studyDay    | 0         |
            | studyWeek   | 0         |
            | visitWindow | 0/+10D    |