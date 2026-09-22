import re
from collections import abc
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Iterable, Self

from clinical_mdr_api.domains.study_definition_aggregates._utils import (
    call_default_init,
    dataclass_with_default_init,
)
from clinical_mdr_api.domains.study_definition_aggregates.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.utils import normalize_string
from common import exceptions


class StudyStatus(Enum):
    DRAFT = "DRAFT"
    RELEASED = "RELEASED"
    LOCKED = "LOCKED"
    DELETED = "DELETED"


class StudyAction(Enum):
    """
    Enumerator for Study item actions that can change Study item status
    """

    LOCK = "lock"
    RELEASE = "release"
    UNLOCK = "unlock"
    DELETE = "delete"


class StudyCopyComponentEnum(str, Enum):
    STUDY_DESIGN = "high_level_study_design"
    STUDY_INTERVENTION = "study_intervention"
    STUDY_POPULATION = "study_population"


class StudyComponentEnum(str, Enum):
    IDENTIFICATION_METADATA = "identification_metadata"
    REGISTRY_IDENTIFIERS = "registry_identifiers"
    VERSION_METADATA = "version_metadata"
    STUDY_DESIGN = "high_level_study_design"
    STUDY_INTERVENTION = "study_intervention"
    STUDY_POPULATION = "study_population"
    STUDY_DESCRIPTION = "study_description"


class StudyCompactComponentEnum(str, Enum):
    IDENTIFICATION_METADATA = "identification_metadata"
    VERSION_METADATA = "version_metadata"
    STUDY_DESCRIPTION = "study_description"


_STUDY_NUMBER_PATTERN = re.compile(r"\d{1,4}")
_STUDY_SUBPART_ACRONYM_PATTERN = re.compile(r"[A-Z0-9]+")


FIX_SOME_VALUE_DEFAULT = """
############################################
##########_FIX_SOME_VALUE_DEFAULT_##########
############################################
"""


@dataclass_with_default_init(frozen=True)
class StudyIdentificationMetadataVO:
    project_number: str
    study_number: str | None
    subpart_id: str | None
    study_acronym: str | None
    study_subpart_acronym: str | None
    study_id_prefix: str | None
    description: str | None
    registry_identifiers: RegistryIdentifiersVO

    def __init__(
        self,
        project_number: str,
        study_number: str | None,
        subpart_id: str | None,
        study_acronym: str | None,
        description: str | None,
        registry_identifiers: RegistryIdentifiersVO | None,
        study_subpart_acronym: str | None = None,
        _study_id_prefix: str | None = None,
        # we denote this param with underscore, for "internal" use
        # (i.e.) use with caution and where You know what You are doing (setting an arbitrary value here)
    ):
        call_default_init(
            self,
            project_number=normalize_string(project_number),
            study_number=normalize_string(study_number),
            subpart_id=normalize_string(subpart_id),
            study_acronym=normalize_string(study_acronym),
            study_subpart_acronym=normalize_string(study_subpart_acronym),
            study_id_prefix=normalize_string(_study_id_prefix),
            description=normalize_string(description),
            registry_identifiers=registry_identifiers,
        )

    @classmethod
    def from_input_values(
        cls,
        project_number: str,
        study_number: str | None,
        subpart_id: str | None,
        study_acronym: str | None,
        description: str | None,
        registry_identifiers: RegistryIdentifiersVO | None,
        study_subpart_acronym: str | None = None,
    ) -> Self:
        return cls(
            study_number=study_number,
            subpart_id=subpart_id,
            study_acronym=study_acronym,
            study_subpart_acronym=study_subpart_acronym,
            project_number=project_number,
            description=description,
            registry_identifiers=registry_identifiers,
        )

    @property
    def study_id(self) -> str | None:
        if self.study_number is None or self.study_id_prefix is None:
            return None
        return f"{self.study_id_prefix}-{self.study_number}"

    def validate(
        self,
        project_exists_callback: Callable[[str], bool] = lambda _: True,
        study_number_exists_callback: Callable[[str, str | None], bool] = (
            lambda x, y: False
        ),
        study_acronym_exists_callback: Callable[[str, str | None], bool] = (
            lambda x, y: False
        ),
        null_value_exists_callback: Callable[[str], bool] = lambda _: True,
        is_subpart: bool = False,
        previous_is_subpart: bool = False,
        updatable_subpart: bool = False,
        previous_project_number: str | None = None,
        previous_study_acronym: str | None = None,
        uid: str | None = None,
    ) -> None:
        """
        Raises exceptions.ValidationException if values do not comply with relevant business rules.

        **Standalone study identification:** When ``is_subpart`` is false, at least one of
        ``study_number`` or ``study_acronym`` must be set. Rationale: a study that is not
        a subpart must be individually identifiable in the study catalogue, study pickers,
        and downstream artefacts; composite display ids derived from a parent no longer
        apply after detach. The same rule applies on subpart→standalone transitions
        (``previous_is_subpart`` true and ``is_subpart`` false).

        :param null_value_exists_callback:
        :param project_exists_callback: optional, if provided makes the method to include validity (existence)
            check on project_number value.
        :param study_number_exists_callback: checks whether given study_number already exist in the database

        """

        exceptions.BusinessLogicException.raise_if(
            previous_project_number
            and is_subpart
            and not updatable_subpart
            and self.project_number != previous_project_number,
            msg="Project of Study Subparts cannot be changed independently from its Study Parent Part.",
        )

        self.registry_identifiers.validate(
            null_value_exists_callback=null_value_exists_callback
        )

        # Standalone (non-subpart) studies must have study number and/or study
        # acronym — including subpart→standalone transitions.
        if previous_is_subpart and not is_subpart:
            exceptions.ValidationException.raise_if(
                self.study_number is None and self.study_acronym is None,
                msg=(
                    "Either study number or study acronym must be given when detaching a "
                    "Study Subpart to a standalone study. The study can no longer rely on "
                    "its parent's identifiers after detach."
                ),
            )
        else:
            exceptions.ValidationException.raise_if(
                not is_subpart
                and self.study_number is None
                and self.study_acronym is None,
                msg=(
                    "Either study number or study acronym must be given in study metadata. "
                    "A standalone study must have at least one of these identifiers so it "
                    "can be distinguished in the study catalogue and selections after it is "
                    "no longer linked as a subpart."
                ),
            )

        exceptions.ValidationException.raise_if(
            is_subpart and not self.study_subpart_acronym,
            msg="Study Subpart Acronym must be provided for Study Subpart.",
        )

        exceptions.ValidationException.raise_if(
            self.study_subpart_acronym is not None
            and len(self.study_subpart_acronym) > 10,
            msg=f"Study Subpart Acronym must not exceed 10 characters, got {len(self.study_subpart_acronym) if self.study_subpart_acronym else 0}.",
        )

        exceptions.ValidationException.raise_if(
            self.study_subpart_acronym is not None
            and not _STUDY_SUBPART_ACRONYM_PATTERN.fullmatch(
                self.study_subpart_acronym
            ),
            msg=f"Study Subpart Acronym must contain only alphanumeric characters (no blanks or special characters), got '{self.study_subpart_acronym}'.",
        )

        exceptions.ValidationException.raise_if(
            not is_subpart
            and self.study_number is not None
            and not _STUDY_NUMBER_PATTERN.fullmatch(self.study_number),
            msg=f"Provided study number can only be up to 4 digits string '{self.study_number}'.",
        )

        exceptions.BusinessLogicException.raise_if(
            self.project_number is not None
            and project_exists_callback is not None
            and not project_exists_callback(self.project_number),
            msg=f"Project with Project Number '{self.project_number}' doesn't exist.",
        )

        exceptions.AlreadyExistsException.raise_if(
            not is_subpart
            and self.study_number is not None
            and study_number_exists_callback(self.study_number, uid),
            "Study",
            self.study_number,
            "Study Number",
        )

        if (
            not is_subpart
            and self.study_acronym is not None
            and previous_study_acronym != self.study_acronym
            and study_acronym_exists_callback(self.study_acronym, uid)
        ):
            raise exceptions.AlreadyExistsException(
                "Study",
                self.study_acronym,
                "Study Acronym",
            )

    def is_valid(
        self,
        project_exists_callback: Callable[[str], bool] = lambda _: True,
        null_value_exists_callback: Callable[[str], bool] = lambda _: True,
    ) -> bool:
        """
        Convenience method (mostly for testing purposes).
        :return: False when self.validate raises exceptions.ValidationException (True otherwise)
        """
        try:
            self.validate(
                project_exists_callback=project_exists_callback,
                null_value_exists_callback=null_value_exists_callback,
            )
        except exceptions.ValidationException:
            return False
        return True

    def fix_some_values(
        self,
        *,
        project_number: str | None = FIX_SOME_VALUE_DEFAULT,
        study_number: str | None = FIX_SOME_VALUE_DEFAULT,
        subpart_id: str | None = FIX_SOME_VALUE_DEFAULT,
        study_acronym: str | None = FIX_SOME_VALUE_DEFAULT,
        study_subpart_acronym: str | None = FIX_SOME_VALUE_DEFAULT,
        study_id_prefix: str | None = FIX_SOME_VALUE_DEFAULT,
        description: str | None = FIX_SOME_VALUE_DEFAULT,
        registry_identifiers: RegistryIdentifiersVO | None = FIX_SOME_VALUE_DEFAULT,  # type: ignore[assignment]
    ) -> Self:
        """
        Helper function to produce a new object with some of values different from self.
        All parameters are optional. Those provided will have provided value in the new object (the rest if the object
        will be the same). It's particularly handy for testing.
        :return:
        """

        def helper(parameter: Any, def_value: Any):
            return def_value if parameter == FIX_SOME_VALUE_DEFAULT else parameter

        return StudyIdentificationMetadataVO(
            project_number=helper(project_number, self.project_number),
            study_number=helper(study_number, self.study_number),
            subpart_id=helper(subpart_id, self.subpart_id),
            study_acronym=helper(study_acronym, self.study_acronym),
            study_subpart_acronym=helper(
                study_subpart_acronym, self.study_subpart_acronym
            ),
            description=helper(description, self.description),
            registry_identifiers=helper(
                registry_identifiers, self.registry_identifiers
            ),
            _study_id_prefix=helper(study_id_prefix, self.study_id_prefix),
        )


