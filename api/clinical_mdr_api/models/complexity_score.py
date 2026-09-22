from typing import Annotated, Any, Self

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel, PostInputModel


class Burden(BaseModel):
    burden_id: Annotated[str, Field()]
    name: Annotated[str, Field()]
    description: Annotated[str, Field()]
    site_burden: Annotated[float, Field()]
    patient_burden: Annotated[float, Field()]
    median_cost_usd: Annotated[float | None, Field()] = None

    @classmethod
    def from_dict(cls, data: Any) -> Self:
        return cls(
            burden_id=data.get("burden_id"),
            site_burden=(
                float(data.get("site_burden"))
                if data.get("site_burden") is not None
                else 0.0
            ),
            name=data.get("name"),
            description=data.get("description"),
            patient_burden=(
                float(data.get("patient_burden"))
                if data.get("patient_burden") is not None
                else 0.0
            ),
            median_cost_usd=(
                float(data.get("median_cost_usd"))
                if data.get("median_cost_usd")
                else None
            ),
        )


class ComplexityScoreVisit(BaseModel):
    type: Annotated[str, Field()]
    count: Annotated[int, Field()]
    burden: Annotated[float, Field()]


class ComplexityScoreAssessment(BaseModel):
    type: Annotated[str, Field()]
    count: Annotated[int, Field()]
    burden: Annotated[float, Field()]


class ComplexityScoreDetails(BaseModel):
    visits: Annotated[list[ComplexityScoreVisit], Field()]
    assessments: Annotated[list[ComplexityScoreAssessment], Field()]


class BurdenInput(PostInputModel):
    burden_id: Annotated[str, Field(min_length=1)]
    name: Annotated[str, Field(min_length=1)]
    description: Annotated[str, Field(min_length=1)]
    site_burden: Annotated[float, Field()]
    patient_burden: Annotated[float, Field()]
    median_cost_usd: Annotated[float | None, Field()] = None


class BurdenIdInput(PostInputModel):
    burden_id: Annotated[str, Field(min_length=1)]


class ActivityBurden(BaseModel):
    activity_subgroup_uid: Annotated[str, Field()]
    activity_subgroup_name: Annotated[str | None, Field()] = None
    burden_id: Annotated[str | None, Field()] = None
    site_burden: Annotated[float, Field()] = 0.0
    patient_burden: Annotated[float, Field()] = 0.0
    median_cost_usd: Annotated[float | None, Field()] = None

    @classmethod
    def from_dict(cls, data: Any) -> Self:
        return cls(
            activity_subgroup_uid=data.get("activity_subgroup_uid"),
            activity_subgroup_name=data.get("activity_subgroup_name"),
            burden_id=data.get("burden_id"),
            site_burden=(
                float(data.get("site_burden"))
                if data.get("site_burden") is not None
                else 0.0
            ),
            patient_burden=(
                float(data.get("patient_burden"))
                if data.get("patient_burden") is not None
                else 0.0
            ),
            median_cost_usd=(
                float(data.get("median_cost_usd"))
                if data.get("median_cost_usd") is not None
                else 0.0
            ),
        )
