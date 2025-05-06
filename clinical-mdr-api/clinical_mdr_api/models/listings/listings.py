from typing import Annotated, Self

from pydantic import Field

from clinical_mdr_api.models.utils import BaseModel


class TopicCdDef(BaseModel):
    lb: Annotated[
        str | None, Field(title="Label", json_schema_extra={"nullable": True})
    ] = None
    topic_cd: Annotated[
        str | None, Field(title="Topic Code", json_schema_extra={"nullable": True})
    ] = None
    short_topic_cd: Annotated[
        str | None,
        Field(title="Short Topic Code", json_schema_extra={"nullable": True}),
    ] = None
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    molecular_weight: Annotated[
        float | None, Field(json_schema_extra={"nullable": True})
    ] = None
    sas_display_format: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    general_domain_class: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    sub_domain_class: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    sub_domain_type: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(
            lb=query_result["lb"],
            topic_cd=query_result["topic_cd"],
            short_topic_cd=query_result["short_topic_cd"],
            description=query_result["description"],
            molecular_weight=query_result["molecular_weight"],
            sas_display_format=query_result["sas_display_format"],
            general_domain_class=query_result["general_domain_class"],
            sub_domain_class=query_result["sub_domain_class"],
            sub_domain_type=query_result["sub_domain_type"],
        )


class MetaData(BaseModel):
    dataset_name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    dataset_label: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    name: Annotated[
        str | None,
        Field(title="name of variable", json_schema_extra={"nullable": True}),
    ] = None
    type: Annotated[
        str | None,
        Field(title="type of variable", json_schema_extra={"nullable": True}),
    ] = None
    length: Annotated[
        float | None,
        Field(title="length of variable", json_schema_extra={"nullable": True}),
    ] = None
    label: Annotated[
        str | None,
        Field(title="label of variable", json_schema_extra={"nullable": True}),
    ] = None
    format: Annotated[
        str | None,
        Field(title="SAS format of variable", json_schema_extra={"nullable": True}),
    ] = None
    informat: Annotated[
        str | None,
        Field(title="SAS informat of variable", json_schema_extra={"nullable": True}),
    ] = None

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(
            dataset_name=query_result["dataset_name"],
            dataset_label=query_result["dataset_label"],
            name=query_result["name"],
            type=query_result["type"],
            length=query_result["length"],
            label=query_result["label"],
            format=query_result["format"],
            informat=query_result["informat"],
        )


CT_SCOPE = "CT scope"
CT_VERSION = "CT version"
PACKAGE_NAME = "Package name"


class CDISCCTVer(BaseModel):
    ct_scope: Annotated[
        str | None, Field(title=CT_SCOPE, json_schema_extra={"nullable": True})
    ] = None
    ct_ver: Annotated[
        str | None, Field(title="CT version", json_schema_extra={"nullable": True})
    ] = None
    pkg_nm: Annotated[
        str | None, Field(title=PACKAGE_NAME, json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(
            ct_scope=query_result["ct_scope"],
            ct_ver=query_result["ct_ver"],
            pkg_nm=query_result["pkg_nm"],
        )


class CDISCCTPkg(BaseModel):
    pkg_scope: Annotated[
        str | None, Field(title="Package scope", json_schema_extra={"nullable": True})
    ] = None
    pkg_nm: Annotated[
        str | None, Field(title=PACKAGE_NAME, json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(pkg_scope=query_result["pkg_scope"], pkg_nm=query_result["pkg_nm"])


class CDISCCTList(BaseModel):
    ct_cd_list_cd: Annotated[
        str | None, Field(title="CT codelist", json_schema_extra={"nullable": True})
    ] = None

    ct_cd_list_extensible: Annotated[
        str | None,
        Field(
            title="CT codelist extensible",
            description="Is CT codelist extensible",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    ct_cd_list_nm: Annotated[
        str | None,
        Field(title="CT codelist name", json_schema_extra={"nullable": True}),
    ] = None
    ct_cd_list_submval: Annotated[
        str | None,
        Field(
            title="CT codelist submission value", json_schema_extra={"nullable": True}
        ),
    ] = None
    ct_scope: Annotated[
        str | None,
        Field(
            title=CT_SCOPE, description=CT_SCOPE, json_schema_extra={"nullable": True}
        ),
    ] = None
    ct_ver: Annotated[
        str | None,
        Field(
            title=CT_VERSION,
            description=CT_VERSION,
            json_schema_extra={"nullable": True},
        ),
    ] = None
    definition: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    nci_pref_term: Annotated[
        str | None,
        Field(title="NCI preferred term", json_schema_extra={"nullable": True}),
    ] = None
    pkg_nm: Annotated[
        str | None, Field(title=PACKAGE_NAME, json_schema_extra={"nullable": True})
    ] = None
    synonyms: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(
            ct_cd_list_cd=query_result["ct_cd_list_cd"],
            ct_cd_list_extensible=query_result["ct_cd_list_extensible"],
            ct_cd_list_nm=query_result["ct_cd_list_nm"],
            ct_cd_list_submval=query_result["ct_cd_list_submval"],
            ct_scope=query_result["ct_scope"],
            ct_ver=query_result["ct_ver"],
            definition=query_result["definition"],
            nci_pref_term=query_result["nci_pref_term"],
            pkg_nm=query_result["pkg_nm"],
            synonyms=query_result["synonyms"],
        )


class CDISCCTVal(BaseModel):
    ct_cd: Annotated[
        str | None, Field(title="CT Code", json_schema_extra={"nullable": True})
    ] = None
    ct_cd_list_submval: Annotated[
        str | None,
        Field(
            title="CT codelist submission value", json_schema_extra={"nullable": True}
        ),
    ] = None
    ct_scope: Annotated[
        str | None, Field(title=CT_SCOPE, json_schema_extra={"nullable": True})
    ] = None
    ct_submval: Annotated[
        str | None,
        Field(title="CT code submission value", json_schema_extra={"nullable": True}),
    ] = None
    ct_ver: Annotated[
        str | None, Field(title=CT_VERSION, json_schema_extra={"nullable": True})
    ] = None
    definition: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    nci_pref_term: Annotated[
        str | None,
        Field(title="NCI preferred term", json_schema_extra={"nullable": True}),
    ] = None
    pkg_nm: Annotated[
        str | None, Field(title=PACKAGE_NAME, json_schema_extra={"nullable": True})
    ] = None
    synonyms: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None

    @classmethod
    def from_query(cls, query_result: dict) -> Self:
        return cls(
            ct_cd=query_result["ct_cd"],
            ct_cd_list_submval=query_result["ct_cd_list_submval"],
            ct_scope=query_result["ct_scope"],
            ct_submval=query_result["ct_submval"],
            ct_ver=query_result["ct_ver"],
            definition=query_result["definition"],
            nci_pref_term=query_result["nci_pref_term"],
            pkg_nm=query_result["pkg_nm"],
            synonyms=query_result["synonyms"],
        )