@dataclass_with_default_init(frozen=True)
class StudyVersionMetadataVO:
    study_status: StudyStatus = StudyStatus.DRAFT
    # pylint: disable=invalid-field-call
    version_timestamp: datetime | None = field(default_factory=datetime.today)
    version_author: str | None = None
    version_description: str | None = None
    version_number: Decimal | None = None

    def __init__(
        self,
        study_status: StudyStatus = StudyStatus.DRAFT,
        version_timestamp: datetime | None = FIX_SOME_VALUE_DEFAULT,  # type: ignore[assignment]
        version_author: str | None = None,
        version_description: str | None = None,
        version_number: Decimal | None = None,
    ):
        if version_timestamp == FIX_SOME_VALUE_DEFAULT:
            version_timestamp = datetime.now(timezone.utc)
        assert version_timestamp is None or isinstance(version_timestamp, datetime)

        call_default_init(
            self,
            study_status=study_status,
            version_number=version_number,
            version_timestamp=version_timestamp,
            version_author=normalize_string(version_author),
            version_description=normalize_string(version_description),
        )

    def validate(self) -> None:
        """
        Raises exceptions.ValidationException if values do not comply with relevant business rules.
        Only business rules relevant to content of this object are evaluated.
        """

        exceptions.ValidationException.raise_if(
            self.study_status == StudyStatus.LOCKED and self.version_number is None,
            msg="LOCKED study must have locked version number.",
        )

        exceptions.ValidationException.raise_if(
            self.study_status != StudyStatus.LOCKED and self.version_number is not None,
            msg="Non-LOCKED study must not have locked version number.",
        )

        exceptions.ValidationException.raise_if(
            self.study_status != StudyStatus.LOCKED and self.version_number is not None,
            msg="Non-LOCKED study must not have locked version number.",
        )

        exceptions.ValidationException.raise_if(
            self.version_timestamp is None,
            msg="timestamp mandatory in VersionMetadataVO",
        )

        exceptions.ValidationException.raise_if(
            self.study_status == StudyStatus.LOCKED
            and (self.version_author is None or self.version_description is None),
            msg="version_info and version_author mandatory for LOCKED version",
        )

    def is_valid(self) -> bool:
        """
        Convenience method (mostly for testing purposes).
        :return: False when self.validate raises exceptions.ValidationException (True otherwise)
        """
        try:
            self.validate()
        except exceptions.ValidationException:
            return False
        return True


