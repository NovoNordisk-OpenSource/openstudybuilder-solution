from typing import Annotated, Callable, Self

from pydantic import Field

from clinical_mdr_api.domains.brands.brand import BrandAR
from clinical_mdr_api.models.utils import BaseModel, PostInputModel


class Brand(BaseModel):
    uid: Annotated[str, Field(description="The unique id of the Brand.")]

    name: Annotated[str, Field()]

    @classmethod
    def from_uid(
        cls,
        uid: str,
        find_by_uid: Callable[[str], BrandAR | None],
    ) -> Self | None:
        brand = None
        brand_ar: BrandAR | None = find_by_uid(uid)
        if brand_ar is not None:
            brand = Brand.from_brand_ar(brand_ar)
        return brand

    @classmethod
    def from_brand_ar(
        cls,
        brand_ar: BrandAR,
    ) -> Self:
        return Brand(
            uid=brand_ar.uid,
            name=brand_ar.name,
        )


class BrandCreateInput(PostInputModel):
    name: Annotated[str, Field(min_length=1)]
