from enum import Enum


class LibraryItemStatus(Enum):
    """
    Enumerator for library item statuses
    """

    FINAL = "Final"
    DRAFT = "Draft"
    RETIRED = "Retired"


class ObjectAction(Enum):
    """
    Enumerator for library item actions that can change library item status
    """

    APPROVE = "approve"
    EDIT = "edit"
    DELETE = "delete"
    NEWVERSION = "new_version"
    INACTIVATE = "inactivate"
    REACTIVATE = "reactivate"


class StudyDesignClassEnum(Enum):
    MANUAL = "Manual"
    STUDY_WITH_COHORTS_BRANCHES_AND_SUBPOPULATIONS = (
        "Study with cohorts, branches and subpopulations"
    )


class StudySourceVariableEnum(Enum):
    COHORT = "Cohort"
    SUBGROUP = "Subgroup"
    STRATUM = "Stratum"


class OdmTranslatedTextTypeEnum(Enum):
    DESCRIPTION = "Description"
    QUESTION = "Question"
    OSB_DISPLAY_TEXT = "osb:DisplayText"
    OSB_DESIGN_NOTES = "osb:DesignNotes"
    OSB_COMPLETION_INSTRUCTIONS = "osb:CompletionInstructions"


class ValidationMode(Enum):
    """
    Enumerator for validation modes used in database integrity checks
    """

    STRICT = "strict"
    WARNING = "warning"