@dataclass(frozen=True)
class HighLevelStudyDesignVO:
    study_type_code: str | None = None
    study_type_null_value_code: str | None = None

    trial_type_codes: list[str] = field(default_factory=list)
    trial_type_null_value_code: str | None = None

    trial_phase_code: str | None = None
    trial_phase_null_value_code: str | None = None

    development_stage_code: str | None = None

    is_extension_trial: bool | None = None
    is_extension_trial_null_value_code: str | None = None

    is_adaptive_design: bool | None = None
    is_adaptive_design_null_value_code: str | None = None

    study_stop_rules: str | None = None
    study_stop_rules_null_value_code: str | None = None

    confirmed_response_minimum_duration: str | None = None
    confirmed_response_minimum_duration_null_value_code: str | None = None

    post_auth_indicator: bool | None = None
    post_auth_indicator_null_value_code: str | None = None

    def normalize_code_set(self, codes: Iterable[str]) -> list[str]:
        return list(
            dict.fromkeys(
                [_ for _ in [normalize_string(_) for _ in codes] if _ is not None]
            )
        )

    def validate(
        self,
        study_type_exists_callback: Callable[[str], bool] = lambda _: True,
        trial_intent_type_exists_callback: Callable[[str], bool] = lambda _: True,
        trial_type_exists_callback: Callable[[str], bool] = lambda _: True,
        trial_phase_exists_callback: Callable[[str], bool] = lambda _: True,
        development_stage_exists_callback: Callable[[str], bool] = (lambda _: True),
        null_value_exists_callback: Callable[[str], bool] = lambda _: True,
    ) -> None:
        """
        Validates content disregarding state of the study. Optionally (if relevant callback are provided as
        parameters) validates also values of codes referring to various coded values. Raises exceptions.ValidationException with proper
        message on first failure (order of checking is indeterminate, however starts with lightest tests).
        :param study_type_exists_callback: (optional) callback for checking study_type_codes
        :param trial_intent_type_exists_callback: (optional) callback for checking intent_type_codes
        :param trial_type_exists_callback: (optional) callback for checking trail_type_codes
        :param trial_phase_exists_callback: (optional) callback for checking trial_phase_codes
        :param development_stage_exists_callback: (optional) callback for checking development_stage_code
        :param null_value_exists_callback: (optional) callback for checking null_value_code for all specific values
        """

        # pylint: disable=unused-argument

        def validate_value_and_associated_null_value_valid(
            value: Any,
            associated_null_value_code: str | None,
            name_of_verified_value: str,
        ) -> None:
            exceptions.ValidationException.raise_if(
                associated_null_value_code is not None
                and not (
                    value is None
                    or (isinstance(value, abc.Collection) and len(value) == 0)
                ),
                msg=f"{name_of_verified_value} and associated null value code cannot be both provided.",
            )

            exceptions.ValidationException.raise_if(
                associated_null_value_code is not None
                and not null_value_exists_callback(associated_null_value_code),
                msg=f"Unknown null value code (reason for missing) provided for {name_of_verified_value}",
            )

        validate_value_and_associated_null_value_valid(
            self.study_type_code, self.study_type_null_value_code, "study_type_code"
        )

        validate_value_and_associated_null_value_valid(
            self.trial_type_codes, self.trial_type_null_value_code, "trial_type_codes"
        )

        validate_value_and_associated_null_value_valid(
            self.trial_phase_code, self.trial_phase_null_value_code, "trial_phase_code"
        )

        validate_value_and_associated_null_value_valid(
            self.is_extension_trial,
            self.is_extension_trial_null_value_code,
            "is_extension_trial",
        )

        validate_value_and_associated_null_value_valid(
            self.is_adaptive_design,
            self.is_adaptive_design_null_value_code,
            "is_adaptive_design",
        )

        validate_value_and_associated_null_value_valid(
            self.study_stop_rules,
            self.study_stop_rules_null_value_code,
            "study_stop_rules",
        )

        validate_value_and_associated_null_value_valid(
            self.confirmed_response_minimum_duration,
            self.confirmed_response_minimum_duration_null_value_code,
            "confirmed_response_minimum_duration",
        )

        validate_value_and_associated_null_value_valid(
            self.post_auth_indicator,
            self.post_auth_indicator_null_value_code,
            "confirmed_response_minimum_duration",
        )

        exceptions.ValidationException.raise_if(
            self.trial_phase_code is not None
            and not trial_phase_exists_callback(self.trial_phase_code),
            msg=f"Non-existent trial phase code provided '{self.trial_phase_code}'.",
        )

        exceptions.ValidationException.raise_if(
            self.study_type_code is not None
            and not study_type_exists_callback(self.study_type_code),
            msg=f"Non-existent study type code provided '{self.study_type_code}'.",
        )

        exceptions.ValidationException.raise_if(
            self.development_stage_code is not None
            and not development_stage_exists_callback(self.development_stage_code),
            msg=f"Non-existent development stage code provided '{self.development_stage_code}'.",
        )

        for trial_type_code in self.trial_type_codes:
            exceptions.ValidationException.raise_if_not(
                trial_type_exists_callback(trial_type_code),
                msg=f"Non-existent trial type code provided '{trial_type_code}'.",
            )

    def is_valid(
        self,
        study_type_exists_callback: Callable[[str], bool] = lambda _: True,
        trial_intent_type_exists_callback: Callable[[str], bool] = lambda _: True,
        trial_type_exists_callback: Callable[[str], bool] = lambda _: True,
        trial_phase_exists_callback: Callable[[str], bool] = lambda _: True,
        development_stage_exists_callback: Callable[[str], bool] = lambda _: True,
    ) -> bool:
        """
        Convenience method (mostly for testing purposes).
        :return: False when self.validate raises exceptions.ValidationException (True otherwise)
        """
        try:
            self.validate(
                study_type_exists_callback=study_type_exists_callback,
                trial_intent_type_exists_callback=trial_intent_type_exists_callback,
                trial_type_exists_callback=trial_type_exists_callback,
                trial_phase_exists_callback=trial_phase_exists_callback,
                development_stage_exists_callback=development_stage_exists_callback,
            )
        except exceptions.ValidationException:
            return False
        return True

    def fix_some_values(
        self,
        study_type_code: str | None = FIX_SOME_VALUE_DEFAULT,
        study_type_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        trial_type_codes: Iterable[str] = FIX_SOME_VALUE_DEFAULT,
        trial_type_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        trial_phase_code: str | None = FIX_SOME_VALUE_DEFAULT,
        trial_phase_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        development_stage_code: str | None = FIX_SOME_VALUE_DEFAULT,
        is_extension_trial: bool | None = FIX_SOME_VALUE_DEFAULT,  # type: ignore[assignment]
        is_extension_trial_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        is_adaptive_design: bool | None = FIX_SOME_VALUE_DEFAULT,  # type: ignore[assignment]
        is_adaptive_design_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        study_stop_rules: str | None = FIX_SOME_VALUE_DEFAULT,
        study_stop_rules_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        confirmed_response_minimum_duration: str | None = FIX_SOME_VALUE_DEFAULT,
        confirmed_response_minimum_duration_null_value_code: (
            str | None
        ) = FIX_SOME_VALUE_DEFAULT,
        post_auth_indicator: bool | None = FIX_SOME_VALUE_DEFAULT,  # type: ignore[assignment]
        post_auth_indicator_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
    ) -> Self:
        """
        Helper function to produce a new HighLevelStudyDesignVO object with some of values different from self.
        All parameters are optional. Those provided will have provided value in the new object (the rest if the object
        will be the same). It's particularly handy for testing.
        :param study_type_code:
        :param study_type_null_value_code:
        :param trial_type_codes:
        :param trial_type_null_value_code:
        :param trial_phase_code:
        :param trial_phase_null_value_code:
        :param development_stage_code:
        :param is_extension_trial:
        :param is_extension_trial_null_value_code:
        :param is_adaptive_design:
        :param is_adaptive_design_null_value_code:
        :param study_stop_rules:
        :param study_stop_rules_null_value_code:
        :param confirmed_response_minimum_duration:
        :param confirmed_response_minimum_duration_null_value_code:
        :param post_auth_indicator:
        :param post_auth_indicator_null_value_code:
        :return:
        """

        def helper(parameter: Any, def_value: Any):
            return def_value if parameter == FIX_SOME_VALUE_DEFAULT else parameter

        return HighLevelStudyDesignVO(
            study_type_code=helper(study_type_code, self.study_type_code),
            study_type_null_value_code=helper(
                study_type_null_value_code, self.study_type_null_value_code
            ),
            trial_type_codes=helper(trial_type_codes, self.trial_type_codes),
            trial_type_null_value_code=helper(
                trial_type_null_value_code, self.trial_type_null_value_code
            ),
            trial_phase_code=helper(trial_phase_code, self.trial_phase_code),
            trial_phase_null_value_code=helper(
                trial_phase_null_value_code, self.trial_phase_null_value_code
            ),
            development_stage_code=helper(
                development_stage_code, self.development_stage_code
            ),
            is_extension_trial=helper(is_extension_trial, self.is_extension_trial),
            is_extension_trial_null_value_code=helper(
                is_extension_trial_null_value_code,
                self.is_extension_trial_null_value_code,
            ),
            is_adaptive_design=helper(is_adaptive_design, self.is_adaptive_design),
            is_adaptive_design_null_value_code=helper(
                is_adaptive_design_null_value_code,
                self.is_adaptive_design_null_value_code,
            ),
            study_stop_rules=helper(study_stop_rules, self.study_stop_rules),
            study_stop_rules_null_value_code=helper(
                study_stop_rules_null_value_code, self.study_stop_rules_null_value_code
            ),
            confirmed_response_minimum_duration=helper(
                confirmed_response_minimum_duration,
                self.confirmed_response_minimum_duration,
            ),
            confirmed_response_minimum_duration_null_value_code=helper(
                confirmed_response_minimum_duration_null_value_code,
                self.confirmed_response_minimum_duration_null_value_code,
            ),
            post_auth_indicator=helper(post_auth_indicator, self.post_auth_indicator),
            post_auth_indicator_null_value_code=helper(
                post_auth_indicator_null_value_code,
                self.post_auth_indicator_null_value_code,
            ),
        )

    @classmethod
    def from_input_values(
        cls,
        *,
        study_type_code: str | None,
        study_type_null_value_code: str | None,
        trial_type_codes: list[str] | None,
        trial_type_null_value_code: str | None,
        trial_phase_code: str | None,
        trial_phase_null_value_code: str | None,
        development_stage_code: str | None,
        is_extension_trial: bool | None,
        is_extension_trial_null_value_code: str | None,
        is_adaptive_design: bool | None,
        is_adaptive_design_null_value_code: str | None,
        study_stop_rules: str | None,
        study_stop_rules_null_value_code: str | None,
        confirmed_response_minimum_duration: str | None,
        confirmed_response_minimum_duration_null_value_code: str | None,
        post_auth_indicator: bool | None,
        post_auth_indicator_null_value_code: str | None,
    ) -> Self:
        return HighLevelStudyDesignVO(
            study_type_code=study_type_code,
            study_type_null_value_code=study_type_null_value_code,
            trial_type_codes=trial_type_codes if trial_type_codes is not None else [],
            trial_type_null_value_code=trial_type_null_value_code,
            trial_phase_code=trial_phase_code,
            trial_phase_null_value_code=trial_phase_null_value_code,
            development_stage_code=development_stage_code,
            is_extension_trial=is_extension_trial,
            is_extension_trial_null_value_code=is_extension_trial_null_value_code,
            is_adaptive_design=is_adaptive_design,
            is_adaptive_design_null_value_code=is_adaptive_design_null_value_code,
            study_stop_rules=study_stop_rules,
            study_stop_rules_null_value_code=study_stop_rules_null_value_code,
            confirmed_response_minimum_duration=confirmed_response_minimum_duration,
            confirmed_response_minimum_duration_null_value_code=confirmed_response_minimum_duration_null_value_code,
            post_auth_indicator=post_auth_indicator,
            post_auth_indicator_null_value_code=post_auth_indicator_null_value_code,
        )


