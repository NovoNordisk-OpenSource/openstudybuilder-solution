from threading import Lock

from cachetools import TTLCache, cached
from cachetools.keys import hashkey

from clinical_mdr_api.domain_repositories.generic_repository import (
    RepositoryClosureData,
)
from clinical_mdr_api.domain_repositories.models.brand import Brand
from clinical_mdr_api.domains.brands.brand import BrandAR
from clinical_mdr_api.repositories._utils import sb_clear_cache
from common.config import settings


class BrandRepository:
    cache_store_item_by_uid = TTLCache(
        maxsize=settings.cache_max_size, ttl=settings.cache_ttl
    )
    lock_store_item_by_uid = Lock()

    def generate_uid(self) -> str:
        return Brand.get_next_free_uid_and_increment_counter()

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
    def find_by_uid(self, uid: str) -> BrandAR | None:
        brand = Brand.nodes.get_or_none(uid=uid, is_deleted=False)
        if brand is not None:
            brand = BrandAR.from_input_values(
                name=brand.name,
                generate_uid_callback=lambda: brand.uid,
            )
            return brand
        return None

    def find_by_brand_name(self, name: str) -> BrandAR | None:
        brand = Brand.nodes.first_or_none(name=name, is_deleted=False)
        if brand is not None:
            brand = BrandAR.from_input_values(
                name=brand.name,
                generate_uid_callback=lambda: brand.uid,
            )
            return brand
        return None

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def save(self, brand: BrandAR) -> None:
        repository_closure_data = brand.repository_closure_data

        if repository_closure_data is None:
            # if save gets an object without a closure - it's a new object.
            # object should already have a UID.
            brand_node = Brand(
                uid=brand.uid,
                name=brand.name,
            )
            brand_node.save()
        else:
            # if save gets an object with a closure, it's a modified existing object.
            raise NotImplementedError

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass

    def find_all(self) -> list[BrandAR]:
        brands: list[Brand] = Brand.nodes.filter(is_deleted=False)
        brand_ars: list[BrandAR] = [
            BrandAR(
                _uid=p.uid,
                name=p.name,
            )
            for p in brands
        ]

        # attaching a proper repository closure data
        repository_closure_data = RepositoryClosureData(
            not_for_update=True, repository=self, additional_closure=None
        )
        for brand_ar in brand_ars:
            brand_ar.repository_closure_data = repository_closure_data

        return brand_ars

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def delete(self, uid: str):
        brand = Brand.nodes.first_or_none(uid=uid)
        if brand is not None:
            brand.is_deleted = True
            brand.save()
