@REQ_ID:[New]
Feature: Maintaining Study Subparts for a Study Parent Part in OpenStudyBuilder API

    Background: Test user must be able to call the OpenStudyBuilder API and test data exist
        Given The test user can call the OpenStudyBuilder API
        Given a test Study identified by 'uid' is in status 'Draft'

    Rule: As an API user,
        I want the system to support Definition of Study Subparts for a Study Parent Part,
        So that I can support Studies holding multiple parts with individual Study Definitions and Study Designs.


        ### Create sub parts
        @TestID:test_create_study_subpart
        Scenario: Creating a Study as a Study Subpart is allowed
            When a Study is created as a Study Subpart using the POST API endpoint '/studies'
            Then the API must ensure the Study will be added as a Study Subpart
            And the Study Subpart is assigned a consecutive Study Subpart ID unique within the set of Study Subparts for the Study Parent Part


        @TestID:test_use_an_already_existing_study_as_a_study_subpart
        Scenario: Using an already existing Study as a Study Subpart is allowed
            When an existing Study is used as a Study Subpart using the PATCH API endpoint '/studies/<uid>'
            Then the API must ensure the Study will be added as a Study Subpart
            And the Study Subpart is assigned a consecutive Study Subpart ID unique within the set of Study Subparts for the Study Parent Part


        @TestID:test_cannot_use_a_study_parent_part_as_study_subpart
        Scenario: Using a Study Parent Part as a Study Subpart is not allowed
            When a Study Parent Part is used as a Study Subpart using the POST API endpoint '/studies/<uid>'
            Then the API must return an error code as a Study Parent Part cannot be used as a Study Subpart


        @TestID:test_cannot_use_a_study_subpart_as_study_parent_part
        Scenario: Using a Study Subpart as a Study Parent Part is not allowed
            When a Study Subpart is added as a Study Parent Part using the POST API endpoint '/studies/<uid>'
            Then the API must return an error code as a Study Subpart cannot be used as a Study Parent Part


        @TestID:test_cannot_add_a_study_subpart_to_a_locked_study_parent_part
        Scenario: Adding a Study Subpart to a locked Study Parent Part is not allowed
            When a Study Subpart is added as to a Study Parent Part using the PATCH API endpoint '/studies/<uid>'
            Then the API must return an error code as a Study Subpart cannot be added to a locked Study Parent Part


        @TestID:test_cannot_make_a_study_a_subpart_of_itself
        Scenario: Using a Study as a Study Subpart to itself is not allowed
            When a Study is added as a Study Subpart to itself using the POST API endpoint '/studies/<uid>'
            Then the API must return an error code as a Study Subpart cannot be made with a self-reference


        Scenario: Study Title and Registry Identifiers for a Study Subpart must be aligned with the Study Parent Part
            When a Study Subpart is added to a Study Parent Part using the POST API endpoint '/studies'
            Then the study number, project relationship, title and Registry Identifiers for the Study Subpart must be aligned with the Study Parent Part


        ### Update subparts
        Scenario: Updates to Study Title or register identifiers for the Study Parent Part must also be applied for the Study Subparts
            When the Study Title or register identifiers are updated for a Study Parent Part using the PATCH API endpoint '/studies/<uid>'
            Then the updated study number, project relationship, title and register identifiers are also updated for the Study Subparts

        @TestID:test_cannot_change_study_title_of_subpart
        Scenario: Changing the Study Title of a Study Subpart is not allowed
            When the Study Title of a Study Subpart is updated using the PATCH API endpoint '/studies/<uid>'
            Then the API must return an error code as these updates cannot be made for Study Subparts


        @TestID:test_cannot_change_registry_identifiers_of_subpart
        Scenario: Changing the Registry Identifiers of a Study Subpart is not allowed
            When the Register Identifiers of a Study Subpart are updated using the PATCH API endpoint '/studies/<uid>'
            Then the API must return an error code as these updates cannot be made for Study Subparts


        @TestID:test_cannot_change_project_of_subpart
        Scenario: Changing the Project Number of a Study Subpart is not allowed
            When the Project Number of a Study Subpart is changed using the PATCH API endpoint '/studies/<uid>'
            Then the API must return an error code as this change cannot be made for Study Subparts


        @TestID:test_cannot_lock_study_subpart
        Scenario: Locking a Study Subpart indepedently from its Study Parent Part is not allowed
            When a Study Subpart is locked using the POST API endpoint '/studies/<uid>/locks'
            Then the API must return an error code as locking of a Study Subpart indepedently from its Study Parent Part is not allowed


        @TestID:test_cannot_unlock_study_subpart
        Scenario: Unlocking a Study Subpart indepedently from its Study Parent Part is not allowed
            When a Study Subpart is locked using the DELETE API endpoint '/studies/<uid>/locks'
            Then the API must return an error code as unlocking of a Study Subpart indepedently from its Study Parent Part is not allowed


        @TestID:test_cannot_release_study_subpart
        Scenario: Releasing a Study Subpart indepedently from its Study Parent Part is not allowed
            When a Study Subpart is locked using the DELETE API endpoint '/studies/<uid>/locks'
            Then the API must return an error code as releasing of a Study Subpart indepedently from its Study Parent Part is not allowed


        Scenario: Changing the acronym and descripton of a Study Subpart is allowed
            When a Study Subpart acronym or description is updated using the PATCH API endpoint '/studies/<uid>'
            Then the Study Subpart acronym or description is updated for the Study Subpart

        @TestID:test_reordering_study_subparts
        Scenario: Reordering a Study Subpart within its Study Parent Part is allowed
            When a Study Subpart is reordered using the PATCH API endpoint '/studies/<uid>'
            Then the Study Subpart will get a new derived Study Subpart ID
            And consecutive Study Subparts are assigned a consecutive new derived Study Subpart ID
            And all derived Study Subpart ID are unique within the set of subparts for the Study Parent Part


        Scenario: Changing the Study fields or selections except the Study Title and Registry Identifiers of a Study Subpart is allowed
            When Study fields or selections except the Study Title and Registry Identifiers are updated using the PATCH API endpoint 'studies/<uid>'
            Then the updated Study fields or selections are updated for the Study Subpart


        ### Remove sub parts
        @TestID:test_cannot_delete_study_parent_part
        Scenario: Deleting a Study Parent Part having Study Subparts is not allowed
            When a Study Parent Part having Study Subparts is deleted using the DELETE API endpoint '/studies/<uid>'
            Then the API must return an error code as deletion of Study Parent Part having Study Subparts is not allowed


        Scenario: Removing a Study Subpart from a Study Parent Part is allowed
            When a Study Subpart is removed from a Study Parent Part using the PATCH API endpoint '/studies/<uid>'
            Then the Study Subpart will be removed from the Study Parent Part
            And remaining Study Subparts are assigned a consecutive new derived Study Subpart ID
            And the value for derived Study Subpart ID, Subpart acronym and description is cleared

        Scenario: When the last Study Subpart is removed from a Study Parent Part then the Study Parent Part change to be a normal Study
            When the last Study Subpart is removed from a Study Parent Part using the PATCH API endpoint '/studies/<uid>'
            Then the Study Subpart will be removed from the Study Parent Part
            And the value for derived Study Subpart ID, Subpart acronym and description is cleared


    ### History of sub parts

    # To be made