@dataclass(frozen=True)
class StudyPopulationVO:
    therapeutic_area_codes: list[str] = field(default_factory=list)
    therapeutic_area_null_value_code: str | None = None

    disease_condition_or_indication_codes: list[str] = field(default_factory=list)
    disease_condition_or_indication_null_value_code: str | None = None

    diagnosis_group_codes: list[str] = field(default_factory=list)
    diagnosis_group_null_value_code: str | None = None

    sex_of_participants_code: str | None = None
    sex_of_participants_null_value_code: str | None = None

    rare_disease_indicator: bool | None = None
    rare_disease_indicator_null_value_code: str | None = None

    healthy_subject_indicator: bool | None = None
    healthy_subject_indicator_null_value_code: str | None = None

    planned_minimum_age_of_subjects: str | None = None
    planned_minimum_age_of_subjects_null_value_code: str | None = None

    planned_maximum_age_of_subjects: str | None = None
    planned_maximum_age_of_subjects_null_value_code: str | None = None

    stable_disease_minimum_duration: str | None = None
    stable_disease_minimum_duration_null_value_code: str | None = None

    pediatric_study_indicator: bool | None = None
    pediatric_study_indicator_null_value_code: str | None = None

    pediatric_postmarket_study_indicator: bool | None = None
    pediatric_postmarket_study_indicator_null_value_code: str | None = None

    pediatric_investigation_plan_indicator: bool | None = None
    pediatric_investigation_plan_indicator_null_value_code: str | None = None

    relapse_criteria: str | None = None
    relapse_criteria_null_value_code: str | None = None

    number_of_expected_subjects: int | None = None
    number_of_expected_subjects_null_value_code: str | None = None

    @classmethod
    def from_input_values(
        cls,
        *,
        therapeutic_area_codes: Iterable[str],
        therapeutic_area_null_value_code: str | None,
        disease_condition_or_indication_codes: Iterable[str],
        disease_condition_or_indication_null_value_code: str | None,
        diagnosis_group_codes: Iterable[str],
        diagnosis_group_null_value_code: str | None,
        sex_of_participants_code: str | None,
        sex_of_participants_null_value_code: str | None,
        rare_disease_indicator: bool | None,
        rare_disease_indicator_null_value_code: str | None,
        healthy_subject_indicator: bool | None,
        healthy_subject_indicator_null_value_code: str | None,
        planned_minimum_age_of_subjects: str | None,
        planned_minimum_age_of_subjects_null_value_code: str | None,
        planned_maximum_age_of_subjects: str | None,
        planned_maximum_age_of_subjects_null_value_code: str | None,
        stable_disease_minimum_duration: str | None,
        stable_disease_minimum_duration_null_value_code: str | None,
        pediatric_study_indicator: bool | None,
        pediatric_study_indicator_null_value_code: str | None,
        pediatric_postmarket_study_indicator: bool | None,
        pediatric_postmarket_study_indicator_null_value_code: str | None,
        pediatric_investigation_plan_indicator: bool | None,
        pediatric_investigation_plan_indicator_null_value_code: str | None,
        relapse_criteria: str | None,
        relapse_criteria_null_value_code: str | None,
        number_of_expected_subjects: int | None,
        number_of_expected_subjects_null_value_code: str | None,
    ) -> Self:
        def normalize_code_set(codes: Iterable[str] | None) -> list[str]:
            if codes is None:
                codes = []
            return sorted(
                dict.fromkeys(
                    [_ for _ in [normalize_string(_) for _ in codes] if _ is not None]
                )
            )

        return StudyPopulationVO(
            therapeutic_area_codes=normalize_code_set(therapeutic_area_codes),
            therapeutic_area_null_value_code=normalize_string(
                therapeutic_area_null_value_code
            ),
            disease_condition_or_indication_codes=normalize_code_set(
                disease_condition_or_indication_codes
            ),
            disease_condition_or_indication_null_value_code=normalize_string(
                disease_condition_or_indication_null_value_code
            ),
            diagnosis_group_codes=normalize_code_set(diagnosis_group_codes),
            diagnosis_group_null_value_code=normalize_string(
                diagnosis_group_null_value_code
            ),
            sex_of_participants_code=normalize_string(sex_of_participants_code),
            sex_of_participants_null_value_code=normalize_string(
                sex_of_participants_null_value_code
            ),
            rare_disease_indicator=rare_disease_indicator,
            rare_disease_indicator_null_value_code=normalize_string(
                rare_disease_indicator_null_value_code
            ),
            healthy_subject_indicator=healthy_subject_indicator,
            healthy_subject_indicator_null_value_code=normalize_string(
                healthy_subject_indicator_null_value_code
            ),
            planned_maximum_age_of_subjects=planned_maximum_age_of_subjects,
            planned_maximum_age_of_subjects_null_value_code=normalize_string(
                planned_maximum_age_of_subjects_null_value_code
            ),
            planned_minimum_age_of_subjects=planned_minimum_age_of_subjects,
            planned_minimum_age_of_subjects_null_value_code=normalize_string(
                planned_minimum_age_of_subjects_null_value_code
            ),
            stable_disease_minimum_duration=stable_disease_minimum_duration,
            stable_disease_minimum_duration_null_value_code=normalize_string(
                stable_disease_minimum_duration_null_value_code
            ),
            pediatric_study_indicator=pediatric_study_indicator,
            pediatric_study_indicator_null_value_code=normalize_string(
                pediatric_study_indicator_null_value_code
            ),
            pediatric_postmarket_study_indicator=pediatric_postmarket_study_indicator,
            pediatric_postmarket_study_indicator_null_value_code=normalize_string(
                pediatric_postmarket_study_indicator_null_value_code
            ),
            pediatric_investigation_plan_indicator=pediatric_investigation_plan_indicator,
            pediatric_investigation_plan_indicator_null_value_code=normalize_string(
                pediatric_investigation_plan_indicator_null_value_code
            ),
            relapse_criteria=normalize_string(relapse_criteria),
            relapse_criteria_null_value_code=normalize_string(
                relapse_criteria_null_value_code
            ),
            number_of_expected_subjects=number_of_expected_subjects,
            number_of_expected_subjects_null_value_code=normalize_string(
                number_of_expected_subjects_null_value_code
            ),
        )

    def validate(
        self,
        *,
        null_value_exists_callback: Callable[[str], bool] = lambda _: True,
        therapeutic_area_exists_callback: Callable[[str], bool] = lambda _: True,
        disease_condition_or_indication_exists_callback: Callable[[str], bool] = (
            lambda _: True
        ),
        diagnosis_group_exists_callback: Callable[[str], bool] = lambda _: True,
        sex_of_participants_exists_callback: Callable[[str], bool] = lambda _: True,
    ) -> None:
        def validate_value_and_associated_null_value_valid(
            value: Any,
            associated_null_value_code: str | None,
            name_of_verified_value: str,
        ) -> None:
            exceptions.ValidationException.raise_if(
                associated_null_value_code is not None
                and not (
                    value is None
                    or (isinstance(value, abc.Collection) and len(value) == 0)
                ),
                msg=f"{name_of_verified_value} and associated null value code cannot be both provided.",
            )

            exceptions.ValidationException.raise_if(
                associated_null_value_code is not None
                and not null_value_exists_callback(associated_null_value_code),
                msg=f"Unknown null value code (reason for missing) provided for {name_of_verified_value}",
            )

        validate_value_and_associated_null_value_valid(
            value=self.therapeutic_area_codes,
            associated_null_value_code=self.therapeutic_area_null_value_code,
            name_of_verified_value="therapeutic_area_code",
        )

        validate_value_and_associated_null_value_valid(
            value=self.diagnosis_group_codes,
            associated_null_value_code=self.diagnosis_group_null_value_code,
            name_of_verified_value="diagnosis_group_code",
        )

        validate_value_and_associated_null_value_valid(
            value=self.disease_condition_or_indication_codes,
            associated_null_value_code=self.disease_condition_or_indication_null_value_code,
            name_of_verified_value="disease_condition_or_indication_code",
        )

        validate_value_and_associated_null_value_valid(
            value=self.sex_of_participants_code,
            associated_null_value_code=self.sex_of_participants_null_value_code,
            name_of_verified_value="sex_of_participants_code",
        )

        validate_value_and_associated_null_value_valid(
            value=self.healthy_subject_indicator,
            associated_null_value_code=self.healthy_subject_indicator_null_value_code,
            name_of_verified_value="healthy_subject_indicator",
        )

        validate_value_and_associated_null_value_valid(
            value=self.rare_disease_indicator,
            associated_null_value_code=self.rare_disease_indicator_null_value_code,
            name_of_verified_value="rare_disease_indicator",
        )

        validate_value_and_associated_null_value_valid(
            value=self.planned_minimum_age_of_subjects,
            associated_null_value_code=self.planned_minimum_age_of_subjects_null_value_code,
            name_of_verified_value="planned_minimum_age_of_subjects",
        )

        validate_value_and_associated_null_value_valid(
            value=self.planned_maximum_age_of_subjects,
            associated_null_value_code=self.planned_maximum_age_of_subjects_null_value_code,
            name_of_verified_value="planned_maximum_age_of_subjects",
        )

        validate_value_and_associated_null_value_valid(
            value=self.pediatric_study_indicator,
            associated_null_value_code=self.pediatric_study_indicator_null_value_code,
            name_of_verified_value="pediatric_study_indicator",
        )

        validate_value_and_associated_null_value_valid(
            value=self.pediatric_postmarket_study_indicator,
            associated_null_value_code=self.pediatric_postmarket_study_indicator_null_value_code,
            name_of_verified_value="pediatric_postmarket_study_indicator",
        )

        validate_value_and_associated_null_value_valid(
            value=self.pediatric_investigation_plan_indicator,
            associated_null_value_code=self.pediatric_investigation_plan_indicator_null_value_code,
            name_of_verified_value="pediatric_investigation_plan_indicator",
        )

        validate_value_and_associated_null_value_valid(
            value=self.relapse_criteria,
            associated_null_value_code=self.relapse_criteria_null_value_code,
            name_of_verified_value="relapse_criteria",
        )

        validate_value_and_associated_null_value_valid(
            value=self.number_of_expected_subjects,
            associated_null_value_code=self.number_of_expected_subjects_null_value_code,
            name_of_verified_value="number_of_expected_subjects",
        )

        for therapeutic_area_code in self.therapeutic_area_codes:
            exceptions.ValidationException.raise_if_not(
                therapeutic_area_exists_callback(therapeutic_area_code),
                msg=f"Unknown therapeutic area code '{therapeutic_area_code}'.",
            )

        for diagnosis_group_code in self.diagnosis_group_codes:
            exceptions.ValidationException.raise_if_not(
                diagnosis_group_exists_callback(diagnosis_group_code),
                msg=f"Unknown diagnosis group code '{diagnosis_group_code}'.",
            )

        for (
            disease_condition_or_indication_code
        ) in self.disease_condition_or_indication_codes:
            exceptions.ValidationException.raise_if_not(
                disease_condition_or_indication_exists_callback(
                    disease_condition_or_indication_code
                ),
                msg=f"Unknown disease_condition_or_indication_code '{disease_condition_or_indication_code}'.",
            )

        exceptions.ValidationException.raise_if(
            self.sex_of_participants_code is not None
            and not sex_of_participants_exists_callback(self.sex_of_participants_code),
            msg=f"Unknown sex of participants code '{self.sex_of_participants_code}'.",
        )

    def is_valid(
        self,
        *,
        null_value_exists_callback: Callable[[str], bool] = lambda _: True,
        therapeutic_area_exists_callback: Callable[[str], bool] = lambda _: True,
        disease_condition_or_indication_exists_callback: Callable[[str], bool] = (
            lambda _: True
        ),
        diagnosis_group_exists_callback: Callable[[str], bool] = lambda _: True,
        sex_of_participants_exists_callback: Callable[[str], bool] = lambda _: True,
    ) -> bool:
        try:
            self.validate(
                null_value_exists_callback=null_value_exists_callback,
                diagnosis_group_exists_callback=diagnosis_group_exists_callback,
                therapeutic_area_exists_callback=therapeutic_area_exists_callback,
                disease_condition_or_indication_exists_callback=disease_condition_or_indication_exists_callback,
                sex_of_participants_exists_callback=sex_of_participants_exists_callback,
            )
        except exceptions.ValidationException:
            return False
        return True

    def fix_some_values(
        self,
        *,
        therapeutic_area_codes: Iterable[str] = FIX_SOME_VALUE_DEFAULT,
        therapeutic_area_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        disease_condition_or_indication_codes: Iterable[str] = FIX_SOME_VALUE_DEFAULT,
        disease_condition_or_indication_null_value_code: (
            str | None
        ) = FIX_SOME_VALUE_DEFAULT,
        diagnosis_group_codes: Iterable[str] = FIX_SOME_VALUE_DEFAULT,
        diagnosis_group_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        sex_of_participants_code: str | None = FIX_SOME_VALUE_DEFAULT,
        sex_of_participants_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        rare_disease_indicator: bool | None = FIX_SOME_VALUE_DEFAULT,  # type: ignore[assignment]
        rare_disease_indicator_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        healthy_subject_indicator: bool | None = FIX_SOME_VALUE_DEFAULT,  # type: ignore[assignment]
        healthy_subject_indicator_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        planned_minimum_age_of_subjects: str | None = FIX_SOME_VALUE_DEFAULT,
        planned_minimum_age_of_subjects_null_value_code: (
            str | None
        ) = FIX_SOME_VALUE_DEFAULT,
        planned_maximum_age_of_subjects: str | None = FIX_SOME_VALUE_DEFAULT,
        planned_maximum_age_of_subjects_null_value_code: (
            str | None
        ) = FIX_SOME_VALUE_DEFAULT,
        stable_disease_minimum_duration: str | None = FIX_SOME_VALUE_DEFAULT,
        stable_disease_minimum_duration_null_value_code: (
            str | None
        ) = FIX_SOME_VALUE_DEFAULT,
        pediatric_study_indicator: bool | None = FIX_SOME_VALUE_DEFAULT,  # type: ignore[assignment]
        pediatric_study_indicator_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        pediatric_postmarket_study_indicator: bool | None = FIX_SOME_VALUE_DEFAULT,  # type: ignore[assignment]
        pediatric_postmarket_study_indicator_null_value_code: (
            str | None
        ) = FIX_SOME_VALUE_DEFAULT,
        pediatric_investigation_plan_indicator: bool | None = FIX_SOME_VALUE_DEFAULT,  # type: ignore[assignment]
        pediatric_investigation_plan_indicator_null_value_code: (
            str | None
        ) = FIX_SOME_VALUE_DEFAULT,
        relapse_criteria: str | None = FIX_SOME_VALUE_DEFAULT,
        relapse_criteria_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        number_of_expected_subjects: int | None = FIX_SOME_VALUE_DEFAULT,  # type: ignore[assignment]
        number_of_expected_subjects_null_value_code: (
            str | None
        ) = FIX_SOME_VALUE_DEFAULT,
    ) -> Self:
        def helper(parameter: Any, def_value: Any):
            if parameter == FIX_SOME_VALUE_DEFAULT:
                if isinstance(def_value, tuple):
                    return list(def_value)
                return def_value
            return parameter

        return StudyPopulationVO.from_input_values(
            therapeutic_area_codes=helper(
                therapeutic_area_codes, self.therapeutic_area_codes
            ),
            therapeutic_area_null_value_code=helper(
                therapeutic_area_null_value_code, self.therapeutic_area_null_value_code
            ),
            disease_condition_or_indication_codes=helper(
                disease_condition_or_indication_codes,
                self.disease_condition_or_indication_codes,
            ),
            disease_condition_or_indication_null_value_code=helper(
                disease_condition_or_indication_null_value_code,
                self.disease_condition_or_indication_null_value_code,
            ),
            diagnosis_group_codes=helper(
                diagnosis_group_codes, self.diagnosis_group_codes
            ),
            diagnosis_group_null_value_code=helper(
                diagnosis_group_null_value_code, self.diagnosis_group_null_value_code
            ),
            sex_of_participants_code=helper(
                sex_of_participants_code, self.sex_of_participants_code
            ),
            sex_of_participants_null_value_code=helper(
                sex_of_participants_null_value_code,
                self.sex_of_participants_null_value_code,
            ),
            healthy_subject_indicator=helper(
                healthy_subject_indicator, self.healthy_subject_indicator
            ),
            healthy_subject_indicator_null_value_code=helper(
                healthy_subject_indicator_null_value_code,
                self.healthy_subject_indicator_null_value_code,
            ),
            rare_disease_indicator=helper(
                rare_disease_indicator, self.rare_disease_indicator
            ),
            rare_disease_indicator_null_value_code=helper(
                rare_disease_indicator_null_value_code,
                self.rare_disease_indicator_null_value_code,
            ),
            planned_minimum_age_of_subjects=helper(
                planned_minimum_age_of_subjects, self.planned_minimum_age_of_subjects
            ),
            planned_minimum_age_of_subjects_null_value_code=helper(
                planned_minimum_age_of_subjects_null_value_code,
                self.planned_minimum_age_of_subjects_null_value_code,
            ),
            planned_maximum_age_of_subjects=helper(
                planned_maximum_age_of_subjects, self.planned_maximum_age_of_subjects
            ),
            planned_maximum_age_of_subjects_null_value_code=helper(
                planned_maximum_age_of_subjects_null_value_code,
                self.planned_maximum_age_of_subjects_null_value_code,
            ),
            stable_disease_minimum_duration=helper(
                stable_disease_minimum_duration, self.stable_disease_minimum_duration
            ),
            stable_disease_minimum_duration_null_value_code=helper(
                stable_disease_minimum_duration_null_value_code,
                self.stable_disease_minimum_duration_null_value_code,
            ),
            pediatric_study_indicator=helper(
                pediatric_study_indicator, self.pediatric_study_indicator
            ),
            pediatric_study_indicator_null_value_code=helper(
                pediatric_study_indicator_null_value_code,
                self.pediatric_study_indicator_null_value_code,
            ),
            pediatric_postmarket_study_indicator=helper(
                pediatric_postmarket_study_indicator,
                self.pediatric_postmarket_study_indicator,
            ),
            pediatric_postmarket_study_indicator_null_value_code=helper(
                pediatric_postmarket_study_indicator_null_value_code,
                self.pediatric_postmarket_study_indicator_null_value_code,
            ),
            pediatric_investigation_plan_indicator=helper(
                pediatric_investigation_plan_indicator,
                self.pediatric_investigation_plan_indicator,
            ),
            pediatric_investigation_plan_indicator_null_value_code=helper(
                pediatric_investigation_plan_indicator_null_value_code,
                self.pediatric_investigation_plan_indicator_null_value_code,
            ),
            relapse_criteria=helper(relapse_criteria, self.relapse_criteria),
            relapse_criteria_null_value_code=helper(
                relapse_criteria_null_value_code, self.relapse_criteria_null_value_code
            ),
            number_of_expected_subjects=helper(
                number_of_expected_subjects, self.number_of_expected_subjects
            ),
            number_of_expected_subjects_null_value_code=helper(
                number_of_expected_subjects_null_value_code,
                self.number_of_expected_subjects_null_value_code,
            ),
        )


