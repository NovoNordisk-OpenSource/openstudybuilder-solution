from datetime import date, datetime
from typing import Annotated, Any, Self

from pydantic import Field

from clinical_mdr_api.domains.controlled_terminologies.ct_package import CTPackageAR
from clinical_mdr_api.models.utils import BaseModel
from clinical_mdr_api.utils import snake_case_data
from common.utils import convert_to_datetime


class CTPackage(BaseModel):
    @classmethod
    def from_ct_package_ar(cls, ct_package_ar: CTPackageAR) -> Self:
        return cls(
            uid=ct_package_ar.uid,
            catalogue_name=ct_package_ar.catalogue_name,
            name=ct_package_ar.name,
            label=ct_package_ar.label,
            description=ct_package_ar.description,
            href=ct_package_ar.href,
            registration_status=ct_package_ar.registration_status,
            source=ct_package_ar.source,
            extends_package=ct_package_ar.extends_package,
            import_date=ct_package_ar.import_date,
            effective_date=ct_package_ar.effective_date,
            author_username=ct_package_ar.author_username,
        )

    uid: Annotated[str, Field()]

    catalogue_name: Annotated[str, Field()]
    name: Annotated[str, Field()]
    label: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})]
    href: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    registration_status: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ]
    source: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    extends_package: Annotated[
        str | None,
        Field(
            description="CDISC CT Package extended by this sponsor package",
            json_schema_extra={"nullable": True},
        ),
    ]
    import_date: Annotated[datetime, Field()]
    effective_date: Annotated[date, Field()]
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None


class CodelistChangeItem(BaseModel):
    uid: Annotated[str, Field()]
    value_node: Annotated[dict, Field()]
    change_date: Annotated[datetime, Field()]
    is_change_of_codelist: Annotated[bool, Field()]

    @classmethod
    def from_repository_output(cls, query_output) -> Self:
        return cls(
            uid=query_output["uid"],
            value_node=snake_case_data(query_output["value_node"]),
            change_date=convert_to_datetime(value=query_output["change_date"]),
            is_change_of_codelist=query_output.get("is_change_of_codelist", True),
        )


class TermChangeItem(BaseModel):
    uid: Annotated[str, Field()]
    value_node: Annotated[dict, Field()]
    change_date: Annotated[datetime, Field()]
    codelists: Annotated[list[Any], Field()]

    @classmethod
    def from_repository_output(cls, query_output) -> Self:
        return cls(
            uid=query_output["uid"],
            value_node=snake_case_data(query_output["value_node"]),
            change_date=convert_to_datetime(value=query_output["change_date"]),
            codelists=query_output["codelists"],
        )


class CTPackageChanges(BaseModel):
    from_package: Annotated[str, Field()]
    to_package: Annotated[str, Field()]
    new_codelists: Annotated[list[CodelistChangeItem], Field()]
    deleted_codelists: Annotated[list[CodelistChangeItem], Field()]
    updated_codelists: Annotated[list[CodelistChangeItem], Field()]

    new_terms: Annotated[list[TermChangeItem], Field()]
    deleted_terms: Annotated[list[TermChangeItem], Field()]
    updated_terms: Annotated[list[TermChangeItem], Field()]

    @classmethod
    def from_repository_output(
        cls, old_package_name: str, new_package_name: str, query_output
    ) -> Self:
        return cls(
            from_package=old_package_name,
            to_package=new_package_name,
            new_codelists=[
                CodelistChangeItem.from_repository_output(item)
                for item in query_output["new_codelists"]
            ],
            updated_codelists=[
                CodelistChangeItem.from_repository_output(item)
                for item in query_output["updated_codelists"]
            ],
            deleted_codelists=[
                CodelistChangeItem.from_repository_output(item)
                for item in query_output["deleted_codelists"]
            ],
            new_terms=[
                TermChangeItem.from_repository_output(item)
                for item in query_output["new_terms"]
            ],
            updated_terms=[
                TermChangeItem.from_repository_output(item)
                for item in query_output["updated_terms"]
            ],
            deleted_terms=[
                TermChangeItem.from_repository_output(item)
                for item in query_output["deleted_terms"]
            ],
        )


class CTPackageChangesSpecificCodelist(CTPackageChanges):
    not_modified_terms: Annotated[list[TermChangeItem], Field()]

    @classmethod
    def from_repository_output(
        cls, old_package_name: str, new_package_name: str, query_output
    ) -> Self:
        return cls(
            from_package=old_package_name,
            to_package=new_package_name,
            new_codelists=[
                CodelistChangeItem.from_repository_output(item)
                for item in query_output["new_codelists"]
            ],
            updated_codelists=[
                CodelistChangeItem.from_repository_output(item)
                for item in query_output["updated_codelists"]
            ],
            deleted_codelists=[
                CodelistChangeItem.from_repository_output(item)
                for item in query_output["deleted_codelists"]
            ],
            new_terms=[
                TermChangeItem.from_repository_output(item)
                for item in query_output["new_terms"]
            ],
            updated_terms=[
                TermChangeItem.from_repository_output(item)
                for item in query_output["updated_terms"]
            ],
            deleted_terms=[
                TermChangeItem.from_repository_output(item)
                for item in query_output["deleted_terms"]
            ],
            not_modified_terms=[
                TermChangeItem.from_repository_output(item)
                for item in query_output["not_modified_terms"]
            ],
        )


class CTPackageDates(BaseModel):
    @classmethod
    def from_repository_output(
        cls, catalogue_name: str, effective_dates: list[date]
    ) -> Self:
        return cls(catalogue_name=catalogue_name, effective_dates=effective_dates)

    catalogue_name: Annotated[str, Field()]
    effective_dates: Annotated[list[date], Field()]
