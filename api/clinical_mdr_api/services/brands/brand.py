from neomodel import db  # type: ignore

from clinical_mdr_api.domains.brands.brand import BrandAR
from clinical_mdr_api.models.brands.brand import Brand, BrandCreateInput
from clinical_mdr_api.services._meta_repository import MetaRepository  # type: ignore
from common.auth.user import user
from common.exceptions import NotFoundException


class BrandService:
    def __init__(self):
        self.author_id = user().id()
        self.repos = MetaRepository()

    def get_all_brands(self) -> list[Brand]:
        try:
            all_brands = self.repos.brand_repository.find_all()
            self.repos.brand_repository.close()
            return [Brand.from_brand_ar(brand_ar) for brand_ar in all_brands]
        finally:
            self.repos.close()

    def get_brand(self, uid: str) -> Brand:
        repos = MetaRepository()
        try:
            brand = Brand.from_uid(uid, repos.brand_repository.find_by_uid)

            NotFoundException.raise_if(brand is None, "Brand", uid)

            return brand
        finally:
            self.repos.close()

    @db.transaction
    def create(self, brand_create_input: BrandCreateInput) -> Brand:
        try:
            brand_ar = BrandAR.from_input_values(
                name=brand_create_input.name,
                generate_uid_callback=self.repos.brand_repository.generate_uid,
            )

            # Try to retrieve brand with the same name, and return it if found
            existing_brand = self.repos.brand_repository.find_by_brand_name(
                brand_create_input.name
            )
            if existing_brand:
                return Brand.from_brand_ar(existing_brand)

            self.repos.brand_repository.save(brand_ar)
            return Brand.from_uid(brand_ar.uid, self.repos.brand_repository.find_by_uid)
        finally:
            self.repos.close()

    @db.transaction
    def delete(self, uid: str):
        self.repos.brand_repository.delete(uid)