@dataclass(frozen=True)
class StudyInterventionVO:
    intervention_type_code: str | None = None
    intervention_type_null_value_code: str | None = None

    add_on_to_existing_treatments: bool | None = None
    add_on_to_existing_treatments_null_value_code: str | None = None

    control_type_code: str | None = None
    control_type_null_value_code: str | None = None

    intervention_model_code: str | None = None
    intervention_model_null_value_code: str | None = None

    trial_intent_types_codes: list[str] = field(default_factory=list)
    trial_intent_type_null_value_code: str | None = None

    is_trial_randomised: bool | None = None
    is_trial_randomised_null_value_code: str | None = None

    stratification_factor: str | None = None
    stratification_factor_null_value_code: str | None = None

    trial_blinding_schema_code: str | None = None
    trial_blinding_schema_null_value_code: str | None = None

    planned_study_length: str | None = None
    planned_study_length_null_value_code: str | None = None

    @classmethod
    def from_input_values(
        cls,
        *,
        intervention_type_code: str | None,
        intervention_type_null_value_code: str | None,
        add_on_to_existing_treatments: bool | None,
        add_on_to_existing_treatments_null_value_code: str | None,
        control_type_code: str | None,
        control_type_null_value_code: str | None,
        intervention_model_code: str | None,
        intervention_model_null_value_code: str | None,
        is_trial_randomised: bool | None,
        is_trial_randomised_null_value_code: str | None,
        stratification_factor: str | None,
        stratification_factor_null_value_code: str | None,
        trial_blinding_schema_code: str | None,
        trial_blinding_schema_null_value_code: str | None,
        planned_study_length: str | None,
        planned_study_length_null_value_code: str | None,
        trial_intent_types_codes: list[str],
        trial_intent_type_null_value_code: str | None,
    ) -> Self:
        return StudyInterventionVO(
            intervention_type_code=normalize_string(intervention_type_code),
            intervention_type_null_value_code=normalize_string(
                intervention_type_null_value_code
            ),
            add_on_to_existing_treatments=add_on_to_existing_treatments,
            add_on_to_existing_treatments_null_value_code=normalize_string(
                add_on_to_existing_treatments_null_value_code
            ),
            control_type_code=normalize_string(control_type_code),
            control_type_null_value_code=normalize_string(control_type_null_value_code),
            intervention_model_code=intervention_model_code,
            intervention_model_null_value_code=normalize_string(
                intervention_model_null_value_code
            ),
            is_trial_randomised=is_trial_randomised,
            is_trial_randomised_null_value_code=normalize_string(
                is_trial_randomised_null_value_code
            ),
            stratification_factor=normalize_string(stratification_factor),
            stratification_factor_null_value_code=normalize_string(
                stratification_factor_null_value_code
            ),
            trial_blinding_schema_code=normalize_string(trial_blinding_schema_code),
            trial_blinding_schema_null_value_code=normalize_string(
                trial_blinding_schema_null_value_code
            ),
            planned_study_length=planned_study_length,
            planned_study_length_null_value_code=normalize_string(
                planned_study_length_null_value_code
            ),
            trial_intent_types_codes=(
                [] if trial_intent_types_codes is None else trial_intent_types_codes
            ),
            trial_intent_type_null_value_code=trial_intent_type_null_value_code,
        )

    def validate(
        self,
        *,
        null_value_exists_callback: Callable[[str], bool] = lambda _: True,
        intervention_type_exists_callback: Callable[[str], bool] = lambda _: True,
        control_type_exists_callback: Callable[[str], bool] = lambda _: True,
        intervention_model_exists_callback: Callable[[str], bool] = lambda _: True,
        trial_blinding_schema_exists_callback: Callable[[str], bool] = lambda _: True,
    ) -> None:
        def validate_value_and_associated_null_value_valid(
            value: Any,
            associated_null_value_code: str | None,
            name_of_verified_value: str,
        ) -> None:
            exceptions.ValidationException.raise_if(
                associated_null_value_code is not None
                and not (
                    value is None
                    or (isinstance(value, abc.Collection) and len(value) == 0)
                ),
                msg=f"{name_of_verified_value} and associated null value code cannot be both provided.",
            )

            exceptions.ValidationException.raise_if(
                associated_null_value_code is not None
                and not null_value_exists_callback(associated_null_value_code),
                msg=f"Unknown null value code (reason for missing) provided for {name_of_verified_value}",
            )

        validate_value_and_associated_null_value_valid(
            value=self.intervention_type_code,
            associated_null_value_code=self.intervention_type_null_value_code,
            name_of_verified_value="intervention_type",
        )

        validate_value_and_associated_null_value_valid(
            value=self.add_on_to_existing_treatments,
            associated_null_value_code=self.add_on_to_existing_treatments_null_value_code,
            name_of_verified_value="add_on_to_existing_treatments",
        )

        validate_value_and_associated_null_value_valid(
            value=self.control_type_code,
            associated_null_value_code=self.control_type_null_value_code,
            name_of_verified_value="control_type",
        )

        validate_value_and_associated_null_value_valid(
            self.trial_intent_types_codes,
            self.trial_intent_type_null_value_code,
            "trial_intent_types_codes",
        )

        validate_value_and_associated_null_value_valid(
            value=self.intervention_model_code,
            associated_null_value_code=self.intervention_model_null_value_code,
            name_of_verified_value="intervention_model",
        )

        validate_value_and_associated_null_value_valid(
            value=self.is_trial_randomised,
            associated_null_value_code=self.is_trial_randomised_null_value_code,
            name_of_verified_value="is_trial_randomised",
        )

        validate_value_and_associated_null_value_valid(
            value=self.stratification_factor,
            associated_null_value_code=self.stratification_factor_null_value_code,
            name_of_verified_value="stratification_factor",
        )

        validate_value_and_associated_null_value_valid(
            value=self.trial_blinding_schema_code,
            associated_null_value_code=self.trial_blinding_schema_null_value_code,
            name_of_verified_value="trial_blinding_schema",
        )

        validate_value_and_associated_null_value_valid(
            value=self.planned_study_length,
            associated_null_value_code=self.planned_study_length_null_value_code,
            name_of_verified_value="planned_study_length",
        )

        exceptions.ValidationException.raise_if(
            self.intervention_type_code is not None
            and not intervention_type_exists_callback(self.intervention_type_code),
            msg=f"Unknown intervention type code '{self.intervention_type_code}'.",
        )

        exceptions.ValidationException.raise_if(
            self.control_type_code is not None
            and not control_type_exists_callback(self.control_type_code),
            msg=f"Unknown control  type code '{self.control_type_code}'.",
        )

        exceptions.ValidationException.raise_if(
            self.intervention_model_code is not None
            and not intervention_model_exists_callback(self.intervention_model_code),
            msg=f"Unknown intervention model code '{self.intervention_model_code}'.",
        )

        exceptions.ValidationException.raise_if(
            self.trial_blinding_schema_code is not None
            and not trial_blinding_schema_exists_callback(
                self.trial_blinding_schema_code
            ),
            msg=f"Unknown trial blinding schema code '{self.trial_blinding_schema_code}'.",
        )

    def is_valid(
        self,
        *,
        null_value_exists_callback: Callable[[str], bool] = lambda _: True,
        intervention_type_exists_callback: Callable[[str], bool] = lambda _: True,
        control_type_exists_callback: Callable[[str], bool] = lambda _: True,
        intervention_model_exists_callback: Callable[[str], bool] = lambda _: True,
        trial_blinding_schema_exists_callback: Callable[[str], bool] = lambda _: True,
    ) -> bool:
        try:
            self.validate(
                null_value_exists_callback=null_value_exists_callback,
                intervention_type_exists_callback=intervention_type_exists_callback,
                control_type_exists_callback=control_type_exists_callback,
                intervention_model_exists_callback=intervention_model_exists_callback,
                trial_blinding_schema_exists_callback=trial_blinding_schema_exists_callback,
            )
        except exceptions.ValidationException:
            return False
        return True

    def fix_some_values(
        self,
        *,
        intervention_type_code: str | None = FIX_SOME_VALUE_DEFAULT,
        intervention_type_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        add_on_to_existing_treatments: bool | None = FIX_SOME_VALUE_DEFAULT,  # type: ignore[assignment]
        add_on_to_existing_treatments_null_value_code: (
            str | None
        ) = FIX_SOME_VALUE_DEFAULT,
        control_type_code: str | None = FIX_SOME_VALUE_DEFAULT,
        control_type_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        intervention_model_code: bool | None = FIX_SOME_VALUE_DEFAULT,  # type: ignore[assignment]
        intervention_model_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        is_trial_randomised: bool | None = FIX_SOME_VALUE_DEFAULT,  # type: ignore[assignment]
        is_trial_randomised_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        stratification_factor: str | None = FIX_SOME_VALUE_DEFAULT,
        stratification_factor_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        trial_blinding_schema_code: str | None = FIX_SOME_VALUE_DEFAULT,
        trial_blinding_schema_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        planned_study_length: str | None = FIX_SOME_VALUE_DEFAULT,
        planned_study_length_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
        trial_intent_types_codes: list[str] = FIX_SOME_VALUE_DEFAULT,  # type: ignore[assignment]
        trial_itent_type_null_value_code: str | None = FIX_SOME_VALUE_DEFAULT,
    ) -> Self:
        def helper(parameter: Any, def_value: Any):
            return def_value if parameter == FIX_SOME_VALUE_DEFAULT else parameter

        return StudyInterventionVO.from_input_values(
            intervention_type_code=helper(
                intervention_type_code, self.intervention_type_code
            ),
            intervention_type_null_value_code=helper(
                intervention_type_null_value_code,
                self.intervention_type_null_value_code,
            ),
            add_on_to_existing_treatments=helper(
                add_on_to_existing_treatments, self.add_on_to_existing_treatments
            ),
            add_on_to_existing_treatments_null_value_code=helper(
                add_on_to_existing_treatments_null_value_code,
                self.add_on_to_existing_treatments_null_value_code,
            ),
            control_type_code=helper(control_type_code, self.control_type_code),
            control_type_null_value_code=helper(
                control_type_null_value_code, self.control_type_null_value_code
            ),
            intervention_model_code=helper(
                intervention_model_code, self.intervention_model_code
            ),
            intervention_model_null_value_code=helper(
                intervention_model_null_value_code,
                self.intervention_model_null_value_code,
            ),
            is_trial_randomised=helper(is_trial_randomised, self.is_trial_randomised),
            is_trial_randomised_null_value_code=helper(
                is_trial_randomised_null_value_code,
                self.is_trial_randomised_null_value_code,
            ),
            stratification_factor=helper(
                stratification_factor, self.stratification_factor
            ),
            stratification_factor_null_value_code=helper(
                stratification_factor_null_value_code,
                self.stratification_factor_null_value_code,
            ),
            trial_blinding_schema_code=helper(
                trial_blinding_schema_code, self.trial_blinding_schema_code
            ),
            trial_blinding_schema_null_value_code=helper(
                trial_blinding_schema_null_value_code,
                self.trial_blinding_schema_null_value_code,
            ),
            planned_study_length=helper(
                planned_study_length, self.planned_study_length
            ),
            planned_study_length_null_value_code=helper(
                planned_study_length_null_value_code,
                self.planned_study_length_null_value_code,
            ),
            trial_intent_types_codes=helper(
                trial_intent_types_codes, self.trial_intent_types_codes
            ),
            trial_intent_type_null_value_code=helper(
                trial_itent_type_null_value_code, self.trial_intent_type_null_value_code
            ),
        )


