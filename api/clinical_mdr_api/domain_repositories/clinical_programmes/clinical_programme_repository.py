from threading import Lock
from typing import Collection

from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from neomodel import db

from clinical_mdr_api.domain_repositories.generic_repository import (
    RepositoryClosureData,
)
from clinical_mdr_api.domain_repositories.models.clinical_programme import (
    ClinicalProgramme,
)
from clinical_mdr_api.domains.clinical_programmes.clinical_programme import (
    ClinicalProgrammeAR,
)
from clinical_mdr_api.repositories._utils import sb_clear_cache
from common.config import settings
from common.exceptions import BusinessLogicException, NotFoundException


class ClinicalProgrammeRepository:
    cache_store_item_by_uid = TTLCache(
        maxsize=settings.cache_max_size, ttl=settings.cache_ttl
    )
    lock_store_item_by_uid = Lock()

    def generate_uid(self) -> str:
        return ClinicalProgramme.get_next_free_uid_and_increment_counter()

    def clinical_programme_exists(self, clinical_programme_uid: str) -> bool:
        clinical_programme_node = ClinicalProgramme.nodes.get_or_none(
            uid=clinical_programme_uid
        )
        return bool(clinical_programme_node)

    def clinical_programme_name_exists(
        self, name: str, exclude_uid: str | None = None
    ) -> bool:
        result, _ = db.cypher_query(
            """
            MATCH (clinical_programme:ClinicalProgramme)
            WHERE toLower(clinical_programme.name) = toLower($name)
                AND ($exclude_uid IS NULL OR clinical_programme.uid <> $exclude_uid)
            RETURN COUNT(clinical_programme)
            """,
            params={"name": name, "exclude_uid": exclude_uid},
        )
        return bool(result[0][0])

    def get_hashkey(
        self,
        uid: str,
    ):
        """
        Returns a hash key that will be used for mapping objects stored in cache,
        which ultimately determines whether a method invocation is a hit or miss.
        """
        return hashkey(
            str(type(self)),
            uid,
        )

    @cached(cache=cache_store_item_by_uid, key=get_hashkey, lock=lock_store_item_by_uid)
    def find_by_uid(self, uid: str) -> ClinicalProgrammeAR:
        clinical_programme = ClinicalProgramme.nodes.get_or_none(uid=uid)

        NotFoundException.raise_if_not(clinical_programme, "Clinical Programme", uid)

        return ClinicalProgrammeAR.from_input_values(
            name=clinical_programme.name,
            generate_uid_callback=lambda: clinical_programme.uid,
        )

    def delete_by_uid(self, uid: str) -> None:
        clinical_programme: ClinicalProgramme = ClinicalProgramme.nodes.get_or_none(
            uid=uid
        )

        if clinical_programme:
            BusinessLogicException.raise_if(
                self.is_used_in_projects(uid),
                msg=f"Cannot delete Clinical Programme with UID '{uid}' because it is used by projects.",
            )

            clinical_programme.delete()

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def save(
        self, clinical_programme_ar: ClinicalProgrammeAR, update: bool = False
    ) -> None:
        """
        Create or update a Clinical Programme in the database.

        This method handles the creation of a new Clinical Programme or updating an existing one based on the `update` flag.

        Args:
            clinical_programme_ar
            update (bool): A flag indicating whether to update an existing Clinical Programme (if True) or create a new one (if False).
            Default is False.

        Raises:
            NotFoundException: If the Clinical Programme with the given UID does not exist.
            BusinessLogicException: If the Clinical Programme with the given UID is used in projects.
        """
        if not update:
            clinical_programme_ar = ClinicalProgramme(
                uid=clinical_programme_ar.uid, name=clinical_programme_ar.name
            )
            clinical_programme_ar.save()
        else:
            clinical_programme = ClinicalProgramme.nodes.get_or_none(
                uid=clinical_programme_ar.uid
            )

            NotFoundException.raise_if_not(
                clinical_programme, "Clinical Programme", clinical_programme_ar.uid
            )

            BusinessLogicException.raise_if(
                self.is_used_in_projects(clinical_programme_ar.uid),
                msg=f"Cannot update Clinical Programme with UID '{clinical_programme_ar.uid}' because it is used by projects.",
            )

            clinical_programme.name = clinical_programme_ar.name
            clinical_programme.save()

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass

    def find_all(self) -> Collection[ClinicalProgrammeAR]:
        clinical_programmes: list[ClinicalProgramme] = ClinicalProgramme.nodes.all()
        # projecting results to ClinicalProgrammeAR instances
        clinical_programme_ars: list[ClinicalProgrammeAR] = [
            ClinicalProgrammeAR.from_input_values(
                name=c.name, generate_uid_callback=lambda x=c: x.uid  # type: ignore[misc]
            )
            for c in clinical_programmes
        ]

        # attaching a proper repository closure data
        repository_closure_data = RepositoryClosureData(
            not_for_update=True, repository=self, additional_closure=None
        )
        for clinical_programme_ar in clinical_programme_ars:
            clinical_programme_ar.repository_closure_data = repository_closure_data

        return clinical_programme_ars

    def is_used_in_projects(self, uid: str) -> bool:
        rs = db.cypher_query(
            """
            MATCH (c:ClinicalProgramme {uid: $uid})-[:HOLDS_PROJECT]->(:Project)
            RETURN DISTINCT COUNT(c)
            """,
            params={"uid": uid},
        )

        return bool(rs[0][0][0])
