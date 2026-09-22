from clinical_mdr_api.models.controlled_terminologies.ct_codelist import (
    CTCodelistNameAndAttributes,
)
from clinical_mdr_api.models.controlled_terminologies.ct_stats import (
    CountByType,
    CountByTypeByYear,
    CountTypeEnum,
    CTStats,
)
from clinical_mdr_api.repositories.ct_packages import get_package_changes_by_year
from clinical_mdr_api.services._meta_repository import MetaRepository
from common.auth.user import user


class CTStatsService:
    _repos: MetaRepository
    author_id: str

    def __init__(self):
        self.author_id = user().id()
        self._repos = MetaRepository(self.author_id)

    def _close_all_repos(self) -> None:
        self._repos.close()

    def get_stats(self, latest_codelists=list[CTCodelistNameAndAttributes]) -> CTStats:
        # Get change details
        yearly_aggregates = get_package_changes_by_year()

        codelist_change_details: list[CountByTypeByYear] = []
        term_change_details: list[CountByTypeByYear] = []
        for aggregate in yearly_aggregates:
            codelist_counts_by_type = [
                CountByType(
                    type=CountTypeEnum.ADDED, count=aggregate["added_codelists"]
                ),
                CountByType(
                    type=CountTypeEnum.DELETED, count=aggregate["deleted_codelists"]
                ),
                CountByType(
                    type=CountTypeEnum.UPDATED, count=aggregate["updated_codelists"]
                ),
            ]
            term_counts_by_type = [
                CountByType(type=CountTypeEnum.ADDED, count=aggregate["added_terms"]),
                CountByType(
                    type=CountTypeEnum.DELETED, count=aggregate["deleted_terms"]
                ),
                CountByType(
                    type=CountTypeEnum.UPDATED, count=aggregate["updated_terms"]
                ),
            ]
            codelist_change_details.append(
                CountByTypeByYear(
                    year=aggregate["year"], counts=codelist_counts_by_type
                )
            )
            term_change_details.append(
                CountByTypeByYear(year=aggregate["year"], counts=term_counts_by_type)
            )
        return CTStats(
            catalogues=self._repos.ct_catalogue_repository.count_all(),
            packages=self._repos.ct_package_repository.count_all(),
            codelist_counts=self._repos.ct_codelist_aggregated_repository.count_all(),
            term_counts=self._repos.ct_term_aggregated_repository.count_all(),
            codelist_change_percentage=self._repos.ct_codelist_aggregated_repository.get_change_percentage(),
            term_change_percentage=self._repos.ct_term_aggregated_repository.get_change_percentage(),
            codelist_change_details=codelist_change_details,
            term_change_details=term_change_details,
            latest_added_codelists=latest_codelists,
        )