@dataclass(frozen=True)
class StudyDescriptionVO:
    study_title: str | None = None
    study_short_title: str | None = None

    @classmethod
    def from_input_values(
        cls, study_title: str | None, study_short_title: str | None
    ) -> Self:
        return StudyDescriptionVO(
            study_title=normalize_string(study_title),
            study_short_title=normalize_string(study_short_title),
        )

    def validate(
        self,
        study_number: str | None,
        *,
        study_title_exists_callback: Callable[[str, str], bool] = (
            lambda _, study_number: True
        ),
        study_short_title_exists_callback: Callable[[str, str], bool] = (
            lambda _, study_number: True
        ),
    ) -> None:
        exceptions.AlreadyExistsException.raise_if(
            self.study_title is not None
            and study_number
            and study_title_exists_callback(self.study_title, study_number),
            msg=f"Study Title '{self.study_title}' already exists.",
        )
        exceptions.AlreadyExistsException.raise_if(
            self.study_short_title is not None
            and study_number
            and study_short_title_exists_callback(self.study_short_title, study_number),
            msg=f"Study Short Title '{self.study_short_title}' already exists.",
        )

    def is_valid(
        self,
        study_number: str,
        *,
        title_exists_callback: Callable[[str, str], bool] = (
            lambda _, study_number: True
        ),
        short_title_exists_callback: Callable[[str, str], bool] = (
            lambda _, study_number: True
        ),
    ) -> bool:
        try:
            self.validate(
                study_title_exists_callback=title_exists_callback,
                study_short_title_exists_callback=short_title_exists_callback,
                study_number=study_number,
            )
        except exceptions.ValidationException:
            return False
        return True

    def fix_some_values(
        self,
        *,
        study_title: str | None = FIX_SOME_VALUE_DEFAULT,
        study_short_title: str | None = FIX_SOME_VALUE_DEFAULT,
    ) -> Self:
        def helper(parameter: Any, def_value: Any):
            return def_value if parameter == FIX_SOME_VALUE_DEFAULT else parameter

        return StudyDescriptionVO.from_input_values(
            study_title=helper(study_title, self.study_title),
            study_short_title=helper(study_short_title, self.study_short_title),
        )


