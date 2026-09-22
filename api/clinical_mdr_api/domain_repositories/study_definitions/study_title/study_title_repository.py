from clinical_mdr_api.domain_repositories.models.study_field import StudyTextField


class StudyTitleRepository:
    @staticmethod
    def study_title_exists(study_title: str, study_number: str) -> bool:
        """
        Checks whether a specified study title already exists within the database.
        """
        study_title = StudyTextField.nodes.get_or_none(
            field_name="StudyTitle", value=study_title
        )
        return study_title is not None and study_title.is_used(
            study_number=study_number
        )

    @staticmethod
    def study_short_title_exists(study_short_title: str, study_number: str) -> bool:
        """
        Checks whether a specified study short title already exists within the database.
        """
        study_short_title = StudyTextField.nodes.get_or_none(
            field_name="StudyShortTitle", value=study_short_title
        )
        return study_short_title is not None and study_short_title.is_used(
            study_number=study_number
        )

    def close(self) -> None:
        """
        Closes the repository.
        """