@dataclass(frozen=True)
class StudyFieldAuditTrailActionVO:
    """
    A single "Action" entry in an audit trail.
    An action is a tuple [Section, Field, Action, Before value, After value].
    """

    section: str
    field_name: str
    before_value: str | None
    after_value: str | None
    action: str

    @classmethod
    def from_input_values(
        cls,
        field_name: str,
        section: str,
        before_value: str | None,
        after_value: str | None,
        action: str,
    ) -> Self:
        return StudyFieldAuditTrailActionVO(
            field_name=normalize_string(field_name),
            section=normalize_string(section),
            before_value=normalize_string(before_value),
            after_value=normalize_string(after_value),
            action=normalize_string(action),
        )


@dataclass(frozen=True)
class StudyFieldAuditTrailEntryAR:
    """
    A dated entry in an audit trail.
    An entry has a specific study and specific user, and contain one or more actions.
    """

    study_uid: str
    author_id: str
    author_username: str
    date: str
    actions: list[StudyFieldAuditTrailActionVO]

    @classmethod
    def from_input_values(
        cls,
        study_uid: str,
        author_id: str,
        author_username: str,
        date: str,
        actions: list[StudyFieldAuditTrailActionVO],
    ) -> Self:
        return StudyFieldAuditTrailEntryAR(
            study_uid=normalize_string(study_uid),
            author_id=normalize_string(author_id),
            author_username=normalize_string(author_username),
            date=normalize_string(date),
            actions=actions,
        )


@dataclass(frozen=True)
class StudyMetadataVO:
    id_metadata: StudyIdentificationMetadataVO | None = None
    ver_metadata: StudyVersionMetadataVO | None = None
    high_level_study_design: HighLevelStudyDesignVO | None = None
    study_population: StudyPopulationVO | None = None
    study_intervention: StudyInterventionVO | None = None
    study_description: StudyDescriptionVO | None = None

    def get_field_value(self, grouping: str, field_name: str):
        """Resolve a field value by navigating the VO hierarchy."""
        if "." in grouping:
            obj = self
            for accessor in grouping.split("."):
                obj = getattr(obj, accessor)
        else:
            obj = getattr(self, grouping)
        return getattr(obj, field_name)

    def validate(
        self,
        *,
        project_exists_callback: Callable[[str], bool] = lambda _: True,
        study_number_exists_callback: Callable[[str, str | None], bool] = (
            lambda x, y: False
        ),
        study_acronym_exists_callback: Callable[[str, str | None], bool] = (
            lambda x, y: False
        ),
        study_type_exists_callback: Callable[[str], bool] = lambda _: True,
        trial_intent_type_exists_callback: Callable[[str], bool] = lambda _: True,
        trial_type_exists_callback: Callable[[str], bool] = lambda _: True,
        trial_phase_exists_callback: Callable[[str], bool] = lambda _: True,
        development_stage_exists_callback: Callable[[str], bool] = lambda _: True,
        null_value_exists_callback: Callable[[str], bool] = lambda _: True,
        therapeutic_area_exists_callback: Callable[[str], bool] = lambda _: True,
        disease_condition_or_indication_exists_callback: Callable[[str], bool] = (
            lambda _: True
        ),
        diagnosis_group_exists_callback: Callable[[str], bool] = lambda _: True,
        sex_of_participants_exists_callback: Callable[[str], bool] = lambda _: True,
        intervention_type_exists_callback: Callable[[str], bool] = lambda _: True,
        control_type_exists_callback: Callable[[str], bool] = lambda _: True,
        intervention_model_exists_callback: Callable[[str], bool] = lambda _: True,
        trial_blinding_schema_exists_callback: Callable[[str], bool] = lambda _: True,
        study_title_exists_callback: Callable[[str, str], bool] = (
            lambda _, study_number: False
        ),
        study_short_title_exists_callback: Callable[[str, str], bool] = (
            lambda _, study_number: False
        ),
        is_subpart: bool = False,
    ) -> None:
        """
        Raises exceptions.ValidationException if values do not comply with relevant business rules. As a parameters takes
        callback which are supposed to verify validity (existence) of relevant coded values. If not provided
        codes are assumed valid.
        """
        self.id_metadata.validate(
            project_exists_callback=project_exists_callback,
            study_number_exists_callback=study_number_exists_callback,
            study_acronym_exists_callback=study_acronym_exists_callback,
            is_subpart=is_subpart,
        )
        self.ver_metadata.validate()
        self.study_description.validate(
            study_title_exists_callback=study_title_exists_callback,
            study_short_title_exists_callback=study_short_title_exists_callback,
            study_number=self.id_metadata.study_number,
        )
        self.high_level_study_design.validate(
            study_type_exists_callback=study_type_exists_callback,
            trial_phase_exists_callback=trial_phase_exists_callback,
            development_stage_exists_callback=development_stage_exists_callback,
            trial_type_exists_callback=trial_type_exists_callback,
            trial_intent_type_exists_callback=trial_intent_type_exists_callback,
            null_value_exists_callback=null_value_exists_callback,
        )
        self.study_population.validate(
            therapeutic_area_exists_callback=therapeutic_area_exists_callback,
            disease_condition_or_indication_exists_callback=disease_condition_or_indication_exists_callback,
            diagnosis_group_exists_callback=diagnosis_group_exists_callback,
            sex_of_participants_exists_callback=sex_of_participants_exists_callback,
        )
        self.study_intervention.validate(
            intervention_type_exists_callback=intervention_type_exists_callback,
            control_type_exists_callback=control_type_exists_callback,
            intervention_model_exists_callback=intervention_model_exists_callback,
            trial_blinding_schema_exists_callback=trial_blinding_schema_exists_callback,
        )
