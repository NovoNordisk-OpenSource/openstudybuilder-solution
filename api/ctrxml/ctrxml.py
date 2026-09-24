# pylint: disable=too-many-lines

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from xsdata.models.datatype import XmlDate, XmlDateTime, XmlDuration, XmlTime


@dataclass
class AtcCodes:
    class Meta:
        name = "atc_codes"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"

    atc_code: List[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "max_length": 12,
            "doc": "D.3.3 IMP ATC Code",
        },
    )


class BooleanDomain(Enum):
    """Domain for identifying boolean values (0 = false, 1 = true, -1 = N/A)"""

    VALUE_0 = 0
    VALUE_1 = 1
    VALUE_1_1 = -1


@dataclass
class EutctDomain:
    class Meta:
        name = "eutct_domain"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"

    eutct_id: str = field(
        default="999999000000",
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "pattern": r"[1-9]{1}[0-9]{11}",
        },
    )
    eutct_version: int = field(
        default=1,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
        },
    )


class Locale(Enum):
    BG = "bg"
    CS = "cs"
    DA = "da"
    DE = "de"
    ET = "et"
    EL = "el"
    EN = "en"
    ES = "es"
    FR = "fr"
    GA = "ga"
    IT = "it"
    LV = "lv"
    LT = "lt"
    HU = "hu"
    MT = "mt"
    NL = "nl"
    PL = "pl"
    PT = "pt"
    RO = "ro"
    SK = "sk"
    SL = "sl"
    FI = "fi"
    SV = "sv"


Locale.BG.__doc__ = "Bulgaria"
Locale.CS.__doc__ = "Czech Republic"
Locale.DA.__doc__ = "Denmark"
Locale.DE.__doc__ = "Germany"
Locale.ET.__doc__ = "Estonia"
Locale.EL.__doc__ = "Greece"
Locale.EN.__doc__ = "Great Britain"
Locale.ES.__doc__ = "Spain"
Locale.FR.__doc__ = "France"
Locale.GA.__doc__ = "Ireland"
Locale.IT.__doc__ = "Italy"
Locale.LV.__doc__ = "Latvia"
Locale.LT.__doc__ = "Lithuania"
Locale.HU.__doc__ = "Hungary"
Locale.MT.__doc__ = "Malta"
Locale.NL.__doc__ = "Netherlands"
Locale.PL.__doc__ = "Poland"
Locale.PT.__doc__ = "Portugal"
Locale.RO.__doc__ = "Romania"
Locale.SK.__doc__ = "Slovakia"
Locale.SL.__doc__ = "Slovenia"
Locale.FI.__doc__ = "Finland"
Locale.SV.__doc__ = "Sweden"


class NationalCompetentAuthority(Enum):
    VALUE_23 = 23
    VALUE_24 = 24
    VALUE_121 = 121
    VALUE_44 = 44
    VALUE_39 = 39
    VALUE_25 = 25
    VALUE_81 = 81
    VALUE_40 = 40
    VALUE_26 = 26
    VALUE_27 = 27
    VALUE_22 = 22
    VALUE_21 = 21
    VALUE_28 = 28
    VALUE_49 = 49
    VALUE_45 = 45
    VALUE_29 = 29
    VALUE_30 = 30
    VALUE_41 = 41
    VALUE_82 = 82
    VALUE_42 = 42
    VALUE_31 = 31
    VALUE_47 = 47
    VALUE_32 = 32
    VALUE_33 = 33
    VALUE_38 = 38
    VALUE_48 = 48
    VALUE_34 = 34
    VALUE_122 = 122
    VALUE_43 = 43
    VALUE_46 = 46
    VALUE_35 = 35
    VALUE_36 = 36
    VALUE_37 = 37
    VALUE_50 = 50
    VALUE_61 = 61
    VALUE_123 = 123


NationalCompetentAuthority.VALUE_23.__doc__ = "Austria - BMGF"
NationalCompetentAuthority.VALUE_24.__doc__ = "Belgium - FPS Health-DGM"
NationalCompetentAuthority.VALUE_121.__doc__ = "Bulgarian Drug Agency"
NationalCompetentAuthority.VALUE_44.__doc__ = "Cyprus - MoH-Ph.S"
NationalCompetentAuthority.VALUE_39.__doc__ = "Czech Republic - SUKL"
NationalCompetentAuthority.VALUE_25.__doc__ = "Denmark - DKMA"
NationalCompetentAuthority.VALUE_81.__doc__ = "EMEA EudraCT Support"
NationalCompetentAuthority.VALUE_40.__doc__ = "Estonia - SAM"
NationalCompetentAuthority.VALUE_26.__doc__ = "Finland - NAM"
NationalCompetentAuthority.VALUE_27.__doc__ = "France - AFSSAPS"
NationalCompetentAuthority.VALUE_22.__doc__ = "Germany - BfArM"
NationalCompetentAuthority.VALUE_21.__doc__ = "Germany - PEI"
NationalCompetentAuthority.VALUE_28.__doc__ = "Greece - EOF"
NationalCompetentAuthority.VALUE_49.__doc__ = "Hungary - National Institute of Pharmacy"
NationalCompetentAuthority.VALUE_45.__doc__ = "Iceland - IMCA"
NationalCompetentAuthority.VALUE_29.__doc__ = "Ireland - IMB"
NationalCompetentAuthority.VALUE_30.__doc__ = "Italy - Ministry of Health"
NationalCompetentAuthority.VALUE_41.__doc__ = "Latvia - SAM"
NationalCompetentAuthority.VALUE_82.__doc__ = (
    "Liechtenstein - Kontrollstelle fur Arneimittel"
)
NationalCompetentAuthority.VALUE_42.__doc__ = "Lithuania - SMCA"
NationalCompetentAuthority.VALUE_31.__doc__ = "Luxembourg - Ministry of Health"
NationalCompetentAuthority.VALUE_47.__doc__ = "Malta - MRU"
NationalCompetentAuthority.VALUE_32.__doc__ = "Netherlands - CBG-MEB"
NationalCompetentAuthority.VALUE_33.__doc__ = "Netherlands - CCMO"
NationalCompetentAuthority.VALUE_38.__doc__ = "Norway - NOMA"
NationalCompetentAuthority.VALUE_48.__doc__ = "Poland - Office for Medicinal Products"
NationalCompetentAuthority.VALUE_34.__doc__ = "Portugal - INFARMED"
NationalCompetentAuthority.VALUE_122.__doc__ = "Romania - National Medicines Agency"
NationalCompetentAuthority.VALUE_43.__doc__ = "Slovakia - SIDC (Slovak)"
NationalCompetentAuthority.VALUE_46.__doc__ = "Slovenia - ARSZMP"
NationalCompetentAuthority.VALUE_35.__doc__ = "Spain - AEMPS"
NationalCompetentAuthority.VALUE_36.__doc__ = "Sweden - MPA"
NationalCompetentAuthority.VALUE_37.__doc__ = "UK - MHRA"
NationalCompetentAuthority.VALUE_50.__doc__ = "Netherlands - IGZ"
NationalCompetentAuthority.VALUE_61.__doc__ = "European Medicines Agency"
NationalCompetentAuthority.VALUE_123.__doc__ = "Bulgarian Drug Agency"


class BlindedRoleEnumeration(Enum):
    SUBJECT = "Subject"
    INVESTIGATOR = "Investigator"
    MONITOR = "Monitor"
    DATA_ANALYST = "Data analyst"
    CARE_PROVIDER = "Care provider"
    ASSESSOR = "Assessor"


class BlindingSchemaType(Enum):
    OPEN = "Open"
    SINGLE_BLIND = "Single blind"
    DOUBLE_BLIND = "Double blind"


class CtarmTypeEnumeration(Enum):
    EXPERIMENTAL = "Experimental"
    ACTIVE_COMPARATOR = "Active Comparator"
    PLACEBO_COMPARATOR = "Placebo Comparator"
    SHAM_COMPARATOR = "Sham Comparator"
    NO_INTERVENTION = "No intervention"
    OTHER = "Other"


class CtrrecruitmentType(Enum):
    PENDING = "Pending"
    RECRUITING = "Recruiting"
    SUSPENDED = "Suspended"
    COMPLETE = "Complete"
    OTHER = "Other"


@dataclass
class CtrsimpleTypeDefinitionRole:
    class Meta:
        name = "CTRsimpleTypeDefinition-Role"
        target_namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    context: Optional[str] = field(
        default=None,
        metadata={
            "name": "Context",
            "type": "Attribute",
        },
    )
    role_code_list_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "RoleCodeListOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class CentralTechnicalFacilityDuty:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    code_list_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "CodeListOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


@dataclass
class Contact:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    user_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "UserOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    contact_role: Optional[str] = field(
        default=None,
        metadata={
            "name": "ContactRole",
            "type": "Attribute",
            "required": True,
        },
    )
    contact_role_code_list_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ContactRoleCodeListOID",
            "type": "Attribute",
        },
    )


class InstitutionalReviewBoardEthicsCommitteeApprovalType(Enum):
    REQUEST_NOT_YET_SUBMITTED = "Request not yet submitted"
    SUBMITTED_PENDING = "Submitted, pending"
    SUBMITTED_APPROVED = "Submitted, approved"
    SUBMITTED_EXEMPT = "Submitted, exempt"
    SUBMITTED_DENIED = "Submitted, denied"
    SUBMISSION_NOT_REQUIRED = "Submission not required"


class InterventionTypeType(Enum):
    BEHAVIORAL_THERAPY = "Behavioral Therapy"
    BIOLOGIC = "Biologic"
    DEVICE = "Device"
    DIETARY_SUPPLEMENT = "Dietary Supplement"
    DRUG = "Drug"
    GENERIC = "Generic"
    OTHER = "Other"
    PROCEDURE = "Procedure"
    RADIATION = "Radiation"


@dataclass
class OrganizationRef:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    organization_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrganizationOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


class OutcomeType(Enum):
    PRIMARY = "Primary"
    SECONDARY = "Secondary"
    OTHER = "Other"


@dataclass
class RecruitmentCountry:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    country_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "CountryCode",
            "type": "Attribute",
            "required": True,
        },
    )
    code_list_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "CodeListOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


class RegistrationType(Enum):
    UNIVERSAL = "Universal"
    PRIMARY = "Primary"
    SECONDARY = "Secondary"
    OTHER = "Other"


class ResponsiblePartyTypeType(Enum):
    SPONSOR = "Sponsor"
    PRINCIPAL_INVESTIGATOR = "Principal Investigator"
    SPONSOR_INVESTIGATOR = "Sponsor-Investigator"


class SponsorTypeType(Enum):
    PRIMARY = "Primary"
    SECONDARY = "Secondary"


class StudyDateType(Enum):
    ANTICIPATED = "Anticipated"
    ACTUAL = "Actual"


class StudyRecruitmentStatusType(Enum):
    RECRUITING = "Recruiting"
    NOT_YET_RECRUITING = "Not yet recruiting"
    ENROLLING_BY_INVITATION = "Enrolling by invitation"
    ACTIVE_NOT_RECRUITING = "Active, not recruiting"
    COMPLETED = "Completed"
    TEMPORARILY_HALTED_SUSPENDED = "Temporarily halted / suspended"
    PREMATURELY_TERMINATED_TERMINATED = "Prematurely terminated / terminated"
    WITHDRAWN = "Withdrawn"


class StudyTypeType(Enum):
    INTERVENTIONAL = "Interventional"
    OBSERVATIONAL = "Observational"


@dataclass
class SubContractorDuty:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    code_list_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "CodeListOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


class YesNoType(Enum):
    YES = "Yes"
    NO = "No"


class CldataType(Enum):
    INTEGER = "integer"
    FLOAT = "float"
    TEXT = "text"
    STRING = "string"


class CommentType(Enum):
    SPONSOR = "Sponsor"
    SITE = "Site"


class Comparator(Enum):
    LT = "LT"
    LE = "LE"
    GT = "GT"
    GE = "GE"
    EQ = "EQ"
    NE = "NE"
    IN = "IN"
    NOTIN = "NOTIN"


class DataType(Enum):
    INTEGER = "integer"
    FLOAT = "float"
    DATE = "date"
    DATETIME = "datetime"
    TIME = "time"
    TEXT = "text"
    STRING = "string"
    DOUBLE = "double"
    URI = "URI"
    BOOLEAN = "boolean"
    HEX_BINARY = "hexBinary"
    BASE64_BINARY = "base64Binary"
    HEX_FLOAT = "hexFloat"
    BASE64_FLOAT = "base64Float"
    PARTIAL_DATE = "partialDate"
    PARTIAL_TIME = "partialTime"
    PARTIAL_DATETIME = "partialDatetime"
    DURATION_DATETIME = "durationDatetime"
    INTERVAL_DATETIME = "intervalDatetime"
    INCOMPLETE_DATETIME = "incompleteDatetime"
    INCOMPLETE_DATE = "incompleteDate"
    INCOMPLETE_TIME = "incompleteTime"


class EditPointType(Enum):
    MONITORING = "Monitoring"
    DATA_MANAGEMENT = "DataManagement"
    DBAUDIT = "DBAudit"


class EventType(Enum):
    SCHEDULED = "Scheduled"
    UNSCHEDULED = "Unscheduled"
    COMMON = "Common"


class FileType(Enum):
    SNAPSHOT = "Snapshot"
    TRANSACTIONAL = "Transactional"


class Granularity(Enum):
    ALL = "All"
    METADATA = "Metadata"
    ADMIN_DATA = "AdminData"
    REFERENCE_DATA = "ReferenceData"
    ALL_CLINICAL_DATA = "AllClinicalData"
    SINGLE_SITE = "SingleSite"
    SINGLE_SUBJECT = "SingleSubject"


class LocationType(Enum):
    SPONSOR = "Sponsor"
    SITE = "Site"
    CRO = "CRO"
    LAB = "Lab"
    OTHER = "Other"


class MethodType(Enum):
    COMPUTATION = "Computation"
    IMPUTATION = "Imputation"
    TRANSPOSE = "Transpose"
    OTHER = "Other"


class Odmversion(Enum):
    VALUE_1_2 = "1.2"
    VALUE_1_2_1 = "1.2.1"
    VALUE_1_3 = "1.3"
    VALUE_1_3_1 = "1.3.1"
    VALUE_1_3_2 = "1.3.2"


@dataclass
class OdmcomplexTypeDefinitionAddress:
    class Meta:
        name = "ODMcomplexTypeDefinition-Address"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    street_name: List[str] = field(
        default_factory=list,
        metadata={
            "name": "StreetName",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    city: Optional[str] = field(
        default=None,
        metadata={
            "name": "City",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    state_prov: Optional[str] = field(
        default=None,
        metadata={
            "name": "StateProv",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    country: Optional[str] = field(
        default=None,
        metadata={
            "name": "Country",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    postal_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "PostalCode",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    other_text: Optional[str] = field(
        default=None,
        metadata={
            "name": "OtherText",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionAlias:
    class Meta:
        name = "ODMcomplexTypeDefinition-Alias"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    context: Optional[str] = field(
        default=None,
        metadata={
            "name": "Context",
            "type": "Attribute",
            "required": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionArchiveLayout:
    class Meta:
        name = "ODMcomplexTypeDefinition-ArchiveLayout"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    pdf_file_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "PdfFileName",
            "type": "Attribute",
            "required": True,
        },
    )
    presentation_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "PresentationOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionArchiveLayoutRef:
    class Meta:
        name = "ODMcomplexTypeDefinition-ArchiveLayoutRef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    archive_layout_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ArchiveLayoutOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionCodeListRef:
    class Meta:
        name = "ODMcomplexTypeDefinition-CodeListRef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    code_list_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "CodeListOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionExternalCodeList:
    class Meta:
        name = "ODMcomplexTypeDefinition-ExternalCodeList"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    dictionary: Optional[str] = field(
        default=None,
        metadata={
            "name": "Dictionary",
            "type": "Attribute",
        },
    )
    version: Optional[str] = field(
        default=None,
        metadata={
            "name": "Version",
            "type": "Attribute",
        },
    )
    href: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    ref: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionExternalQuestion:
    class Meta:
        name = "ODMcomplexTypeDefinition-ExternalQuestion"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    dictionary: Optional[str] = field(
        default=None,
        metadata={
            "name": "Dictionary",
            "type": "Attribute",
        },
    )
    version: Optional[str] = field(
        default=None,
        metadata={
            "name": "Version",
            "type": "Attribute",
        },
    )
    code: Optional[str] = field(
        default=None,
        metadata={
            "name": "Code",
            "type": "Attribute",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionFlagType:
    class Meta:
        name = "ODMcomplexTypeDefinition-FlagType"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "required": True,
            "min_length": 1,
        },
    )
    code_list_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "CodeListOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionFlagValue:
    class Meta:
        name = "ODMcomplexTypeDefinition-FlagValue"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    code_list_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "CodeListOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionFormalExpression:
    class Meta:
        name = "ODMcomplexTypeDefinition-FormalExpression"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    context: Optional[str] = field(
        default=None,
        metadata={
            "name": "Context",
            "type": "Attribute",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionImputationMethod:
    class Meta:
        name = "ODMcomplexTypeDefinition-ImputationMethod"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionInclude:
    class Meta:
        name = "ODMcomplexTypeDefinition-Include"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    study_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "StudyOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    meta_data_version_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MetaDataVersionOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionInvestigatorRef:
    class Meta:
        name = "ODMcomplexTypeDefinition-InvestigatorRef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    user_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "UserOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionKeySet:
    class Meta:
        name = "ODMcomplexTypeDefinition-KeySet"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    study_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "StudyOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    subject_key: Optional[str] = field(
        default=None,
        metadata={
            "name": "SubjectKey",
            "type": "Attribute",
            "min_length": 1,
        },
    )
    study_event_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "StudyEventOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )
    study_event_repeat_key: Optional[str] = field(
        default=None,
        metadata={
            "name": "StudyEventRepeatKey",
            "type": "Attribute",
            "min_length": 1,
        },
    )
    form_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "FormOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )
    form_repeat_key: Optional[str] = field(
        default=None,
        metadata={
            "name": "FormRepeatKey",
            "type": "Attribute",
            "min_length": 1,
        },
    )
    item_group_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemGroupOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )
    item_group_repeat_key: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemGroupRepeatKey",
            "type": "Attribute",
            "min_length": 1,
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionLocationRef:
    class Meta:
        name = "ODMcomplexTypeDefinition-LocationRef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    location_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "LocationOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionMeasurementUnitRef:
    class Meta:
        name = "ODMcomplexTypeDefinition-MeasurementUnitRef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionMetaDataVersionRef:
    class Meta:
        name = "ODMcomplexTypeDefinition-MetaDataVersionRef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    study_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "StudyOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    meta_data_version_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MetaDataVersionOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    effective_date: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "EffectiveDate",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionPicture:
    class Meta:
        name = "ODMcomplexTypeDefinition-Picture"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    picture_file_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "PictureFileName",
            "type": "Attribute",
            "required": True,
        },
    )
    image_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "ImageType",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionPresentation:
    class Meta:
        name = "ODMcomplexTypeDefinition-Presentation"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    lang: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionSignatureRef:
    class Meta:
        name = "ODMcomplexTypeDefinition-SignatureRef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    signature_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionSiteRef:
    class Meta:
        name = "ODMcomplexTypeDefinition-SiteRef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    location_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "LocationOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionTranslatedText:
    class Meta:
        name = "ODMcomplexTypeDefinition-TranslatedText"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    lang: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "namespace": "http://www.w3.org/XML/1998/namespace",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionUserRef:
    class Meta:
        name = "ODMcomplexTypeDefinition-UserRef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    user_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "UserOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


class SignMethod(Enum):
    DIGITAL = "Digital"
    ELECTRONIC = "Electronic"


class SoftOrHard(Enum):
    SOFT = "Soft"
    HARD = "Hard"


class TransactionType(Enum):
    INSERT = "Insert"
    UPDATE = "Update"
    REMOVE = "Remove"
    UPSERT = "Upsert"
    CONTEXT = "Context"


class UserType(Enum):
    SPONSOR = "Sponsor"
    INVESTIGATOR = "Investigator"
    LAB = "Lab"
    OTHER = "Other"


class YesOnly(Enum):
    YES = "Yes"


class YesOrNo(Enum):
    YES = "Yes"
    NO = "No"


@dataclass
class SdmcomplexTypeDefinitionActivityRef:
    """An ActivityRef is used in multiple locations to link the containing
    definition to an activity.

    When used within an odm:StudyEventDef and the referenced activity
    contains FormRefs, those Forms must also be linke directly from
    within the StudyEventDef.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-ActivityRef"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    activity_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ActivityOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "OID of the referenced ActivityDef",
        },
    )
    order_number: Optional[int] = field(
        default=None,
        metadata={
            "name": "OrderNumber",
            "type": "Attribute",
            "doc": (
                "Optional ordering of activities within parent element "
                "(overrides document order)"
            ),
        },
    )


@dataclass
class SdmcomplexTypeDefinitionArmRef:
    """
    An ArmRef is used within ArmAssocation to link cell definitions to arms.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-ArmRef"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    arm_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ArmOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "OID of the references ArmDef",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionIncludeInclusionExclusionCriteria:
    """
    Include Inclusion/Exclusion criteria in entry or exit criteria of a
    structural element.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-IncludeInclusionExclusionCriteria"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class SdmcomplexTypeDefinitionSegmentRef:
    """
    A SegmentRef links cell definitions to segments.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-SegmentRef"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    segment_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "SegmentOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "OID of the referenced SegmentDef",
        },
    )
    order_number: Optional[int] = field(
        default=None,
        metadata={
            "name": "OrderNumber",
            "type": "Attribute",
            "doc": (
                "Optional ordering of segments within parent element "
                "(overrides document order)"
            ),
        },
    )


class Blindunblind(Enum):
    """
    Specifies arm association as blinded or unblinded.
    """

    BLINDED = "Blinded"
    UNBLINDED = "Unblinded"


class Structuralelementtype(Enum):
    ACTIVITY = "Activity"
    SEGMENT = "Segment"
    STUDY_EVENT = "StudyEvent"
    CELL = "Cell"
    EPOCH = "Epoch"
    STUDY = "Study"


class Subsequentschedulingbasistype(Enum):
    """
    Indicates to an execution engine how the subsequent activities' timing
    should be applied.
    """

    PLANNED = "Planned"
    ACTUAL = "Actual"


class Timepointgranularitytype(Enum):
    """Defines how a target time (or window endpoint) should be expanded.

    For example, "PD" means any time that day whereas "PTH" means
    anytime that hour.
    """

    PY = "PY"
    PM = "PM"
    PD = "PD"
    PTH = "PTH"
    PTM = "PTM"
    PTS = "PTS"


class Timingrelationshiptype(Enum):
    """
    For relative timing constraints, defines the types of relationships that
    may exist.
    """

    START_TO_START = "StartToStart"
    START_TO_FINISH = "StartToFinish"
    FINISH_TO_START = "FinishToStart"
    FINISH_TO_FINISH = "FinishToFinish"


@dataclass
class CanonicalizationMethodType:
    class Meta:
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    algorithm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Algorithm",
            "type": "Attribute",
            "required": True,
        },
    )
    content: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
        },
    )


@dataclass
class DsakeyValueType:
    class Meta:
        name = "DSAKeyValueType"
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    p: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "P",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "format": "base64",
        },
    )
    q: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "Q",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "format": "base64",
        },
    )
    g: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "G",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "format": "base64",
        },
    )
    y: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "Y",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "required": True,
            "format": "base64",
        },
    )
    j: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "J",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "format": "base64",
        },
    )
    seed: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "Seed",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "format": "base64",
        },
    )
    pgen_counter: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "PgenCounter",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "format": "base64",
        },
    )


@dataclass
class DigestMethodType:
    class Meta:
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    algorithm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Algorithm",
            "type": "Attribute",
            "required": True,
        },
    )
    content: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
        },
    )


@dataclass
class ObjectType:
    class Meta:
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Attribute",
        },
    )
    mime_type: Optional[str] = field(
        default=None,
        metadata={
            "name": "MimeType",
            "type": "Attribute",
        },
    )
    encoding: Optional[str] = field(
        default=None,
        metadata={
            "name": "Encoding",
            "type": "Attribute",
        },
    )
    content: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
        },
    )


@dataclass
class PgpdataType:
    class Meta:
        name = "PGPDataType"
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    pgpkey_id: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "PGPKeyID",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "format": "base64",
        },
    )
    pgpkey_packet: List[bytes] = field(
        default_factory=list,
        metadata={
            "name": "PGPKeyPacket",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "max_occurs": 2,
            "format": "base64",
        },
    )
    other_element: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
        },
    )


@dataclass
class RsakeyValueType:
    class Meta:
        name = "RSAKeyValueType"
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    modulus: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "Modulus",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "required": True,
            "format": "base64",
        },
    )
    exponent: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "Exponent",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "required": True,
            "format": "base64",
        },
    )


@dataclass
class SpkidataType:
    class Meta:
        name = "SPKIDataType"
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    spkisexp: List[bytes] = field(
        default_factory=list,
        metadata={
            "name": "SPKISexp",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "min_occurs": 1,
            "sequential": True,
            "format": "base64",
        },
    )
    other_element: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
            "sequential": True,
        },
    )


@dataclass
class SignatureMethodType:
    class Meta:
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    algorithm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Algorithm",
            "type": "Attribute",
            "required": True,
        },
    )
    content: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
            "choices": (
                {
                    "name": "HMACOutputLength",
                    "type": int,
                    "namespace": "http://www.w3.org/2000/09/xmldsig#",
                },
            ),
        },
    )


@dataclass
class SignaturePropertyType:
    class Meta:
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    target: Optional[str] = field(
        default=None,
        metadata={
            "name": "Target",
            "type": "Attribute",
            "required": True,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Attribute",
        },
    )
    content: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
        },
    )


@dataclass
class SignatureValueType:
    class Meta:
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    value: Optional[bytes] = field(
        default=None,
        metadata={
            "required": True,
            "format": "base64",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Attribute",
        },
    )


@dataclass
class TransformType:
    class Meta:
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    algorithm: Optional[str] = field(
        default=None,
        metadata={
            "name": "Algorithm",
            "type": "Attribute",
            "required": True,
        },
    )
    content: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
            "choices": (
                {
                    "name": "XPath",
                    "type": str,
                    "namespace": "http://www.w3.org/2000/09/xmldsig#",
                },
            ),
        },
    )


@dataclass
class X509IssuerSerialType:
    class Meta:
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    x509_issuer_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "X509IssuerName",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "required": True,
        },
    )
    x509_serial_number: Optional[int] = field(
        default=None,
        metadata={
            "name": "X509SerialNumber",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "required": True,
        },
    )


@dataclass
class ActiveSubstances:
    class Meta:
        name = "active_substances"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"

    active_substance: List["ActiveSubstances.ActiveSubstance"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "doc": (
                "This element holds information about individual active " "substances"
            ),
        },
    )

    @dataclass
    class ActiveSubstance:
        inn: Optional[str] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
                "max_length": 150,
                "nillable": True,
                "doc": "D.3.8 Active substance INN",
            },
        )
        cas_number: Optional[str] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
                "max_length": 12,
                "nillable": True,
                "doc": "D.3.9.1 Active substance CAS number",
            },
        )
        current_sponsor_code: Optional[str] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
                "required": True,
                "max_length": 100,
                "doc": "D.3.9.2 Active substance current sponsor code",
            },
        )
        other_descriptive_name: Optional[str] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
                "required": True,
                "max_length": 500,
                "doc": "D.3.9.3 Active substance other descriptive name",
            },
        )
        substance_code: Optional[str] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
                "max_length": 15,
                "nillable": True,
                "doc": "D.3.9.4 EV Substance Code",
            },
        )
        molecular_formula: Optional[str] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
                "required": True,
                "max_length": 500,
                "doc": "D.3.9.5 Active substance molecular formula",
            },
        )
        description: Optional[str] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
                "required": True,
                "max_length": 4000,
                "doc": "D.3.9.6 Active substance description",
            },
        )
        concentration_unit: Optional[EutctDomain] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
                "nillable": True,
                "doc": "D.3.10.1 Active substance concentration unit",
            },
        )
        concentration_type: Optional[EutctDomain] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
                "nillable": True,
                "doc": "D.3.10.2 Active substance concentration type",
            },
        )
        concentration_num_part1: Optional[str] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
                "max_length": 17,
                "nillable": True,
                "doc": "D.3.10.3 Active substance concentration number 1",
            },
        )
        concentration_num_part2: Optional[str] = field(
            default=None,
            metadata={
                "type": "Element",
                "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
                "max_length": 17,
                "nillable": True,
                "doc": "D.3.10.3 Active substance concentration number 2",
            },
        )


@dataclass
class CellOrigin:
    class Meta:
        name = "cell_origin"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"

    tissue_eng_origin_autologous: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.6.1.1\tTissue Engineered origin autologous",
        },
    )
    tissue_eng_origin_allogeneic: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.6.1.2\tTissue Engineered origin allogeneic",
        },
    )
    tissue_eng_origin_xenogeneic: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.6.1.3\tTissue Engineered origin xenogeneic",
        },
    )
    tissue_eng_xenogeneic_species: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 200,
            "doc": "D.6.1.3.1 Tissue Engineered xenogeneic species",
        },
    )


@dataclass
class CellType:
    class Meta:
        name = "cell_type"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"

    tissue_eng_type_stem: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.6.2.1\tTissue Engineered type stem",
        },
    )
    tissue_eng_type_differentiated: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.6.2.2\tTissue Engineered type differentiated",
        },
    )
    tissue_eng_diff_spec: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 200,
            "doc": "D.6.2.2.1 Tissue Engineered differentiated specification",
        },
    )
    tissue_eng_other: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.6.2.3\tTissue Engineered Other",
        },
    )
    tissue_eng_other_spec: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 200,
            "doc": "D.6.2.3.1 Tissue Engineered Other specification",
        },
    )


@dataclass
class CtaIdentification:
    class Meta:
        name = "cta_identification"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"

    eudract_no: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "pattern": r"20[0-9]{2}-[0-9]{6}-[0-9]{2}",
        },
    )
    nca: Optional[NationalCompetentAuthority] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
        },
    )


@dataclass
class GeneTherapy:
    class Meta:
        name = "gene_therapy"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"

    gene_ther_genes_of_interest: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 500,
            "doc": "D.5.1 Gene therapy gene(s) of interest",
        },
    )
    gene_ther_in_vivo: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.5.2 Gene therapy in-vivo",
        },
    )
    gene_ther_ex_vivo: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.5.3 Gene therapy ex-vivo",
        },
    )
    gene_ther_nucleic_acid: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.5.4.1\tGene therapy nucleic acid",
        },
    )
    gene_ther_nucleic_acid_naked: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.5.4.1.1 Gene therapy naked",
        },
    )
    gene_ther_nucleic_acid_complex: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.5.4.1.2 Gene therapy complexed",
        },
    )
    gene_ther_viral: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.5.4.2\tGene therapy viral vector",
        },
    )
    gene_ther_viral_specify: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 100,
            "doc": "D.5.4.2.1 Gene therapy viral vector type",
        },
    )
    gene_ther_others: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.5.4.3\tGene Therapy other",
        },
    )
    gene_ther_others_specify: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 200,
            "doc": "D.5.4.3.1 Gene therapy other specification",
        },
    )
    gene_ther_genetically_modified: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.5.5 GM cells",
        },
    )
    gene_ther_autologous: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.5.5.1\tGM cells origin autologous",
        },
    )
    gene_ther_allogeneic: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.5.5.2\tGM cells origin allogeneic",
        },
    )
    gene_ther_xenogeneic: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.5.5.3\tGM cells origin xenogeneic",
        },
    )
    gene_ther_xeno_species_origin: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 200,
            "doc": "D.5.5.3.1 GM cells xenogeneic species",
        },
    )
    gene_ther_type_cells_dtls: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 200,
            "doc": "D.5.5.4\tGM cells Other specification",
        },
    )


@dataclass
class ImpDevice:
    class Meta:
        name = "imp_device"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"

    device_description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 200,
            "doc": "D.7.1 Device description",
        },
    )
    device_name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 200,
            "doc": "D.7.2 Device name",
        },
    )
    device_implantable: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.7.3 Device implantable",
        },
    )
    is_medical_device: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.7.4.1\tContains medical device",
        },
    )
    has_device_ce_mark: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.7.4.1.1 Device has CE mark",
        },
    )
    device_notified_body: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 200,
            "doc": "D.7.4.1.1.1 Device notified body",
        },
    )
    has_biomedical_material: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.7.4.2\tContains Bio-materials",
        },
    )
    has_scaffolds: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.7.4.3\tContains Scaffolds",
        },
    )
    has_matrices: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.7.4.4\tContains Matrices",
        },
    )
    has_other_device: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.7.4.5\tDevice Other",
        },
    )
    other_device_spec: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 200,
            "doc": "D.7.4.5.1 Device Other specification",
        },
    )


@dataclass
class ImpIdentificationNotPossible:
    class Meta:
        name = "imp_identification_not_possible"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"

    has_any_auth_active_substance: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.2.2.1\tTreatment defined only by AS",
        },
    )
    has_local_site_products: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.2.2.2\tCombinations of marketed products",
        },
    )
    is_atc_group_used: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.2.2.3\tIMP defined by ATC Group",
        },
    )
    has_imp_other_identification: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.2.2.4\tIMP identification other",
        },
    )
    other_description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 500,
            "doc": "D.2.2.4.1 IMP identification other specification",
        },
    )


@dataclass
class ImpMemberState:
    class Meta:
        name = "imp_member_state"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"

    trade_name_in_ms: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 250,
            "doc": "D.2.1.1.1 IMP Trade name",
        },
    )
    ev_identifiable_product_code: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "max_length": 25,
            "nillable": True,
            "doc": "D.2.1.1.1.1 EV Identifiable Product Code",
        },
    )
    ma_holder: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 100,
            "doc": "D.2.1.1.2 MA holder",
        },
    )
    ma_number: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 100,
            "doc": "D.2.1.1.3 MA number",
        },
    )
    is_imp_modified: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.2.1.1.4 IMP modified",
        },
    )
    imp_modified_specification: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 500,
            "doc": "D.2.1.1.4.1 IMP modified specification",
        },
    )
    granted_ma_country: Optional[EutctDomain] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.2.1.2\tCountry granting MA",
        },
    )
    is_granting_ma_concerned_ms: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.2.1.2.1 Country granting MA is concerned MS",
        },
    )


@dataclass
class InternationalizedTextsType:
    class Meta:
        name = "internationalized_texts_type"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    locale: Optional[Locale] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class MemberStates:
    class Meta:
        name = "member_states"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"

    country: List[EutctDomain] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "doc": "D.2.4.1\tIMP previously used for CT in community MS",
        },
    )


@dataclass
class RoutesOfAdministration:
    class Meta:
        name = "routes_of_administration"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"

    route_of_administration: List[EutctDomain] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "doc": "D.3.7 IMP Routes of Administration",
        },
    )


@dataclass
class SomaticCell:
    class Meta:
        name = "somatic_cell"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"

    somatic_cell_autologous: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.4.1.1\tSomatic Cell Therapy origin autologous",
        },
    )
    somatic_cell_allogeneic: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.4.1.2\tSomatic Cell Therapy origin allogeneic",
        },
    )
    somatic_cell_xenogeneic: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.4.1.3\tSomatic Cell Therapy origin xenogeneic",
        },
    )
    somatic_cell_xen_sp_origin: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 200,
            "doc": "D.4.1.3.1 Somatic Cell Therapy xenogeneic species",
        },
    )
    somatic_cell_stem: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.4.2.1\tSomatic Cell Therapy type stem",
        },
    )
    somatic_cell_differenciated: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.4.2.2\tSomatic Cell Therapy type differentiated",
        },
    )
    somatic_cell_diff_type: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 200,
            "doc": "D.4.2.2.1 Type of differentiated cells",
        },
    )
    somatic_cell_others: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "nillable": True,
            "doc": "D.4.2.3 Somatic Cell Therapy type other",
        },
    )
    somatic_cell_others_specify: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "required": True,
            "max_length": 200,
            "doc": "D.4.2.3.1 Somatic Cell Therapy type other specification",
        },
    )


@dataclass
class BlindedRole:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    value: Optional[BlindedRoleEnumeration] = field(
        default=None,
        metadata={
            "required": True,
        },
    )


@dataclass
class CentralTechnicalFacility:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    organization_ref: Optional[OrganizationRef] = field(
        default=None,
        metadata={
            "name": "OrganizationRef",
            "type": "Element",
            "required": True,
        },
    )
    contact: Optional[Contact] = field(
        default=None,
        metadata={
            "name": "Contact",
            "type": "Element",
        },
    )
    central_technical_facility_duty: List[CentralTechnicalFacilityDuty] = field(
        default_factory=list,
        metadata={
            "name": "CentralTechnicalFacilityDuty",
            "type": "Element",
        },
    )


@dataclass
class Contacts:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    contact: List[Contact] = field(
        default_factory=list,
        metadata={
            "name": "Contact",
            "type": "Element",
            "min_occurs": 1,
        },
    )


@dataclass
class Fdainformation:
    class Meta:
        name = "FDAInformation"
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    is_fdaregulated_intervention: Optional[YesNoType] = field(
        default=None,
        metadata={
            "name": "IsFDARegulatedIntervention",
            "type": "Attribute",
            "required": True,
        },
    )
    is_indndeprotocol: Optional[YesNoType] = field(
        default=None,
        metadata={
            "name": "IsINDNDEProtocol",
            "type": "Attribute",
            "required": True,
        },
    )
    has_data_monitoring_committee: Optional[YesNoType] = field(
        default=None,
        metadata={
            "name": "HasDataMonitoringCommittee",
            "type": "Attribute",
        },
    )


@dataclass
class InstitutionalReviewBoardEthicsCommittee:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    organization_ref: Optional[OrganizationRef] = field(
        default=None,
        metadata={
            "name": "OrganizationRef",
            "type": "Element",
            "required": True,
        },
    )
    contact: List[Contact] = field(
        default_factory=list,
        metadata={
            "name": "Contact",
            "type": "Element",
            "min_occurs": 1,
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    approval: Optional[InstitutionalReviewBoardEthicsCommitteeApprovalType] = field(
        default=None,
        metadata={
            "name": "Approval",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class Network:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    organization_ref: Optional[OrganizationRef] = field(
        default=None,
        metadata={
            "name": "OrganizationRef",
            "type": "Element",
            "required": True,
        },
    )
    contact: Optional[Contact] = field(
        default=None,
        metadata={
            "name": "Contact",
            "type": "Element",
        },
    )
    network_activities: Optional[str] = field(
        default=None,
        metadata={
            "name": "NetworkActivities",
            "type": "Element",
            "required": True,
        },
    )


@dataclass
class OversightAuthority:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    organization_ref: Optional[OrganizationRef] = field(
        default=None,
        metadata={
            "name": "OrganizationRef",
            "type": "Element",
            "required": True,
        },
    )
    country_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "CountryCode",
            "type": "Attribute",
            "required": True,
        },
    )
    code_list_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "CodeListOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class RecruitmentCountries:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    recruitment_country: List[RecruitmentCountry] = field(
        default_factory=list,
        metadata={
            "name": "RecruitmentCountry",
            "type": "Element",
            "min_occurs": 1,
        },
    )


@dataclass
class RecruitmentStatus:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    recruitment_status_other: Optional[str] = field(
        default=None,
        metadata={
            "name": "RecruitmentStatusOther",
            "type": "Element",
        },
    )
    country: Optional[str] = field(
        default=None,
        metadata={
            "name": "Country",
            "type": "Attribute",
        },
    )
    current_status: Optional[CtrrecruitmentType] = field(
        default=None,
        metadata={
            "name": "CurrentStatus",
            "type": "Attribute",
            "required": True,
        },
    )
    recruitment_start_date: Optional[str] = field(
        default=None,
        metadata={
            "name": "RecruitmentStartDate",
            "type": "Attribute",
            "required": True,
            "pattern": r"([ ])?",
        },
    )
    recruitment_end_date: Optional[str] = field(
        default=None,
        metadata={
            "name": "RecruitmentEndDate",
            "type": "Attribute",
            "pattern": r"([ ])?",
        },
    )
    estimated_recruitment_duration: Optional[XmlDuration] = field(
        default=None,
        metadata={
            "name": "EstimatedRecruitmentDuration",
            "type": "Attribute",
        },
    )


@dataclass
class Registration:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    type: Optional[RegistrationType] = field(
        default=None,
        metadata={
            "name": "Type",
            "type": "Attribute",
            "required": True,
        },
    )
    registration_authority: Optional[str] = field(
        default=None,
        metadata={
            "name": "RegistrationAuthority",
            "type": "Attribute",
            "required": True,
        },
    )
    registration_date: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "RegistrationDate",
            "type": "Attribute",
        },
    )
    registration_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "RegistrationID",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class Role(CtrsimpleTypeDefinitionRole):
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"


@dataclass
class Sponsor:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    funding_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "FundingID",
            "type": "Attribute",
        },
    )
    organization_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OrganizationOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )
    user_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "UserOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )
    sponsor_type: Optional[SponsorTypeType] = field(
        default=None,
        metadata={
            "name": "SponsorType",
            "type": "Attribute",
        },
    )


@dataclass
class StudyCompletion:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    value: str = field(
        default="",
        metadata={
            "pattern": r"([ ])?",
        },
    )
    type: Optional[StudyDateType] = field(
        default=None,
        metadata={
            "name": "Type",
            "type": "Attribute",
        },
    )


@dataclass
class StudyEndDate:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    value: str = field(
        default="",
        metadata={
            "pattern": r"([ ])?",
        },
    )
    type: Optional[StudyDateType] = field(
        default=None,
        metadata={
            "name": "Type",
            "type": "Attribute",
        },
    )


@dataclass
class StudyEndDatePrimaryOutcome:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    value: str = field(
        default="",
        metadata={
            "pattern": r"([ ])?",
        },
    )
    type: Optional[StudyDateType] = field(
        default=None,
        metadata={
            "name": "Type",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class StudyRecruitmentStatus:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    status: Optional[StudyRecruitmentStatusType] = field(
        default=None,
        metadata={
            "name": "Status",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class StudyStartDate:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    value: str = field(
        default="",
        metadata={
            "pattern": r"([ ])?",
        },
    )
    type: Optional[StudyDateType] = field(
        default=None,
        metadata={
            "name": "Type",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class SubContractor:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    organization_ref: Optional[OrganizationRef] = field(
        default=None,
        metadata={
            "name": "OrganizationRef",
            "type": "Element",
            "required": True,
        },
    )
    contact: Optional[Contact] = field(
        default=None,
        metadata={
            "name": "Contact",
            "type": "Element",
        },
    )
    sub_contractor_duty: List[SubContractorDuty] = field(
        default_factory=list,
        metadata={
            "name": "SubContractorDuty",
            "type": "Element",
        },
    )


@dataclass
class Address(OdmcomplexTypeDefinitionAddress):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class Alias(OdmcomplexTypeDefinitionAlias):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ArchiveLayout(OdmcomplexTypeDefinitionArchiveLayout):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ArchiveLayoutRef(OdmcomplexTypeDefinitionArchiveLayoutRef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class CodeListRef(OdmcomplexTypeDefinitionCodeListRef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ExternalCodeList(OdmcomplexTypeDefinitionExternalCodeList):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ExternalQuestion(OdmcomplexTypeDefinitionExternalQuestion):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class FlagType(OdmcomplexTypeDefinitionFlagType):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class FlagValue(OdmcomplexTypeDefinitionFlagValue):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class FormalExpression(OdmcomplexTypeDefinitionFormalExpression):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ImputationMethod(OdmcomplexTypeDefinitionImputationMethod):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class Include(OdmcomplexTypeDefinitionInclude):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class InvestigatorRef(OdmcomplexTypeDefinitionInvestigatorRef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class KeySet(OdmcomplexTypeDefinitionKeySet):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class LocationRef(OdmcomplexTypeDefinitionLocationRef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class MeasurementUnitRef(OdmcomplexTypeDefinitionMeasurementUnitRef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class MetaDataVersionRef(OdmcomplexTypeDefinitionMetaDataVersionRef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class OdmcomplexTypeDefinitionComment:
    class Meta:
        name = "ODMcomplexTypeDefinition-Comment"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    sponsor_or_site: Optional[CommentType] = field(
        default=None,
        metadata={
            "name": "SponsorOrSite",
            "type": "Attribute",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionFormRef:
    class Meta:
        name = "ODMcomplexTypeDefinition-FormRef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    form_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "FormOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    order_number: Optional[int] = field(
        default=None,
        metadata={
            "name": "OrderNumber",
            "type": "Attribute",
        },
    )
    mandatory: Optional[YesOrNo] = field(
        default=None,
        metadata={
            "name": "Mandatory",
            "type": "Attribute",
            "required": True,
        },
    )
    collection_exception_condition_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "CollectionExceptionConditionOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataAny:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataAny"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    is_null: Optional[YesOnly] = field(
        default=None,
        metadata={
            "name": "IsNull",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataBase64Binary:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataBase64Binary"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: Optional[bytes] = field(
        default=None,
        metadata={
            "required": True,
            "format": "base64",
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataBase64Float:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataBase64Float"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: Optional[bytes] = field(
        default=None,
        metadata={
            "required": True,
            "max_length": 12,
            "format": "base64",
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataBoolean:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataBoolean"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: Optional[bool] = field(
        default=None,
        metadata={
            "required": True,
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataDate:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataDate"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: Optional[XmlDate] = field(
        default=None,
        metadata={
            "required": True,
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataDatetime:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataDatetime"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "required": True,
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataDouble:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataDouble"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "required": True,
            "pattern": r"(((\+|-)?[0-9]+(\.[0-9]+)?((D|d|E|e)(\+|-)[0-9]+)?)|(-?INF)|(NaN))",
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataDurationDatetime:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataDurationDatetime"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "pattern": r"([ ])?",
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataFloat:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataFloat"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: Optional[Decimal] = field(
        default=None,
        metadata={
            "required": True,
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataHexBinary:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataHexBinary"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: Optional[bytes] = field(
        default=None,
        metadata={
            "required": True,
            "format": "base16",
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataHexFloat:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataHexFloat"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: Optional[bytes] = field(
        default=None,
        metadata={
            "required": True,
            "max_length": 16,
            "format": "base16",
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataIncompleteDate:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataIncompleteDate"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "pattern": r"([ ])?",
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataIncompleteDatetime:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataIncompleteDatetime"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "pattern": r"([ ])?",
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataIncompleteTime:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataIncompleteTime"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "pattern": r"([ ])?",
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataInteger:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataInteger"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: Optional[int] = field(
        default=None,
        metadata={
            "required": True,
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataIntervalDatetime:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataIntervalDatetime"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "pattern": r"([ ])?",
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataPartialDate:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataPartialDate"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "pattern": r"([ ])?",
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataPartialDatetime:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataPartialDatetime"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "pattern": r"([ ])?",
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataPartialTime:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataPartialTime"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "pattern": r"([ ])?",
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataString:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataString"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataTime:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataTime"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: Optional[XmlTime] = field(
        default=None,
        metadata={
            "required": True,
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDataUri:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDataURI"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    audit_record_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AuditRecordID",
            "type": "Attribute",
        },
    )
    signature_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SignatureID",
            "type": "Attribute",
        },
    )
    annotation_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "AnnotationID",
            "type": "Attribute",
        },
    )
    measurement_unit_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemGroupRef:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemGroupRef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    item_group_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemGroupOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    order_number: Optional[int] = field(
        default=None,
        metadata={
            "name": "OrderNumber",
            "type": "Attribute",
        },
    )
    mandatory: Optional[YesOrNo] = field(
        default=None,
        metadata={
            "name": "Mandatory",
            "type": "Attribute",
            "required": True,
        },
    )
    collection_exception_condition_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "CollectionExceptionConditionOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemRef:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemRef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    key_sequence: Optional[int] = field(
        default=None,
        metadata={
            "name": "KeySequence",
            "type": "Attribute",
        },
    )
    method_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MethodOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )
    imputation_method_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ImputationMethodOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "name": "Role",
            "type": "Attribute",
        },
    )
    role_code_list_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "RoleCodeListOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )
    order_number: Optional[int] = field(
        default=None,
        metadata={
            "name": "OrderNumber",
            "type": "Attribute",
        },
    )
    mandatory: Optional[YesOrNo] = field(
        default=None,
        metadata={
            "name": "Mandatory",
            "type": "Attribute",
            "required": True,
        },
    )
    collection_exception_condition_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "CollectionExceptionConditionOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionSignatureDef:
    class Meta:
        name = "ODMcomplexTypeDefinition-SignatureDef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    meaning: Optional[str] = field(
        default=None,
        metadata={
            "name": "Meaning",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    legal_reason: Optional[str] = field(
        default=None,
        metadata={
            "name": "LegalReason",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    methodology: Optional[SignMethod] = field(
        default=None,
        metadata={
            "name": "Methodology",
            "type": "Attribute",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionStudyEventRef:
    class Meta:
        name = "ODMcomplexTypeDefinition-StudyEventRef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    study_event_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "StudyEventOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    order_number: Optional[int] = field(
        default=None,
        metadata={
            "name": "OrderNumber",
            "type": "Attribute",
        },
    )
    mandatory: Optional[YesOrNo] = field(
        default=None,
        metadata={
            "name": "Mandatory",
            "type": "Attribute",
            "required": True,
        },
    )
    collection_exception_condition_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "CollectionExceptionConditionOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class Picture(OdmcomplexTypeDefinitionPicture):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class Presentation(OdmcomplexTypeDefinitionPresentation):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class SignatureRef(OdmcomplexTypeDefinitionSignatureRef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class SiteRef(OdmcomplexTypeDefinitionSiteRef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class TranslatedText(OdmcomplexTypeDefinitionTranslatedText):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class UserRef(OdmcomplexTypeDefinitionUserRef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ActivityRef(SdmcomplexTypeDefinitionActivityRef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class ArmRef(SdmcomplexTypeDefinitionArmRef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class IncludeInclusionExclusionCriteria(
    SdmcomplexTypeDefinitionIncludeInclusionExclusionCriteria
):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class SegmentRef(SdmcomplexTypeDefinitionSegmentRef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class CanonicalizationMethod(CanonicalizationMethodType):
    class Meta:
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class DsakeyValue(DsakeyValueType):
    class Meta:
        name = "DSAKeyValue"
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class DigestMethod(DigestMethodType):
    class Meta:
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class Object(ObjectType):
    class Meta:
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class Pgpdata(PgpdataType):
    class Meta:
        name = "PGPData"
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class RsakeyValue(RsakeyValueType):
    class Meta:
        name = "RSAKeyValue"
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class Spkidata(SpkidataType):
    class Meta:
        name = "SPKIData"
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class SignatureMethod(SignatureMethodType):
    class Meta:
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class SignatureProperty(SignaturePropertyType):
    class Meta:
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class SignatureValue(SignatureValueType):
    class Meta:
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class Transform(TransformType):
    class Meta:
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class X509DataType:
    class Meta:
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    x509_issuer_serial: List[X509IssuerSerialType] = field(
        default_factory=list,
        metadata={
            "name": "X509IssuerSerial",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "sequential": True,
        },
    )
    x509_ski: List[bytes] = field(
        default_factory=list,
        metadata={
            "name": "X509SKI",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "sequential": True,
            "format": "base64",
        },
    )
    x509_subject_name: List[str] = field(
        default_factory=list,
        metadata={
            "name": "X509SubjectName",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "sequential": True,
        },
    )
    x509_certificate: List[bytes] = field(
        default_factory=list,
        metadata={
            "name": "X509Certificate",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "sequential": True,
            "format": "base64",
        },
    )
    x509_crl: List[bytes] = field(
        default_factory=list,
        metadata={
            "name": "X509CRL",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "sequential": True,
            "format": "base64",
        },
    )
    other_element: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##other",
            "sequential": True,
        },
    )


@dataclass
class InternationalizedTextsType100(InternationalizedTextsType):
    class Meta:
        name = "internationalized_texts_type_100"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"


@dataclass
class InternationalizedTextsType1000(InternationalizedTextsType):
    class Meta:
        name = "internationalized_texts_type_1000"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"


@dataclass
class InternationalizedTextsType200(InternationalizedTextsType):
    class Meta:
        name = "internationalized_texts_type_200"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"


@dataclass
class InternationalizedTextsType2000(InternationalizedTextsType):
    class Meta:
        name = "internationalized_texts_type_2000"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"


@dataclass
class InternationalizedTextsType250(InternationalizedTextsType):
    class Meta:
        name = "internationalized_texts_type_250"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"


@dataclass
class InternationalizedTextsType4000(InternationalizedTextsType):
    class Meta:
        name = "internationalized_texts_type_4000"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"


@dataclass
class InternationalizedTextsType500(InternationalizedTextsType):
    class Meta:
        name = "internationalized_texts_type_500"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"


@dataclass
class InternationalizedTextsType5000(InternationalizedTextsType):
    class Meta:
        name = "internationalized_texts_type_5000"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"


@dataclass
class InternationalizedTextsType800(InternationalizedTextsType):
    class Meta:
        name = "internationalized_texts_type_800"
        target_namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"


@dataclass
class MedicinalProduct:
    class Meta:
        name = "medicinal_product"
        namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"

    imp_category: Optional[EutctDomain] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.1.2 and D.1.3 IMP Category",
        },
    )
    has_ma: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.2.1 IMP has MA",
        },
    )
    imp_member_state: Optional[ImpMemberState] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "This element holds information about the member state",
        },
    )
    imp_identification_not_possible: Optional[ImpIdentificationNotPossible] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": (
                "This element holds information about a IMP that can't be " "identified"
            ),
        },
    )
    has_full_impd: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.2.3.1 Full IMPD submitted",
        },
    )
    has_simplified_impd: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.2.3.2 Simplified IMPD submitted",
        },
    )
    has_summary_of_prod_character: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.2.3.3 Only SmPC submitted",
        },
    )
    is_prev_auth_in_community: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.2.4 IMP previously used for CT in community",
        },
    )
    member_states: Optional[MemberStates] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": (
                "This element holds information about the IMP previously used "
                "for CT in community MS"
            ),
        },
    )
    is_orphan_drug_in_community: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.2.5 IMP is orphan drug",
        },
    )
    orphan_drug_designation_no: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 50,
            "doc": "D.2.5.1 Orphan drug number",
        },
    )
    has_scientific_advice: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.2.6 IMP subject of scientific advice",
        },
    )
    has_scientific_advice_chmp: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.2.6.1.1 SA from CHMP",
        },
    )
    has_scientific_advice_nca: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.2.6.1.2 SA from NCA",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 100,
            "doc": "D.3.1 IMP Name",
        },
    )
    code: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 50,
            "doc": "D.3.2 IMP Code",
        },
    )
    atc_codes: Optional[AtcCodes] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "This element holds information about ATC codes",
        },
    )
    pharmaceutical_form: Optional[EutctDomain] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.4 IMP Pharmaceutical Form",
        },
    )
    is_paediatric_formulation: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.4.1 Specific paediatric formulation",
        },
    )
    max_duration_imp: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 250,
            "doc": "D.3.5 Maximum duration of treatment",
        },
    )
    first_dose_fih_allowed: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 250,
            "doc": "D.3.6.1 First dose in FIH dose allowed",
        },
    )
    first_dose_fih_per_day_total: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.6.1 First dose in FIH Dose per Day or Total",
        },
    )
    first_dose_fih_total_dose_num: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 100,
            "doc": "D.3.6.1 First dose in FIH Total Dose Number",
        },
    )
    first_dose_fih_total_dose_unit: Optional[EutctDomain] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.6.1 First dose in FIHTotal Dose Unit",
        },
    )
    first_dose_fih_roa: Optional[EutctDomain] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.6.1 First dose in FIH Route of administration",
        },
    )
    max_dose_imp: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 250,
            "doc": "D.3.6.2 Maximum dose allowed",
        },
    )
    max_dose_perday_total_imp: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.6.2 Maximum Dose per Day or Total",
        },
    )
    total_dose_number: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 100,
            "doc": "D.3.6.2 Total Dose Number",
        },
    )
    total_dose_unit: Optional[EutctDomain] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.6.2 Total Dose Unit",
        },
    )
    max_dose_route_of_administration: Optional[EutctDomain] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.6.2 Route of administration for max dose",
        },
    )
    routes_of_administration: Optional[RoutesOfAdministration] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": (
                "This element holds information about the various routes of "
                "administration of the\nmedicinal product"
            ),
        },
    )
    has_chemical_origin: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.1 Chemical origin Active substance",
        },
    )
    has_biological_origin: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.2 Biological origin Active substance",
        },
    )
    is_advanced_therapy_mp: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.3 Advanced Therapy MP",
        },
    )
    is_somatic_therapy_mp: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.3.1 Somatic cell therapy MP",
        },
    )
    is_gene_therapy_mp: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.3.2 Gene therapy MP",
        },
    )
    is_tissue_engineered_mp: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.3.3 Tissue Engineered MP",
        },
    )
    is_combination_atimp: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.3.4 Combination ATIMP",
        },
    )
    is_cat_classification_isued: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.3.5 CAT Classification issued",
        },
    )
    cat_classification: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 200,
            "doc": "D.3.11.3.5.1 CAT Classification",
        },
    )
    is_device_included: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.4 Combination product including device",
        },
    )
    is_radiopharmaceutical_mp: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.5 Radiopharmaceutical MP",
        },
    )
    is_immunological_mp: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.6 Immunological MP",
        },
    )
    is_plasma_derived_mp: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.7 Plasma derived MP",
        },
    )
    is_other_extractive: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.8 Extractive MP",
        },
    )
    is_recombinant_mp: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.9 Recombinant MP",
        },
    )
    is_gmo_mp: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.10 GMO MP",
        },
    )
    is_genetically_mod_auth_accord: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.10.1\tGMP MP Auth granted",
        },
    )
    is_genetically_mod_auth_pend: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.10.2\tGMP MP Auth pending",
        },
    )
    is_herbal_mp: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.11 Herbal MP",
        },
    )
    is_homeopathetic_mp: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.12 Homeopathic MP",
        },
    )
    is_other_mp: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.11.13 Other MP",
        },
    )
    other_mp_specification: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 200,
            "doc": "D.3.11.13.1\tOther MP Specification",
        },
    )
    mode_of_action: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 500,
            "doc": "D.3.12 Mode of action",
        },
    )
    is_first_in_human: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.13 First in Human",
        },
    )
    first_in_human_risk_factors: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "required": True,
            "max_length": 500,
            "doc": "D.3.13.1 First in Human Risk Factors",
        },
    )
    somatic_cell: Optional[SomaticCell] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.4\tSomatic Cell Therapy IMP",
        },
    )
    gene_therapy: Optional[GeneTherapy] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.5\tGene Therapy IMP",
        },
    )
    cell_origin: Optional[CellOrigin] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.6.1 Tissue Engineered origin",
        },
    )
    cell_type: Optional[CellType] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.6.2 Tissue Engineered type",
        },
    )
    imp_device: Optional[ImpDevice] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.7\tProducts containing devices",
        },
    )
    active_substances: Optional[ActiveSubstances] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "D.3.9 Active substances",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "pattern": r"PR[0-9]{1,2}",
        },
    )


@dataclass
class Authorities:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    fdainformation: Optional[Fdainformation] = field(
        default=None,
        metadata={
            "name": "FDAInformation",
            "type": "Element",
        },
    )
    institutional_review_board_ethics_committee: List[
        InstitutionalReviewBoardEthicsCommittee
    ] = field(
        default_factory=list,
        metadata={
            "name": "InstitutionalReviewBoardEthicsCommittee",
            "type": "Element",
        },
    )
    oversight_authority: List[OversightAuthority] = field(
        default_factory=list,
        metadata={
            "name": "OversightAuthority",
            "type": "Element",
        },
    )


@dataclass
class CentralTechnicalFacilities:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    central_technical_facility: List[CentralTechnicalFacility] = field(
        default_factory=list,
        metadata={
            "name": "CentralTechnicalFacility",
            "type": "Element",
            "min_occurs": 1,
        },
    )


@dataclass
class FundingSupport:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    sponsor: List[Sponsor] = field(
        default_factory=list,
        metadata={
            "name": "Sponsor",
            "type": "Element",
            "min_occurs": 1,
        },
    )


@dataclass
class Networks:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    network: List[Network] = field(
        default_factory=list,
        metadata={
            "name": "Network",
            "type": "Element",
            "min_occurs": 1,
        },
    )


@dataclass
class Organization:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    address: List[Address] = field(
        default_factory=list,
        metadata={
            "name": "Address",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    email: List[str] = field(
        default_factory=list,
        metadata={
            "name": "Email",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    fax: List[str] = field(
        default_factory=list,
        metadata={
            "name": "Fax",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    certificate: List[str] = field(
        default_factory=list,
        metadata={
            "name": "Certificate",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    role: List[Role] = field(
        default_factory=list,
        metadata={
            "name": "Role",
            "type": "Element",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


@dataclass
class PublicTitle:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    translated_text: List[TranslatedText] = field(
        default_factory=list,
        metadata={
            "name": "TranslatedText",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "min_occurs": 1,
        },
    )


@dataclass
class Recruitment:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    recruitment_countries: Optional[RecruitmentCountries] = field(
        default=None,
        metadata={
            "name": "RecruitmentCountries",
            "type": "Element",
            "required": True,
        },
    )
    recruitment_status: List[RecruitmentStatus] = field(
        default_factory=list,
        metadata={
            "name": "RecruitmentStatus",
            "type": "Element",
            "min_occurs": 1,
        },
    )


@dataclass
class Registrations:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    registration: List[Registration] = field(
        default_factory=list,
        metadata={
            "name": "Registration",
            "type": "Element",
            "min_occurs": 1,
        },
    )


@dataclass
class StudyDetailedDescription:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    translated_text: List[TranslatedText] = field(
        default_factory=list,
        metadata={
            "name": "TranslatedText",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "min_occurs": 1,
        },
    )


@dataclass
class StudyNameLocalizations:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    translated_text: List[TranslatedText] = field(
        default_factory=list,
        metadata={
            "name": "TranslatedText",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "min_occurs": 1,
        },
    )


@dataclass
class SubContractors:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    sub_contractor: List[SubContractor] = field(
        default_factory=list,
        metadata={
            "name": "SubContractor",
            "type": "Element",
            "min_occurs": 1,
        },
    )


@dataclass
class Comment(OdmcomplexTypeDefinitionComment):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class FormRef(OdmcomplexTypeDefinitionFormRef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataAny(OdmcomplexTypeDefinitionItemDataAny):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataBase64Binary(OdmcomplexTypeDefinitionItemDataBase64Binary):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataBase64Float(OdmcomplexTypeDefinitionItemDataBase64Float):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataBoolean(OdmcomplexTypeDefinitionItemDataBoolean):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataDate(OdmcomplexTypeDefinitionItemDataDate):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataDatetime(OdmcomplexTypeDefinitionItemDataDatetime):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataDouble(OdmcomplexTypeDefinitionItemDataDouble):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataDurationDatetime(OdmcomplexTypeDefinitionItemDataDurationDatetime):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataFloat(OdmcomplexTypeDefinitionItemDataFloat):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataHexBinary(OdmcomplexTypeDefinitionItemDataHexBinary):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataHexFloat(OdmcomplexTypeDefinitionItemDataHexFloat):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataIncompleteDate(OdmcomplexTypeDefinitionItemDataIncompleteDate):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataIncompleteDatetime(OdmcomplexTypeDefinitionItemDataIncompleteDatetime):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataIncompleteTime(OdmcomplexTypeDefinitionItemDataIncompleteTime):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataInteger(OdmcomplexTypeDefinitionItemDataInteger):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataIntervalDatetime(OdmcomplexTypeDefinitionItemDataIntervalDatetime):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataPartialDate(OdmcomplexTypeDefinitionItemDataPartialDate):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataPartialDatetime(OdmcomplexTypeDefinitionItemDataPartialDatetime):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataPartialTime(OdmcomplexTypeDefinitionItemDataPartialTime):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataString(OdmcomplexTypeDefinitionItemDataString):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataTime(OdmcomplexTypeDefinitionItemDataTime):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDataUri(OdmcomplexTypeDefinitionItemDataUri):
    class Meta:
        name = "ItemDataURI"
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemGroupRef(OdmcomplexTypeDefinitionItemGroupRef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemRef(OdmcomplexTypeDefinitionItemRef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class OdmcomplexTypeDefinitionAuditRecord:
    class Meta:
        name = "ODMcomplexTypeDefinition-AuditRecord"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    user_ref: Optional[UserRef] = field(
        default=None,
        metadata={
            "name": "UserRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    location_ref: Optional[LocationRef] = field(
        default=None,
        metadata={
            "name": "LocationRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    date_time_stamp: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "DateTimeStamp",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    reason_for_change: Optional[str] = field(
        default=None,
        metadata={
            "name": "ReasonForChange",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    source_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "SourceID",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    edit_point: Optional[EditPointType] = field(
        default=None,
        metadata={
            "name": "EditPoint",
            "type": "Attribute",
        },
    )
    used_imputation_method: Optional[YesOrNo] = field(
        default=None,
        metadata={
            "name": "UsedImputationMethod",
            "type": "Attribute",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ID",
            "type": "Attribute",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionDecode:
    class Meta:
        name = "ODMcomplexTypeDefinition-Decode"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    translated_text: List[TranslatedText] = field(
        default_factory=list,
        metadata={
            "name": "TranslatedText",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "min_occurs": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionDescription:
    class Meta:
        name = "ODMcomplexTypeDefinition-Description"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    translated_text: List[TranslatedText] = field(
        default_factory=list,
        metadata={
            "name": "TranslatedText",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "min_occurs": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionEnumeratedItem:
    class Meta:
        name = "ODMcomplexTypeDefinition-EnumeratedItem"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    alias: List[Alias] = field(
        default_factory=list,
        metadata={
            "name": "Alias",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    coded_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "CodedValue",
            "type": "Attribute",
            "required": True,
        },
    )
    rank: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Rank",
            "type": "Attribute",
        },
    )
    order_number: Optional[int] = field(
        default=None,
        metadata={
            "name": "OrderNumber",
            "type": "Attribute",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionErrorMessage:
    class Meta:
        name = "ODMcomplexTypeDefinition-ErrorMessage"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    translated_text: List[TranslatedText] = field(
        default_factory=list,
        metadata={
            "name": "TranslatedText",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "min_occurs": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionFlag:
    class Meta:
        name = "ODMcomplexTypeDefinition-Flag"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    flag_value: Optional[FlagValue] = field(
        default=None,
        metadata={
            "name": "FlagValue",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    flag_type: Optional[FlagType] = field(
        default=None,
        metadata={
            "name": "FlagType",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionLocation:
    class Meta:
        name = "ODMcomplexTypeDefinition-Location"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    meta_data_version_ref: List[MetaDataVersionRef] = field(
        default_factory=list,
        metadata={
            "name": "MetaDataVersionRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "min_occurs": 1,
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    location_type: Optional[LocationType] = field(
        default=None,
        metadata={
            "name": "LocationType",
            "type": "Attribute",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionQuestion:
    class Meta:
        name = "ODMcomplexTypeDefinition-Question"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    translated_text: List[TranslatedText] = field(
        default_factory=list,
        metadata={
            "name": "TranslatedText",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "min_occurs": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionSignature:
    class Meta:
        name = "ODMcomplexTypeDefinition-Signature"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    user_ref: Optional[UserRef] = field(
        default=None,
        metadata={
            "name": "UserRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    location_ref: Optional[LocationRef] = field(
        default=None,
        metadata={
            "name": "LocationRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    signature_ref: Optional[SignatureRef] = field(
        default=None,
        metadata={
            "name": "SignatureRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    date_time_stamp: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "DateTimeStamp",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    crypto_binding_manifest: Optional[str] = field(
        default=None,
        metadata={
            "name": "CryptoBindingManifest",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ID",
            "type": "Attribute",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionSymbol:
    class Meta:
        name = "ODMcomplexTypeDefinition-Symbol"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    translated_text: List[TranslatedText] = field(
        default_factory=list,
        metadata={
            "name": "TranslatedText",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "min_occurs": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionUser:
    class Meta:
        name = "ODMcomplexTypeDefinition-User"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    login_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "LoginName",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    display_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "DisplayName",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    full_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "FullName",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    first_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "FirstName",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    last_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "LastName",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    organization: Optional[str] = field(
        default=None,
        metadata={
            "name": "Organization",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    address: List[Address] = field(
        default_factory=list,
        metadata={
            "name": "Address",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    email: List[str] = field(
        default_factory=list,
        metadata={
            "name": "Email",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    picture: Optional[Picture] = field(
        default=None,
        metadata={
            "name": "Picture",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    pager: Optional[str] = field(
        default=None,
        metadata={
            "name": "Pager",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    fax: List[str] = field(
        default_factory=list,
        metadata={
            "name": "Fax",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    phone: List[str] = field(
        default_factory=list,
        metadata={
            "name": "Phone",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    location_ref: List[LocationRef] = field(
        default_factory=list,
        metadata={
            "name": "LocationRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    certificate: List[str] = field(
        default_factory=list,
        metadata={
            "name": "Certificate",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    role: List[Role] = field(
        default_factory=list,
        metadata={
            "name": "Role",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
        },
    )
    organization_ref: List[OrganizationRef] = field(
        default_factory=list,
        metadata={
            "name": "OrganizationRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
        },
    )
    qualifications: List[str] = field(
        default_factory=list,
        metadata={
            "name": "Qualifications",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    user_type: Optional[UserType] = field(
        default=None,
        metadata={
            "name": "UserType",
            "type": "Attribute",
        },
    )


@dataclass
class SignatureDef(OdmcomplexTypeDefinitionSignatureDef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class StudyEventRef(OdmcomplexTypeDefinitionStudyEventRef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class SdmcomplexTypeDefinitionArmAssociation:
    """
    A ArmAssociation links cell definitions to arms.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-ArmAssociation"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    arm_ref: List[ArmRef] = field(
        default_factory=list,
        metadata={
            "name": "ArmRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "min_occurs": 1,
            "doc": "List of references to Arms",
        },
    )
    blinded_role: List[BlindedRoleEnumeration] = field(
        default_factory=list,
        metadata={
            "name": "BlindedRole",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
        },
    )
    type: Optional[Blindunblind] = field(
        default=None,
        metadata={
            "name": "Type",
            "type": "Attribute",
            "required": True,
            "doc": "Indication of whether or not the arms are blinded of not",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionValue:
    class Meta:
        name = "SDMcomplexTypeDefinition-Value"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    scope: Optional[str] = field(
        default=None,
        metadata={
            "name": "Scope",
            "type": "Attribute",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
        },
    )
    code_list_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "CodeListOID",
            "type": "Attribute",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
            "min_length": 1,
        },
    )
    display_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "DisplayValue",
            "type": "Attribute",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
        },
    )
    content: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
            "choices": (
                {
                    "name": "TranslatedText",
                    "type": TranslatedText,
                    "namespace": "http://www.cdisc.org/ns/odm/v1.3",
                },
            ),
        },
    )


@dataclass
class KeyValueType:
    class Meta:
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    content: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
            "choices": (
                {
                    "name": "DSAKeyValue",
                    "type": DsakeyValue,
                    "namespace": "http://www.w3.org/2000/09/xmldsig#",
                },
                {
                    "name": "RSAKeyValue",
                    "type": RsakeyValue,
                    "namespace": "http://www.w3.org/2000/09/xmldsig#",
                },
            ),
        },
    )


@dataclass
class SignaturePropertiesType:
    class Meta:
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    signature_property: List[SignatureProperty] = field(
        default_factory=list,
        metadata={
            "name": "SignatureProperty",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "min_occurs": 1,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Attribute",
        },
    )


@dataclass
class TransformsType:
    class Meta:
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    transform: List[Transform] = field(
        default_factory=list,
        metadata={
            "name": "Transform",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "min_occurs": 1,
        },
    )


@dataclass
class X509Data(X509DataType):
    class Meta:
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class MedicinalProductInformation:
    """
    This element groups information about the clinical trial medicinal product
    information.
    """

    class Meta:
        name = "medicinal_product_information"
        namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"

    medicinal_product: List[MedicinalProduct] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "",
        },
    )


@dataclass
class PopulationInformation:
    class Meta:
        name = "population_information"
        namespace = "http://eudract.emea.europa.eu/schema/clinical_trial"

    has_under_18: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.1.1 Population under eighteen",
        },
    )
    under_18_subjects_no: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "min_inclusive": 0,
            "max_inclusive": 9999999999,
            "nillable": True,
            "doc": "F.1.1 Population number under eighteen",
        },
    )
    has_in_utero: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.1.1.1 Population in utero",
        },
    )
    in_utero_no: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "min_inclusive": 0,
            "max_inclusive": 9999999999,
            "nillable": True,
            "doc": "F.1.1.1.1 Population number in utero",
        },
    )
    has_preterm_newborn_infants: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.1.1.2 Population preterm newborn infants",
        },
    )
    preterm_newborn_infants_no: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "min_inclusive": 0,
            "max_inclusive": 9999999999,
            "nillable": True,
            "doc": "F.1.1.2.1 Population number preterm newborn infants",
        },
    )
    has_newborns: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.1.1.3 Population newborns",
        },
    )
    newborns_no: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "min_inclusive": 0,
            "max_inclusive": 9999999999,
            "nillable": True,
            "doc": "F.1.1.3.1 Population number newborns",
        },
    )
    has_infants_and_toddlers: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.1.1.4 Population infants and toddlers",
        },
    )
    infants_and_toddlers_no: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "min_inclusive": 0,
            "max_inclusive": 9999999999,
            "nillable": True,
            "doc": "F.1.1.4.1 Population number infants and toddlers",
        },
    )
    has_childen: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.1.1.5 Population children",
        },
    )
    childen_no: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "min_inclusive": 0,
            "max_inclusive": 9999999999,
            "nillable": True,
            "doc": "F.1.1.5.1 Population number children",
        },
    )
    has_adolescents: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.1.1.6 Population adolescents",
        },
    )
    adolescents_no: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "min_inclusive": 0,
            "max_inclusive": 9999999999,
            "nillable": True,
            "doc": "F.1.1.6.1 Population number adolescents",
        },
    )
    has_adults: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.1.2 Population adults",
        },
    )
    adults_no: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "min_inclusive": 0,
            "max_inclusive": 9999999999,
            "nillable": True,
            "doc": "F.1.2.1 Population number adults",
        },
    )
    has_elderly: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.1.3 Population elderly",
        },
    )
    elderly_no: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "min_inclusive": 0,
            "max_inclusive": 9999999999,
            "nillable": True,
            "doc": "F.1.3.1 Population number elderly",
        },
    )
    is_gender_male: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.2.1 Population male",
        },
    )
    is_gender_female: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.2.2 Population female",
        },
    )
    has_healthy_volunteers: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.3.1 Population healthy volunteers",
        },
    )
    has_patients: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.3.2 Population patients",
        },
    )
    has_specific_vunerable_popul: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.3.3 Population specific vunerable populations",
        },
    )
    has_women_child_bear_contra: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": (
                "F.3.3.1 Population women of child bearing potential no "
                "contraception"
            ),
        },
    )
    has_women_child_bear_potent: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": (
                "F.3.3.2 Population women of child bearing potential " "contraception"
            ),
        },
    )
    has_pregnant_women: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.3.3.3 Population pregnant women",
        },
    )
    has_nursing_women: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.3.3.4 Population nursing women",
        },
    )
    has_emergency_situation: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.3.3.5 Population emergency situation",
        },
    )
    has_incapable_consent: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.3.3.6 Population subjects incapable of giving consent",
        },
    )
    has_incapable_consent_details_localized: Optional[
        "PopulationInformation.HasIncapableConsentDetailsLocalized"
    ] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
        },
    )
    has_other_patient: Optional[BooleanDomain] = field(
        default=BooleanDomain.VALUE_0,
        metadata={
            "type": "Element",
            "nillable": True,
            "doc": "F.3.3.7 Population other subjects",
        },
    )
    other_patient_details_localized: Optional[
        "PopulationInformation.OtherPatientDetailsLocalized"
    ] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
        },
    )
    in_ms_no: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "min_inclusive": 0,
            "max_inclusive": 999999,
            "nillable": True,
            "doc": "F.4.1 Population planned numbers in MS",
        },
    )
    in_eea_no: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "min_inclusive": 0,
            "max_inclusive": 999999,
            "nillable": True,
            "doc": "F.4.2.1 Population planned numbers in EEA",
        },
    )
    in_whole_trial: Optional[int] = field(
        default=None,
        metadata={
            "type": "Element",
            "min_inclusive": 0,
            "max_inclusive": 999999,
            "nillable": True,
            "doc": "F.4.2.2 Population planned numbers in whole trial",
        },
    )
    post_trial_treatment_details_localized: Optional[
        "PopulationInformation.PostTrialTreatmentDetailsLocalized"
    ] = field(
        default=None,
        metadata={
            "type": "Element",
            "nillable": True,
        },
    )

    @dataclass
    class HasIncapableConsentDetailsLocalized:
        has_incapable_consent_details: List[InternationalizedTextsType250] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "doc": (
                    "F.3.3.6.1 Population subjects incapable of giving consent "
                    "details"
                ),
            },
        )

    @dataclass
    class OtherPatientDetailsLocalized:
        other_patient_details: List[InternationalizedTextsType100] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "doc": "F.3.3.7.1 Population other subjects details",
            },
        )

    @dataclass
    class PostTrialTreatmentDetailsLocalized:
        post_trial_treatment_details: List[InternationalizedTextsType500] = field(
            default_factory=list,
            metadata={
                "type": "Element",
                "doc": "F.5 Population post trial treatment details",
            },
        )


@dataclass
class AuditRecord(OdmcomplexTypeDefinitionAuditRecord):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class Decode(OdmcomplexTypeDefinitionDecode):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class Description(OdmcomplexTypeDefinitionDescription):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class EnumeratedItem(OdmcomplexTypeDefinitionEnumeratedItem):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ErrorMessage(OdmcomplexTypeDefinitionErrorMessage):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class Flag(OdmcomplexTypeDefinitionFlag):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class Location(OdmcomplexTypeDefinitionLocation):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class OdmcomplexTypeDefinitionStudyName:
    class Meta:
        name = "ODMcomplexTypeDefinition-StudyName"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    study_name_localizations: List[StudyNameLocalizations] = field(
        default_factory=list,
        metadata={
            "name": "StudyNameLocalizations",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
        },
    )


@dataclass
class Question(OdmcomplexTypeDefinitionQuestion):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class Signature2(OdmcomplexTypeDefinitionSignature):
    class Meta:
        name = "Signature"
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class Symbol(OdmcomplexTypeDefinitionSymbol):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class User(OdmcomplexTypeDefinitionUser):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ArmAssociation(SdmcomplexTypeDefinitionArmAssociation):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class Value(SdmcomplexTypeDefinitionValue):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class KeyValue(KeyValueType):
    class Meta:
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class SignatureProperties(SignaturePropertiesType):
    class Meta:
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class Transforms(TransformsType):
    class Meta:
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class Intervention:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    intervention_other_name: List[str] = field(
        default_factory=list,
        metadata={
            "name": "InterventionOtherName",
            "type": "Element",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
        },
    )
    intervention_type: Optional[InterventionTypeType] = field(
        default=None,
        metadata={
            "name": "InterventionType",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class TimePoint:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    formal_expression: List[FormalExpression] = field(
        default_factory=list,
        metadata={
            "name": "FormalExpression",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "min_occurs": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionAdminData:
    class Meta:
        name = "ODMcomplexTypeDefinition-AdminData"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    user: List[User] = field(
        default_factory=list,
        metadata={
            "name": "User",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    location: List[Location] = field(
        default_factory=list,
        metadata={
            "name": "Location",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    signature_def: List[SignatureDef] = field(
        default_factory=list,
        metadata={
            "name": "SignatureDef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    organization: List[Organization] = field(
        default_factory=list,
        metadata={
            "name": "Organization",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
        },
    )
    central_technical_facilities: List[CentralTechnicalFacilities] = field(
        default_factory=list,
        metadata={
            "name": "CentralTechnicalFacilities",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
            "sequential": True,
        },
    )
    networks: List[Networks] = field(
        default_factory=list,
        metadata={
            "name": "Networks",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
            "sequential": True,
        },
    )
    sub_contractors: List[SubContractors] = field(
        default_factory=list,
        metadata={
            "name": "SubContractors",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
            "sequential": True,
        },
    )
    study_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "StudyOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionAnnotation:
    class Meta:
        name = "ODMcomplexTypeDefinition-Annotation"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    comment: Optional[Comment] = field(
        default=None,
        metadata={
            "name": "Comment",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    flag: List[Flag] = field(
        default_factory=list,
        metadata={
            "name": "Flag",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    seq_num: Optional[int] = field(
        default=None,
        metadata={
            "name": "SeqNum",
            "type": "Attribute",
            "required": True,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ID",
            "type": "Attribute",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionAuditRecords:
    class Meta:
        name = "ODMcomplexTypeDefinition-AuditRecords"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    audit_record: List[AuditRecord] = field(
        default_factory=list,
        metadata={
            "name": "AuditRecord",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionCodeListItem:
    class Meta:
        name = "ODMcomplexTypeDefinition-CodeListItem"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    decode: Optional[Decode] = field(
        default=None,
        metadata={
            "name": "Decode",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    alias: List[Alias] = field(
        default_factory=list,
        metadata={
            "name": "Alias",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    coded_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "CodedValue",
            "type": "Attribute",
            "required": True,
        },
    )
    rank: Optional[Decimal] = field(
        default=None,
        metadata={
            "name": "Rank",
            "type": "Attribute",
        },
    )
    order_number: Optional[int] = field(
        default=None,
        metadata={
            "name": "OrderNumber",
            "type": "Attribute",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionConditionDef:
    class Meta:
        name = "ODMcomplexTypeDefinition-ConditionDef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    formal_expression: List[FormalExpression] = field(
        default_factory=list,
        metadata={
            "name": "FormalExpression",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    alias: List[Alias] = field(
        default_factory=list,
        metadata={
            "name": "Alias",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionFormDef:
    class Meta:
        name = "ODMcomplexTypeDefinition-FormDef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_group_ref: List[ItemGroupRef] = field(
        default_factory=list,
        metadata={
            "name": "ItemGroupRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    archive_layout: List[ArchiveLayout] = field(
        default_factory=list,
        metadata={
            "name": "ArchiveLayout",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    alias: List[Alias] = field(
        default_factory=list,
        metadata={
            "name": "Alias",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    repeating: Optional[YesOrNo] = field(
        default=None,
        metadata={
            "name": "Repeating",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemGroupDef:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemGroupDef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_ref: List[ItemRef] = field(
        default_factory=list,
        metadata={
            "name": "ItemRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    alias: List[Alias] = field(
        default_factory=list,
        metadata={
            "name": "Alias",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    repeating: Optional[YesOrNo] = field(
        default=None,
        metadata={
            "name": "Repeating",
            "type": "Attribute",
            "required": True,
        },
    )
    is_reference_data: Optional[YesOrNo] = field(
        default=None,
        metadata={
            "name": "IsReferenceData",
            "type": "Attribute",
        },
    )
    sasdataset_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "SASDatasetName",
            "type": "Attribute",
            "max_length": 8,
            "pattern": r"[A-Za-z_][A-Za-z0-9_]*",
        },
    )
    domain: Optional[str] = field(
        default=None,
        metadata={
            "name": "Domain",
            "type": "Attribute",
        },
    )
    origin: Optional[str] = field(
        default=None,
        metadata={
            "name": "Origin",
            "type": "Attribute",
        },
    )
    role: Optional[str] = field(
        default=None,
        metadata={
            "name": "Role",
            "type": "Attribute",
            "min_length": 1,
        },
    )
    purpose: Optional[str] = field(
        default=None,
        metadata={
            "name": "Purpose",
            "type": "Attribute",
        },
    )
    comment: Optional[str] = field(
        default=None,
        metadata={
            "name": "Comment",
            "type": "Attribute",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionMeasurementUnit:
    class Meta:
        name = "ODMcomplexTypeDefinition-MeasurementUnit"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    symbol: Optional[Symbol] = field(
        default=None,
        metadata={
            "name": "Symbol",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    alias: List[Alias] = field(
        default_factory=list,
        metadata={
            "name": "Alias",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionMethodDef:
    class Meta:
        name = "ODMcomplexTypeDefinition-MethodDef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    formal_expression: List[FormalExpression] = field(
        default_factory=list,
        metadata={
            "name": "FormalExpression",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    alias: List[Alias] = field(
        default_factory=list,
        metadata={
            "name": "Alias",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    type: Optional[MethodType] = field(
        default=None,
        metadata={
            "name": "Type",
            "type": "Attribute",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionRangeCheck:
    class Meta:
        name = "ODMcomplexTypeDefinition-RangeCheck"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    check_value: List[str] = field(
        default_factory=list,
        metadata={
            "name": "CheckValue",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    formal_expression: List[FormalExpression] = field(
        default_factory=list,
        metadata={
            "name": "FormalExpression",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    measurement_unit_ref: Optional[MeasurementUnitRef] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    error_message: Optional[ErrorMessage] = field(
        default=None,
        metadata={
            "name": "ErrorMessage",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    comparator: Optional[Comparator] = field(
        default=None,
        metadata={
            "name": "Comparator",
            "type": "Attribute",
        },
    )
    soft_hard: Optional[SoftOrHard] = field(
        default=None,
        metadata={
            "name": "SoftHard",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionSignatures:
    class Meta:
        name = "ODMcomplexTypeDefinition-Signatures"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    signature: List[Signature2] = field(
        default_factory=list,
        metadata={
            "name": "Signature",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionStudyEventDef:
    class Meta:
        name = "ODMcomplexTypeDefinition-StudyEventDef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    form_ref: List[FormRef] = field(
        default_factory=list,
        metadata={
            "name": "FormRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    alias: List[Alias] = field(
        default_factory=list,
        metadata={
            "name": "Alias",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    activity_ref: List[ActivityRef] = field(
        default_factory=list,
        metadata={
            "name": "ActivityRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    repeating: Optional[YesOrNo] = field(
        default=None,
        metadata={
            "name": "Repeating",
            "type": "Attribute",
            "required": True,
        },
    )
    type: Optional[EventType] = field(
        default=None,
        metadata={
            "name": "Type",
            "type": "Attribute",
            "required": True,
        },
    )
    category: Optional[str] = field(
        default=None,
        metadata={
            "name": "Category",
            "type": "Attribute",
        },
    )


@dataclass
class StudyName(OdmcomplexTypeDefinitionStudyName):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class SdmcomplexTypeDefinitionAbsoluteTimingConstraint:
    """
    Each absolute timing constraint limits when an activity can take place
    during a given time interval, or to specifies an exact date and time as the
    ideal timing for an activity.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-AbsoluteTimingConstraint"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Unique identifier for the timing constraint.",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "The name of the timing constraint.",
        },
    )
    activity_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ActivityOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": (
                "The Activity identifier that this timing constraint refers " "to."
            ),
        },
    )
    timepoint_target: Optional[str] = field(
        default=None,
        metadata={
            "name": "TimepointTarget",
            "type": "Attribute",
            "required": True,
            "pattern": r"([ ])?",
            "doc": ("The point in time at which the activity ideally should start."),
        },
    )
    timepoint_granularity: Optional[Timepointgranularitytype] = field(
        default=None,
        metadata={
            "name": "TimepointGranularity",
            "type": "Attribute",
            "doc": (
                "The granularity that should be applied to the window once the"
                " target time has had the pre and post windows applied."
            ),
        },
    )
    timepoint_pre_window: Optional[str] = field(
        default=None,
        metadata={
            "name": "TimepointPreWindow",
            "type": "Attribute",
            "pattern": r"[^\-].+",
            "doc": (
                "Specifies a window (duration) prior to the target time when "
                "it is allowed for the activity to start."
            ),
        },
    )
    timepoint_post_window: Optional[str] = field(
        default=None,
        metadata={
            "name": "TimepointPostWindow",
            "type": "Attribute",
            "pattern": r"[^\-].+",
            "doc": (
                "Specifies a window (duration) after the target time when it "
                "is allowed for the activity to start."
            ),
        },
    )


@dataclass
class SdmcomplexTypeDefinitionActivityDef:
    """
    An ActivityDef represents a point in a study at which a specific actions
    are to be taken.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-ActivityDef"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "doc": "Activity description",
        },
    )
    form_ref: List[FormRef] = field(
        default_factory=list,
        metadata={
            "name": "FormRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "doc": (
                "List of references to odm:FormDefs which are to be collected."
                "  Indicates that the activity is a data collection activity."
            ),
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Unique identifier for the activity",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Short name for the activity",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionActivityDuration:
    """
    Defines the normal length of time that an activity would take, also
    allowing the specification of plus/minus windows.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-ActivityDuration"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Unique identifier for the activity duration.",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "The name of the activity duration.",
        },
    )
    activity_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ActivityOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "The activity to which this duration information relates.",
        },
    )
    planned_duration: Optional[str] = field(
        default=None,
        metadata={
            "name": "PlannedDuration",
            "type": "Attribute",
            "required": True,
            "pattern": r"([ ])?",
            "doc": "The length of time that the activity would normally take.",
        },
    )
    planned_duration_pre_window: Optional[str] = field(
        default=None,
        metadata={
            "name": "PlannedDurationPreWindow",
            "type": "Attribute",
            "pattern": r"[^\-].+",
            "doc": (
                "A duration that would be applied to the planned duration to "
                "calculate the pre-window."
            ),
        },
    )
    planned_duration_post_window: Optional[str] = field(
        default=None,
        metadata={
            "name": "PlannedDurationPostWindow",
            "type": "Attribute",
            "pattern": r"[^\-].+",
            "doc": (
                "A duration that would be applied to the planned duration to "
                "calculate the post-window."
            ),
        },
    )


@dataclass
class SdmcomplexTypeDefinitionArm:
    """
    An Arm element provides the declaration of a study arm.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-Arm"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "doc": "Arm description",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Unique identifier for the arm",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Short name for the arm",
        },
    )
    intervention_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "InterventionOID",
            "type": "Attribute",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
            "min_length": 1,
        },
    )
    ctarm_type: Optional[CtarmTypeEnumeration] = field(
        default=None,
        metadata={
            "name": "CTArmType",
            "type": "Attribute",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionCellDef:
    """
    A CellDef provides for the declaration of a study cell, which is a common
    study-design visualization for the intersection of an epoch with an arm.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-CellDef"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "doc": "Cell description",
        },
    )
    arm_association: Optional[ArmAssociation] = field(
        default=None,
        metadata={
            "name": "ArmAssociation",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": ("Container for definition association between cells and arms"),
        },
    )
    segment_ref: List[SegmentRef] = field(
        default_factory=list,
        metadata={
            "name": "SegmentRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "List of segments contained in the cell.",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Unique identifier for the cell",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Short name for the cell",
        },
    )
    epoch_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "EpochOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "OID of the Epoch in which the cell is contained.",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionCriterion:
    """
    Defines a criterion which is to be evaluated at runtime to influence
    workflow.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-Criterion"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "doc": "Criterion description.",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Unique identifier for the criterion",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Short name for the criterion",
        },
    )
    condition_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ConditionOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Reference to the a ConditionDef",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionEpoch:
    """
    An Epoch element represents the information about the study's Epochs.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-Epoch"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "doc": "Epoch description",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Unique identifier for the epoch",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Short name for the epoch",
        },
    )
    order_number: Optional[int] = field(
        default=None,
        metadata={
            "name": "OrderNumber",
            "type": "Attribute",
            "doc": (
                "Optional order number indicating the order in which the "
                "Epochs occur within in study.\nEither all Epochs within the "
                "containing Structure element must have an OrderNumber, or "
                "none of the Epochs may have an OrderNumber.\nWhen OrderNumber"
                " is used, each Epoch element within its parent Structure "
                "element must have unique OrderNumber value."
            ),
        },
    )
    blinding_schema: Optional[BlindingSchemaType] = field(
        default=None,
        metadata={
            "name": "BlindingSchema",
            "type": "Attribute",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionParameter:
    """
    Study parameter.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-Parameter"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "doc": "Parameter description",
        },
    )
    value: List[Value] = field(
        default_factory=list,
        metadata={
            "name": "Value",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Unique identifier for the parameter",
        },
    )
    term: Optional[str] = field(
        default=None,
        metadata={
            "name": "Term",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Parameter term",
        },
    )
    short_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "ShortName",
            "type": "Attribute",
            "doc": "Parameter short name",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionPathCanFinish:
    """
    The PathCanFinish element allows to specify activities for which it is not
    necessarily an error that the workflow doesn't provide a transition from
    that activity to another activity.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-PathCanFinish"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "doc": (
                "Description of the activities for which the lack of outgoing "
                "transitions from those activities is an intentional part of "
                "the design rather than an error of omission"
            ),
        },
    )
    activity_ref: List[ActivityRef] = field(
        default_factory=list,
        metadata={
            "name": "ActivityRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": (
                "Reference to an activity that is allowed to be an end-of-path"
                " activity"
            ),
        },
    )


@dataclass
class SdmcomplexTypeDefinitionRelativeTimingConstraint:
    """
    A relative timing constraint allows for the scheduling of an activity to be
    relative to another activity anywhere in the study design.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-RelativeTimingConstraint"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Unique identifier for the timing constraint.",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "The name of the timing constraint.",
        },
    )
    predecessor_activity_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "PredecessorActivityOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": (
                "Identifies the predecessor activity that forms the basis for "
                "the relative timing."
            ),
        },
    )
    successor_activity_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "SuccessorActivityOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": (
                "Identifies the successor activity that should be scheduled "
                "relative to the predecessor."
            ),
        },
    )
    type: Timingrelationshiptype = field(
        default=Timingrelationshiptype.FINISH_TO_START,
        metadata={
            "name": "Type",
            "type": "Attribute",
            "doc": (
                "Identifies which ends of the activities the timing should be "
                "applied to."
            ),
        },
    )
    timepoint_relative_target: Optional[str] = field(
        default=None,
        metadata={
            "name": "TimepointRelativeTarget",
            "type": "Attribute",
            "required": True,
            "pattern": r"([ ])?",
            "doc": (
                "The ideal time duration between the activities, given the "
                "relationship type."
            ),
        },
    )
    timepoint_granularity: Optional[Timepointgranularitytype] = field(
        default=None,
        metadata={
            "name": "TimepointGranularity",
            "type": "Attribute",
            "doc": (
                "The granularity that should be applied to the window once the"
                " target time has had the pre and post windows applied."
            ),
        },
    )
    timepoint_pre_window: Optional[str] = field(
        default=None,
        metadata={
            "name": "TimepointPreWindow",
            "type": "Attribute",
            "pattern": r"[^\-].+",
            "doc": (
                "Specifies a window (duration) prior to the target time when "
                "it is allowed for the activity to start."
            ),
        },
    )
    timepoint_post_window: Optional[str] = field(
        default=None,
        metadata={
            "name": "TimepointPostWindow",
            "type": "Attribute",
            "pattern": r"[^\-].+",
            "doc": (
                "Specifies a window (duration) after the target time when it "
                "is allowed for the activity to start."
            ),
        },
    )
    subsequent_scheduling_basis: Subsequentschedulingbasistype = field(
        default=Subsequentschedulingbasistype.PLANNED,
        metadata={
            "name": "SubsequentSchedulingBasis",
            "type": "Attribute",
            "doc": (
                "Signifies to an execution engine whether the successor "
                "activity should occur based on the planned time of the "
                "predecessor or the actual time of the predecessor."
            ),
        },
    )


@dataclass
class SdmcomplexTypeDefinitionSegmentDef:
    """A SegmentDef represents a set of activities.

    Each segment must be referenced by a cell via a SegmentRef within a
    CellDef.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-SegmentDef"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "doc": "Segment description",
        },
    )
    activity_ref: List[ActivityRef] = field(
        default_factory=list,
        metadata={
            "name": "ActivityRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": (
                "List of references to activities which are contained in the "
                "segment."
            ),
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Unique identifier for the segment",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Short name for the segment",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionStudyFinish:
    """
    The StudyFinish element references an activity that is the exit point out
    of the study.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-StudyFinish"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "doc": "Description of the study finish activity",
        },
    )
    activity_ref: Optional[ActivityRef] = field(
        default=None,
        metadata={
            "name": "ActivityRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "required": True,
            "doc": (
                "Reference to an activity that acts as the study finish " "activity"
            ),
        },
    )


@dataclass
class SdmcomplexTypeDefinitionStudyStart:
    """
    The StudyStart references an activity that is the entry point into the
    study.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-StudyStart"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "doc": "Description of the study start activity",
        },
    )
    activity_ref: Optional[ActivityRef] = field(
        default=None,
        metadata={
            "name": "ActivityRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "required": True,
            "doc": ("Reference to an activity acts as the start finish activity"),
        },
    )


@dataclass
class SdmcomplexTypeDefinitionTransitionDefault:
    class Meta:
        name = "SDMcomplexTypeDefinition-TransitionDefault"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "doc": "Description of the default transition",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Unique identifier for the default transition",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Short name or description",
        },
    )
    target_activity_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "TargetActivityOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "OID of the activity to which the default transition leads",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionTransitionDestination:
    """The TransitionDestination element references a single target activity
    and a condition.

    When a TransitionDestination element is encountered, and its
    referenced condition evaluates to true, then the destination is to
    be followed
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-TransitionDestination"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "doc": "Description of the transition destination",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Unique identifier for the TransitionDestination",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Short name or description",
        },
    )
    target_activity_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "TargetActivityOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": (
                "Reference to the activity which is the target activity of the"
                " transition"
            ),
        },
    )
    condition_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ConditionOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": (
                "Reference to the condition under which the destination is to "
                "be followed"
            ),
        },
    )
    order_number: Optional[int] = field(
        default=None,
        metadata={
            "name": "OrderNumber",
            "type": "Attribute",
            "doc": (
                "Optional order number indicating the order in which the "
                "conditions for the transitions must be evaluated.\nEach "
                "TransitionDestination element within its parent Switch "
                "element must have an OrderNumber attribute with a unique "
                "value,\nor none of the TransitionDestination elements within "
                "the parent Switch element must have an OrderNumber "
                "attribute.\nIt is an error if one TransitionDestination "
                "within a Switch element has an OrderNumber attribute, whereas"
                " one or more others don't."
            ),
        },
    )


@dataclass
class SdmcomplexTypeDefinitionTransitionTimingConstraint:
    """
    Allows for a timing constraint to be added to a workflow transition.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-TransitionTimingConstraint"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Unique identifier for the timing constraint.",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "The name of the timing constraint.",
        },
    )
    transition_destination_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "TransitionDestinationOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": (
                "Identifies the transition destination element (in the "
                "workflow section) that this applies to."
            ),
        },
    )
    type: Timingrelationshiptype = field(
        default=Timingrelationshiptype.FINISH_TO_START,
        metadata={
            "name": "Type",
            "type": "Attribute",
            "doc": (
                "Identifies which ends of the activities the timing should be "
                "applied to."
            ),
        },
    )
    timepoint_relative_target: Optional[str] = field(
        default=None,
        metadata={
            "name": "TimepointRelativeTarget",
            "type": "Attribute",
            "required": True,
            "pattern": r"([ ])?",
            "doc": (
                "The ideal time duration between the activities, given the "
                "relationship type."
            ),
        },
    )
    timepoint_granularity: Optional[Timepointgranularitytype] = field(
        default=None,
        metadata={
            "name": "TimepointGranularity",
            "type": "Attribute",
            "doc": (
                "The granularity that should be applied to the window once the"
                " target time has had the pre and post windows applied."
            ),
        },
    )
    timepoint_pre_window: Optional[str] = field(
        default=None,
        metadata={
            "name": "TimepointPreWindow",
            "type": "Attribute",
            "pattern": r"[^\-].+",
            "doc": (
                "Specifies a window (duration) prior to the target time when "
                "it is allowed for the activity to start."
            ),
        },
    )
    timepoint_post_window: Optional[str] = field(
        default=None,
        metadata={
            "name": "TimepointPostWindow",
            "type": "Attribute",
            "pattern": r"[^\-].+",
            "doc": (
                "Specifies a window (duration) after the target time when it "
                "is allowed for the activity to start."
            ),
        },
    )
    subsequent_scheduling_basis: Subsequentschedulingbasistype = field(
        default=Subsequentschedulingbasistype.PLANNED,
        metadata={
            "name": "SubsequentSchedulingBasis",
            "type": "Attribute",
            "doc": (
                "Signifies to an execution engine whether the successor "
                "activity should occur based on the planned time of the "
                "predecessor or the actual time of the predecessor."
            ),
        },
    )


@dataclass
class ReferenceType:
    class Meta:
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    transforms: Optional[Transforms] = field(
        default=None,
        metadata={
            "name": "Transforms",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        },
    )
    digest_method: Optional[DigestMethod] = field(
        default=None,
        metadata={
            "name": "DigestMethod",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "required": True,
        },
    )
    digest_value: Optional[bytes] = field(
        default=None,
        metadata={
            "name": "DigestValue",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "required": True,
            "format": "base64",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Attribute",
        },
    )
    uri: Optional[str] = field(
        default=None,
        metadata={
            "name": "URI",
            "type": "Attribute",
        },
    )
    type: Optional[str] = field(
        default=None,
        metadata={
            "name": "Type",
            "type": "Attribute",
        },
    )


@dataclass
class RetrievalMethodType:
    class Meta:
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    transforms: Optional[Transforms] = field(
        default=None,
        metadata={
            "name": "Transforms",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        },
    )
    uri: Optional[str] = field(
        default=None,
        metadata={
            "name": "URI",
            "type": "Attribute",
        },
    )
    type: Optional[str] = field(
        default=None,
        metadata={
            "name": "Type",
            "type": "Attribute",
        },
    )


@dataclass
class Interventions:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    intervention: List[Intervention] = field(
        default_factory=list,
        metadata={
            "name": "Intervention",
            "type": "Element",
            "min_occurs": 1,
        },
    )


@dataclass
class OutcomeMeasure:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    time_point: List[TimePoint] = field(
        default_factory=list,
        metadata={
            "name": "TimePoint",
            "type": "Element",
            "min_occurs": 1,
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
        },
    )
    type: Optional[OutcomeType] = field(
        default=None,
        metadata={
            "name": "Type",
            "type": "Attribute",
            "required": True,
        },
    )
    is_safety_issue: Optional[YesNoType] = field(
        default=None,
        metadata={
            "name": "IsSafetyIssue",
            "type": "Attribute",
        },
    )


@dataclass
class AdminData(OdmcomplexTypeDefinitionAdminData):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class Annotation(OdmcomplexTypeDefinitionAnnotation):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class AuditRecords(OdmcomplexTypeDefinitionAuditRecords):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class CodeListItem(OdmcomplexTypeDefinitionCodeListItem):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ConditionDef(OdmcomplexTypeDefinitionConditionDef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class FormDef(OdmcomplexTypeDefinitionFormDef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemGroupDef(OdmcomplexTypeDefinitionItemGroupDef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class MeasurementUnit(OdmcomplexTypeDefinitionMeasurementUnit):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class MethodDef(OdmcomplexTypeDefinitionMethodDef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class OdmcomplexTypeDefinitionGlobalVariables:
    class Meta:
        name = "ODMcomplexTypeDefinition-GlobalVariables"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    study_name: Optional[StudyName] = field(
        default=None,
        metadata={
            "name": "StudyName",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    study_description: Optional[str] = field(
        default=None,
        metadata={
            "name": "StudyDescription",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    protocol_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "ProtocolName",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
            "min_length": 1,
        },
    )
    authorities: List[Authorities] = field(
        default_factory=list,
        metadata={
            "name": "Authorities",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
            "sequential": True,
        },
    )
    public_title: List[PublicTitle] = field(
        default_factory=list,
        metadata={
            "name": "PublicTitle",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
            "sequential": True,
        },
    )
    study_detailed_description: List[StudyDetailedDescription] = field(
        default_factory=list,
        metadata={
            "name": "StudyDetailedDescription",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
            "sequential": True,
        },
    )
    registrations: List[Registrations] = field(
        default_factory=list,
        metadata={
            "name": "Registrations",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
            "sequential": True,
        },
    )
    funding_support: List[FundingSupport] = field(
        default_factory=list,
        metadata={
            "name": "FundingSupport",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
            "sequential": True,
        },
    )
    contacts: List[Contacts] = field(
        default_factory=list,
        metadata={
            "name": "Contacts",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
            "sequential": True,
        },
    )


@dataclass
class RangeCheck(OdmcomplexTypeDefinitionRangeCheck):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class Signatures(OdmcomplexTypeDefinitionSignatures):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class StudyEventDef(OdmcomplexTypeDefinitionStudyEventDef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class AbsoluteTimingConstraint(SdmcomplexTypeDefinitionAbsoluteTimingConstraint):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class ActivityDef(SdmcomplexTypeDefinitionActivityDef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class ActivityDuration(SdmcomplexTypeDefinitionActivityDuration):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class Arm(SdmcomplexTypeDefinitionArm):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class CellDef(SdmcomplexTypeDefinitionCellDef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class Criterion(SdmcomplexTypeDefinitionCriterion):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class Epoch(SdmcomplexTypeDefinitionEpoch):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class Parameter(SdmcomplexTypeDefinitionParameter):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class PathCanFinish(SdmcomplexTypeDefinitionPathCanFinish):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class RelativeTimingConstraint(SdmcomplexTypeDefinitionRelativeTimingConstraint):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class SegmentDef(SdmcomplexTypeDefinitionSegmentDef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class StudyFinish(SdmcomplexTypeDefinitionStudyFinish):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class StudyStart(SdmcomplexTypeDefinitionStudyStart):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class TransitionDefault(SdmcomplexTypeDefinitionTransitionDefault):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class TransitionDestination(SdmcomplexTypeDefinitionTransitionDestination):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class TransitionTimingConstraint(SdmcomplexTypeDefinitionTransitionTimingConstraint):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class Reference(ReferenceType):
    class Meta:
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class RetrievalMethod(RetrievalMethodType):
    class Meta:
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class OutcomeMeasures:
    class Meta:
        namespace = "http://www.cdisc.org/ns/ctr/v1.0"

    outcome_measure: List[OutcomeMeasure] = field(
        default_factory=list,
        metadata={
            "name": "OutcomeMeasure",
            "type": "Element",
            "min_occurs": 1,
        },
    )


@dataclass
class GlobalVariables(OdmcomplexTypeDefinitionGlobalVariables):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class OdmcomplexTypeDefinitionAnnotations:
    class Meta:
        name = "ODMcomplexTypeDefinition-Annotations"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    annotation: List[Annotation] = field(
        default_factory=list,
        metadata={
            "name": "Annotation",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionAssociation:
    class Meta:
        name = "ODMcomplexTypeDefinition-Association"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    key_set: List[KeySet] = field(
        default_factory=list,
        metadata={
            "name": "KeySet",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "min_occurs": 1,
            "max_occurs": 2,
        },
    )
    annotation: Optional[Annotation] = field(
        default=None,
        metadata={
            "name": "Annotation",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    study_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "StudyOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    meta_data_version_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MetaDataVersionOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionBasicDefinitions:
    class Meta:
        name = "ODMcomplexTypeDefinition-BasicDefinitions"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    measurement_unit: List[MeasurementUnit] = field(
        default_factory=list,
        metadata={
            "name": "MeasurementUnit",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionCodeList:
    class Meta:
        name = "ODMcomplexTypeDefinition-CodeList"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    code_list_item: List[CodeListItem] = field(
        default_factory=list,
        metadata={
            "name": "CodeListItem",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    external_code_list: Optional[ExternalCodeList] = field(
        default=None,
        metadata={
            "name": "ExternalCodeList",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    enumerated_item: List[EnumeratedItem] = field(
        default_factory=list,
        metadata={
            "name": "EnumeratedItem",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    alias: List[Alias] = field(
        default_factory=list,
        metadata={
            "name": "Alias",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    data_type: Optional[CldataType] = field(
        default=None,
        metadata={
            "name": "DataType",
            "type": "Attribute",
            "required": True,
        },
    )
    sasformat_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "SASFormatName",
            "type": "Attribute",
            "max_length": 8,
            "pattern": r"[A-Za-z_$][A-Za-z0-9_.]*",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemData:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemData"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    audit_record: Optional[AuditRecord] = field(
        default=None,
        metadata={
            "name": "AuditRecord",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    signature: Optional[Signature2] = field(
        default=None,
        metadata={
            "name": "Signature",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    measurement_unit_ref: Optional[MeasurementUnitRef] = field(
        default=None,
        metadata={
            "name": "MeasurementUnitRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    annotation: List[Annotation] = field(
        default_factory=list,
        metadata={
            "name": "Annotation",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )
    is_null: Optional[YesOnly] = field(
        default=None,
        metadata={
            "name": "IsNull",
            "type": "Attribute",
        },
    )
    value: Optional[str] = field(
        default=None,
        metadata={
            "name": "Value",
            "type": "Attribute",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionItemDef:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemDef"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    question: Optional[Question] = field(
        default=None,
        metadata={
            "name": "Question",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    external_question: Optional[ExternalQuestion] = field(
        default=None,
        metadata={
            "name": "ExternalQuestion",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    measurement_unit_ref: List[MeasurementUnitRef] = field(
        default_factory=list,
        metadata={
            "name": "MeasurementUnitRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    range_check: List[RangeCheck] = field(
        default_factory=list,
        metadata={
            "name": "RangeCheck",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    code_list_ref: Optional[CodeListRef] = field(
        default=None,
        metadata={
            "name": "CodeListRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    role: List[str] = field(
        default_factory=list,
        metadata={
            "name": "Role",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    alias: List[Alias] = field(
        default_factory=list,
        metadata={
            "name": "Alias",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    data_type: Optional[DataType] = field(
        default=None,
        metadata={
            "name": "DataType",
            "type": "Attribute",
            "required": True,
        },
    )
    length: Optional[int] = field(
        default=None,
        metadata={
            "name": "Length",
            "type": "Attribute",
        },
    )
    significant_digits: Optional[int] = field(
        default=None,
        metadata={
            "name": "SignificantDigits",
            "type": "Attribute",
        },
    )
    sasfield_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "SASFieldName",
            "type": "Attribute",
            "max_length": 8,
            "pattern": r"[A-Za-z_][A-Za-z0-9_]*",
        },
    )
    sdsvar_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "SDSVarName",
            "type": "Attribute",
            "max_length": 8,
            "pattern": r"[A-Za-z_][A-Za-z0-9_]*",
        },
    )
    origin: Optional[str] = field(
        default=None,
        metadata={
            "name": "Origin",
            "type": "Attribute",
        },
    )
    comment: Optional[str] = field(
        default=None,
        metadata={
            "name": "Comment",
            "type": "Attribute",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionEntryCriteria:
    """
    The EntryCriteria element describes the criteria for allowing a subject to
    enter a structural element.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-EntryCriteria"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    include_inclusion_exclusion_criteria: Optional[
        IncludeInclusionExclusionCriteria
    ] = field(
        default=None,
        metadata={
            "name": "IncludeInclusionExclusionCriteria",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "Include Inclusion/Exclusion criteria in entry criteria",
        },
    )
    criterion: List[Criterion] = field(
        default_factory=list,
        metadata={
            "name": "Criterion",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "Definition of a single entry criterion",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionExclusionCriteria:
    """
    Container element for exclusion criteria.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-ExclusionCriteria"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    criterion: List[Criterion] = field(
        default_factory=list,
        metadata={
            "name": "Criterion",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "List of criterion forming the exclusion criteria",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionExitCriteria:
    """
    The ExitCriteria element describes the criteria for allowing a subject to
    exit a structural element.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-ExitCriteria"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    include_inclusion_exclusion_criteria: Optional[
        IncludeInclusionExclusionCriteria
    ] = field(
        default=None,
        metadata={
            "name": "IncludeInclusionExclusionCriteria",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "Include Inclusion/Exclusion criteria in exit criteria",
        },
    )
    criterion: List[Criterion] = field(
        default_factory=list,
        metadata={
            "name": "Criterion",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "Definition of a single exit criterion",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionInclusionCriteria:
    """
    Container element for inclusion criteria.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-InclusionCriteria"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    criterion: List[Criterion] = field(
        default_factory=list,
        metadata={
            "name": "Criterion",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "List of criterion forming the inclusion criteria",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionStructure:
    """Structure is a container for all SDM structural elements.

    It is placed inside a ODM Protocol element in order to extend on ODM
    file with SDM structural definitions.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-Structure"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    epoch: List[Epoch] = field(
        default_factory=list,
        metadata={
            "name": "Epoch",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "List of epoch definitions",
        },
    )
    arm: List[Arm] = field(
        default_factory=list,
        metadata={
            "name": "Arm",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "List of arm definitions",
        },
    )
    cell_def: List[CellDef] = field(
        default_factory=list,
        metadata={
            "name": "CellDef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "List of cell definitions",
        },
    )
    segment_def: List[SegmentDef] = field(
        default_factory=list,
        metadata={
            "name": "SegmentDef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "List of segment definitions",
        },
    )
    activity_def: List[ActivityDef] = field(
        default_factory=list,
        metadata={
            "name": "ActivityDef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "List of activity definitions",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionSummary:
    """The Summary element provides the ability to define a set of parameters
    to the study design.

    It is placed inside a ODM Protocol element in order to extend on ODM
    file with SDM structural definitions.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-Summary"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "doc": "Description of summary",
        },
    )
    parameter: List[Parameter] = field(
        default_factory=list,
        metadata={
            "name": "Parameter",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "List of parameters",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionSwitch:
    """
    The Switch element defines a set of TransitionDestination elements that are
    to be evaluated in the order they are encountered.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-Switch"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    transition_destination: List[TransitionDestination] = field(
        default_factory=list,
        metadata={
            "name": "TransitionDestination",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "Single target activity and condition for the transition",
        },
    )
    transition_default: Optional[TransitionDefault] = field(
        default=None,
        metadata={
            "name": "TransitionDefault",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "Default transition",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionTiming:
    """
    All timing constructs are grouped beneath the Timing element.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-Timing"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    absolute_timing_constraint: List[AbsoluteTimingConstraint] = field(
        default_factory=list,
        metadata={
            "name": "AbsoluteTimingConstraint",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "Zero or more absolute timing constraints may be defined.",
        },
    )
    relative_timing_constraint: List[RelativeTimingConstraint] = field(
        default_factory=list,
        metadata={
            "name": "RelativeTimingConstraint",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "Zero or more relative timing constraints may be defined.",
        },
    )
    transition_timing_constraint: List[TransitionTimingConstraint] = field(
        default_factory=list,
        metadata={
            "name": "TransitionTimingConstraint",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": ("Zero or more transition timing constraints may be defined."),
        },
    )
    activity_duration: List[ActivityDuration] = field(
        default_factory=list,
        metadata={
            "name": "ActivityDuration",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "Zero or more activity durations may be defined.",
        },
    )


@dataclass
class KeyInfoType:
    class Meta:
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Attribute",
        },
    )
    content: List[object] = field(
        default_factory=list,
        metadata={
            "type": "Wildcard",
            "namespace": "##any",
            "mixed": True,
            "choices": (
                {
                    "name": "KeyName",
                    "type": str,
                    "namespace": "http://www.w3.org/2000/09/xmldsig#",
                },
                {
                    "name": "KeyValue",
                    "type": KeyValue,
                    "namespace": "http://www.w3.org/2000/09/xmldsig#",
                },
                {
                    "name": "RetrievalMethod",
                    "type": RetrievalMethod,
                    "namespace": "http://www.w3.org/2000/09/xmldsig#",
                },
                {
                    "name": "X509Data",
                    "type": X509Data,
                    "namespace": "http://www.w3.org/2000/09/xmldsig#",
                },
                {
                    "name": "PGPData",
                    "type": Pgpdata,
                    "namespace": "http://www.w3.org/2000/09/xmldsig#",
                },
                {
                    "name": "SPKIData",
                    "type": Spkidata,
                    "namespace": "http://www.w3.org/2000/09/xmldsig#",
                },
                {
                    "name": "MgmtData",
                    "type": str,
                    "namespace": "http://www.w3.org/2000/09/xmldsig#",
                },
            ),
        },
    )


@dataclass
class ManifestType:
    class Meta:
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    reference: List[Reference] = field(
        default_factory=list,
        metadata={
            "name": "Reference",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "min_occurs": 1,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Attribute",
        },
    )


@dataclass
class SignedInfoType:
    class Meta:
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    canonicalization_method: Optional[CanonicalizationMethod] = field(
        default=None,
        metadata={
            "name": "CanonicalizationMethod",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "required": True,
        },
    )
    signature_method: Optional[SignatureMethod] = field(
        default=None,
        metadata={
            "name": "SignatureMethod",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "required": True,
        },
    )
    reference: List[Reference] = field(
        default_factory=list,
        metadata={
            "name": "Reference",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "min_occurs": 1,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Attribute",
        },
    )


@dataclass
class Annotations(OdmcomplexTypeDefinitionAnnotations):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class Association(OdmcomplexTypeDefinitionAssociation):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class BasicDefinitions(OdmcomplexTypeDefinitionBasicDefinitions):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class CodeList(OdmcomplexTypeDefinitionCodeList):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemData(OdmcomplexTypeDefinitionItemData):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ItemDef(OdmcomplexTypeDefinitionItemDef):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class EntryCriteria(SdmcomplexTypeDefinitionEntryCriteria):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class ExclusionCriteria(SdmcomplexTypeDefinitionExclusionCriteria):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class ExitCriteria(SdmcomplexTypeDefinitionExitCriteria):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class InclusionCriteria(SdmcomplexTypeDefinitionInclusionCriteria):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class Structure(SdmcomplexTypeDefinitionStructure):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class Summary(SdmcomplexTypeDefinitionSummary):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class Switch(SdmcomplexTypeDefinitionSwitch):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class Timing(SdmcomplexTypeDefinitionTiming):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class KeyInfo(KeyInfoType):
    class Meta:
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class Manifest(ManifestType):
    class Meta:
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class SignedInfo(SignedInfoType):
    class Meta:
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class OdmcomplexTypeDefinitionItemGroupData:
    class Meta:
        name = "ODMcomplexTypeDefinition-ItemGroupData"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    audit_record: Optional[AuditRecord] = field(
        default=None,
        metadata={
            "name": "AuditRecord",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    signature: Optional[Signature2] = field(
        default=None,
        metadata={
            "name": "Signature",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    annotation: List[Annotation] = field(
        default_factory=list,
        metadata={
            "name": "Annotation",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data: List[ItemData] = field(
        default_factory=list,
        metadata={
            "name": "ItemData",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_uri: List[ItemDataUri] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataURI",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_any: List[ItemDataAny] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataAny",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_boolean: List[ItemDataBoolean] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataBoolean",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_string: List[ItemDataString] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataString",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_integer: List[ItemDataInteger] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataInteger",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_float: List[ItemDataFloat] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataFloat",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_double: List[ItemDataDouble] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataDouble",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_date: List[ItemDataDate] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataDate",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_time: List[ItemDataTime] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataTime",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_datetime: List[ItemDataDatetime] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataDatetime",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_hex_binary: List[ItemDataHexBinary] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataHexBinary",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_base64_binary: List[ItemDataBase64Binary] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataBase64Binary",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_hex_float: List[ItemDataHexFloat] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataHexFloat",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_base64_float: List[ItemDataBase64Float] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataBase64Float",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_partial_date: List[ItemDataPartialDate] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataPartialDate",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_partial_time: List[ItemDataPartialTime] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataPartialTime",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_partial_datetime: List[ItemDataPartialDatetime] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataPartialDatetime",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_duration_datetime: List[ItemDataDurationDatetime] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataDurationDatetime",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_interval_datetime: List[ItemDataIntervalDatetime] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataIntervalDatetime",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_incomplete_datetime: List[ItemDataIncompleteDatetime] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataIncompleteDatetime",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_incomplete_date: List[ItemDataIncompleteDate] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataIncompleteDate",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_data_incomplete_time: List[ItemDataIncompleteTime] = field(
        default_factory=list,
        metadata={
            "name": "ItemDataIncompleteTime",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_group_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemGroupOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    item_group_repeat_key: Optional[str] = field(
        default=None,
        metadata={
            "name": "ItemGroupRepeatKey",
            "type": "Attribute",
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionEntryExitCriteria:
    """
    The EntryExitCriteria element describes the criteria for allowing a subject
    to enter or exit a structural element such as an activity, a segment, a
    study event, a cell, an epoch, or the study as a whole.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-EntryExitCriteria"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "doc": "Description of the criteria",
        },
    )
    entry_criteria: Optional[EntryCriteria] = field(
        default=None,
        metadata={
            "name": "EntryCriteria",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "List of entry criteria",
        },
    )
    exit_criteria: Optional[ExitCriteria] = field(
        default=None,
        metadata={
            "name": "ExitCriteria",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "List of exit criteria",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Unique identifier",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Short name or description",
        },
    )
    structural_element_type: Optional[Structuralelementtype] = field(
        default=None,
        metadata={
            "name": "StructuralElementType",
            "type": "Attribute",
            "required": True,
            "doc": (
                "The structural element type on which the set of entry/exit "
                "criteria applies"
            ),
        },
    )
    structural_element_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "StructuralElementOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": (
                "The OID of the structural element on which the set of "
                "entry/exit criteria applies.\nThe referenced structural "
                "element must be of the type given by the "
                "StructuralElementType attribute"
            ),
        },
    )


@dataclass
class SdmcomplexTypeDefinitionInclusionExclusionCriteria:
    """
    Container element for inclusion and exclution criteria.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-InclusionExclusionCriteria"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "doc": "Description of the inclusion/exclusion criteria",
        },
    )
    inclusion_criteria: Optional[InclusionCriteria] = field(
        default=None,
        metadata={
            "name": "InclusionCriteria",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "Inclusion criteria container",
        },
    )
    exclusion_criteria: Optional[ExclusionCriteria] = field(
        default=None,
        metadata={
            "name": "ExclusionCriteria",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "Exclusion criteria container",
        },
    )


@dataclass
class SdmcomplexTypeDefinitionTransition:
    """
    The Transition element specifies the set of potential branches that could
    be followed after completion of a given activity.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-Transition"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "doc": "Description of the transition",
        },
    )
    switch: Optional[Switch] = field(
        default=None,
        metadata={
            "name": "Switch",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "required": True,
            "doc": "Set of transition destinations",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Unique identifier for the transition",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Short name or description for the transition",
        },
    )
    source_activity_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "SourceActivityOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": (
                "Reference to the activity from which the transition " "originates"
            ),
        },
    )


@dataclass
class SdmcomplexTypeDefinitionTrigger:
    """
    The Trigger element describes a divergence to a new path which can be
    started at any point during a study participant's path within the
    referenced structural element.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-Trigger"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "doc": "Description of the trigger",
        },
    )
    switch: Optional[Switch] = field(
        default=None,
        metadata={
            "name": "Switch",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "required": True,
            "doc": "Set of transition destinations for the trigger",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Unique identifier for the trigger",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": "Short name or description",
        },
    )
    condition_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "ConditionOID",
            "type": "Attribute",
            "min_length": 1,
            "doc": "Reference to the condition that activates the trigger",
        },
    )
    structural_element_type: Optional[Structuralelementtype] = field(
        default=None,
        metadata={
            "name": "StructuralElementType",
            "type": "Attribute",
            "required": True,
            "doc": "The structural element type on which the trigger applies",
        },
    )
    structural_element_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "StructuralElementOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
            "doc": (
                "The OID of the structural element on which the trigger "
                "applies.\nThe referenced structural element must be of the "
                "type given by the StructuralElementType attribute"
            ),
        },
    )


@dataclass
class SignatureType:
    class Meta:
        target_namespace = "http://www.w3.org/2000/09/xmldsig#"

    signed_info: Optional[SignedInfo] = field(
        default=None,
        metadata={
            "name": "SignedInfo",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "required": True,
        },
    )
    signature_value: Optional[SignatureValue] = field(
        default=None,
        metadata={
            "name": "SignatureValue",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
            "required": True,
        },
    )
    key_info: Optional[KeyInfo] = field(
        default=None,
        metadata={
            "name": "KeyInfo",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        },
    )
    object_value: List[Object] = field(
        default_factory=list,
        metadata={
            "name": "Object",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Attribute",
        },
    )


@dataclass
class ItemGroupData(OdmcomplexTypeDefinitionItemGroupData):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class EntryExitCriteria(SdmcomplexTypeDefinitionEntryExitCriteria):
    """
    Entry and exit criteria for structural elements.
    """

    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class InclusionExclusionCriteria(SdmcomplexTypeDefinitionInclusionExclusionCriteria):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class Transition(SdmcomplexTypeDefinitionTransition):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class Trigger(SdmcomplexTypeDefinitionTrigger):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class Signature1(SignatureType):
    class Meta:
        name = "Signature"
        namespace = "http://www.w3.org/2000/09/xmldsig#"


@dataclass
class OdmcomplexTypeDefinitionFormData:
    class Meta:
        name = "ODMcomplexTypeDefinition-FormData"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    audit_record: Optional[AuditRecord] = field(
        default=None,
        metadata={
            "name": "AuditRecord",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    signature: Optional[Signature2] = field(
        default=None,
        metadata={
            "name": "Signature",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    archive_layout_ref: Optional[ArchiveLayoutRef] = field(
        default=None,
        metadata={
            "name": "ArchiveLayoutRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    annotation: List[Annotation] = field(
        default_factory=list,
        metadata={
            "name": "Annotation",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_group_data: List[ItemGroupData] = field(
        default_factory=list,
        metadata={
            "name": "ItemGroupData",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    form_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "FormOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    form_repeat_key: Optional[str] = field(
        default=None,
        metadata={
            "name": "FormRepeatKey",
            "type": "Attribute",
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionReferenceData:
    class Meta:
        name = "ODMcomplexTypeDefinition-ReferenceData"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    item_group_data: List[ItemGroupData] = field(
        default_factory=list,
        metadata={
            "name": "ItemGroupData",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    audit_records: List[AuditRecords] = field(
        default_factory=list,
        metadata={
            "name": "AuditRecords",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    signatures: List[Signatures] = field(
        default_factory=list,
        metadata={
            "name": "Signatures",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    annotations: List[Annotations] = field(
        default_factory=list,
        metadata={
            "name": "Annotations",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    study_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "StudyOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    meta_data_version_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MetaDataVersionOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


@dataclass
class SdmcomplexTypeDefinitionWorkflow:
    """
    The Workflow element describes the workflow between activities in the
    study.
    """

    class Meta:
        name = "SDMcomplexTypeDefinition-Workflow"
        target_namespace = "http://www.cdisc.org/ns/studydesign/v1.0"

    study_start: Optional[StudyStart] = field(
        default=None,
        metadata={
            "name": "StudyStart",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "References the Activity that acts as the study start",
        },
    )
    study_finish: Optional[StudyFinish] = field(
        default=None,
        metadata={
            "name": "StudyFinish",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "References the Activity that acts as the study finish",
        },
    )
    path_can_finish: Optional[PathCanFinish] = field(
        default=None,
        metadata={
            "name": "PathCanFinish",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": (
                "Specifies activities that are allowed to be at the end of a "
                "workflow path"
            ),
        },
    )
    entry_exit_criteria: List[EntryExitCriteria] = field(
        default_factory=list,
        metadata={
            "name": "EntryExitCriteria",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "doc": "List of entry- and exit criteria for structural elements",
        },
    )
    transition: List[Transition] = field(
        default_factory=list,
        metadata={
            "name": "Transition",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "sequential": True,
            "doc": "A set of potential branches in the workflow",
        },
    )
    trigger: List[Trigger] = field(
        default_factory=list,
        metadata={
            "name": "Trigger",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "sequential": True,
            "doc": "Trigger for unplanned activities",
        },
    )


@dataclass
class FormData(OdmcomplexTypeDefinitionFormData):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class ReferenceData(OdmcomplexTypeDefinitionReferenceData):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class Workflow(SdmcomplexTypeDefinitionWorkflow):
    class Meta:
        namespace = "http://www.cdisc.org/ns/studydesign/v1.0"


@dataclass
class OdmcomplexTypeDefinitionProtocol:
    class Meta:
        name = "ODMcomplexTypeDefinition-Protocol"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    description: Optional[Description] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    study_event_ref: List[StudyEventRef] = field(
        default_factory=list,
        metadata={
            "name": "StudyEventRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    alias: List[Alias] = field(
        default_factory=list,
        metadata={
            "name": "Alias",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    summary: List[Summary] = field(
        default_factory=list,
        metadata={
            "name": "Summary",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "sequential": True,
        },
    )
    inclusion_exclusion_criteria: List[InclusionExclusionCriteria] = field(
        default_factory=list,
        metadata={
            "name": "InclusionExclusionCriteria",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "sequential": True,
        },
    )
    structure: List[Structure] = field(
        default_factory=list,
        metadata={
            "name": "Structure",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "sequential": True,
        },
    )
    workflow: List[Workflow] = field(
        default_factory=list,
        metadata={
            "name": "Workflow",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "sequential": True,
        },
    )
    timing: List[Timing] = field(
        default_factory=list,
        metadata={
            "name": "Timing",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/studydesign/v1.0",
            "sequential": True,
        },
    )
    protocol_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ProtocolId",
            "type": "Attribute",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
            "required": True,
        },
    )
    protocol_version: Optional[str] = field(
        default=None,
        metadata={
            "name": "ProtocolVersion",
            "type": "Attribute",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
        },
    )
    protocol_version_date: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ProtocolVersionDate",
            "type": "Attribute",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
        },
    )
    protocol_version_change_date: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "ProtocolVersionChangeDate",
            "type": "Attribute",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionStudyEventData:
    class Meta:
        name = "ODMcomplexTypeDefinition-StudyEventData"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    audit_record: Optional[AuditRecord] = field(
        default=None,
        metadata={
            "name": "AuditRecord",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    signature: Optional[Signature2] = field(
        default=None,
        metadata={
            "name": "Signature",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    annotation: List[Annotation] = field(
        default_factory=list,
        metadata={
            "name": "Annotation",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    form_data: List[FormData] = field(
        default_factory=list,
        metadata={
            "name": "FormData",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    study_event_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "StudyEventOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    study_event_repeat_key: Optional[str] = field(
        default=None,
        metadata={
            "name": "StudyEventRepeatKey",
            "type": "Attribute",
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )


@dataclass
class Protocol(OdmcomplexTypeDefinitionProtocol):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class StudyEventData(OdmcomplexTypeDefinitionStudyEventData):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class OdmcomplexTypeDefinitionMetaDataVersion:
    class Meta:
        name = "ODMcomplexTypeDefinition-MetaDataVersion"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    include: Optional[Include] = field(
        default=None,
        metadata={
            "name": "Include",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    protocol: Optional[Protocol] = field(
        default=None,
        metadata={
            "name": "Protocol",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    study_event_def: List[StudyEventDef] = field(
        default_factory=list,
        metadata={
            "name": "StudyEventDef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    form_def: List[FormDef] = field(
        default_factory=list,
        metadata={
            "name": "FormDef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_group_def: List[ItemGroupDef] = field(
        default_factory=list,
        metadata={
            "name": "ItemGroupDef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    item_def: List[ItemDef] = field(
        default_factory=list,
        metadata={
            "name": "ItemDef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    code_list: List[CodeList] = field(
        default_factory=list,
        metadata={
            "name": "CodeList",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    imputation_method: List[ImputationMethod] = field(
        default_factory=list,
        metadata={
            "name": "ImputationMethod",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    presentation: List[Presentation] = field(
        default_factory=list,
        metadata={
            "name": "Presentation",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    condition_def: List[ConditionDef] = field(
        default_factory=list,
        metadata={
            "name": "ConditionDef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    method_def: List[MethodDef] = field(
        default_factory=list,
        metadata={
            "name": "MethodDef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    recruitment: Optional[Recruitment] = field(
        default=None,
        metadata={
            "name": "Recruitment",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
        },
    )
    interventions: Optional[Interventions] = field(
        default=None,
        metadata={
            "name": "Interventions",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
        },
    )
    outcome_measures: Optional[OutcomeMeasures] = field(
        default=None,
        metadata={
            "name": "OutcomeMeasures",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "name": "Name",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Attribute",
        },
    )


@dataclass
class OdmcomplexTypeDefinitionSubjectData:
    class Meta:
        name = "ODMcomplexTypeDefinition-SubjectData"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    audit_record: Optional[AuditRecord] = field(
        default=None,
        metadata={
            "name": "AuditRecord",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    signature: Optional[Signature2] = field(
        default=None,
        metadata={
            "name": "Signature",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    investigator_ref: Optional[InvestigatorRef] = field(
        default=None,
        metadata={
            "name": "InvestigatorRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    site_ref: Optional[SiteRef] = field(
        default=None,
        metadata={
            "name": "SiteRef",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    annotation: List[Annotation] = field(
        default_factory=list,
        metadata={
            "name": "Annotation",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    study_event_data: List[StudyEventData] = field(
        default_factory=list,
        metadata={
            "name": "StudyEventData",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    subject_key: Optional[str] = field(
        default=None,
        metadata={
            "name": "SubjectKey",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    transaction_type: Optional[TransactionType] = field(
        default=None,
        metadata={
            "name": "TransactionType",
            "type": "Attribute",
        },
    )


@dataclass
class MetaDataVersion(OdmcomplexTypeDefinitionMetaDataVersion):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class SubjectData(OdmcomplexTypeDefinitionSubjectData):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class OdmcomplexTypeDefinitionClinicalData:
    class Meta:
        name = "ODMcomplexTypeDefinition-ClinicalData"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    subject_data: List[SubjectData] = field(
        default_factory=list,
        metadata={
            "name": "SubjectData",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    audit_records: List[AuditRecords] = field(
        default_factory=list,
        metadata={
            "name": "AuditRecords",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    signatures: List[Signatures] = field(
        default_factory=list,
        metadata={
            "name": "Signatures",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    annotations: List[Annotations] = field(
        default_factory=list,
        metadata={
            "name": "Annotations",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    study_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "StudyOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    meta_data_version_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "MetaDataVersionOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )


@dataclass
class OdmcomplexTypeDefinitionStudy:
    class Meta:
        name = "ODMcomplexTypeDefinition-Study"
        target_namespace = "http://www.cdisc.org/ns/odm/v1.3"

    global_variables: Optional[GlobalVariables] = field(
        default=None,
        metadata={
            "name": "GlobalVariables",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
            "required": True,
        },
    )
    basic_definitions: Optional[BasicDefinitions] = field(
        default=None,
        metadata={
            "name": "BasicDefinitions",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    meta_data_version: List[MetaDataVersion] = field(
        default_factory=list,
        metadata={
            "name": "MetaDataVersion",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/odm/v1.3",
        },
    )
    study_start_date: List[StudyStartDate] = field(
        default_factory=list,
        metadata={
            "name": "StudyStartDate",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
            "sequential": True,
        },
    )
    study_end_date: List[StudyEndDate] = field(
        default_factory=list,
        metadata={
            "name": "StudyEndDate",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
            "sequential": True,
        },
    )
    study_end_date_primary_outcome: List[StudyEndDatePrimaryOutcome] = field(
        default_factory=list,
        metadata={
            "name": "StudyEndDatePrimaryOutcome",
            "type": "Element",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
            "sequential": True,
        },
    )
    medicinal_product_information: List[MedicinalProductInformation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "sequential": True,
        },
    )
    population_information: List[PopulationInformation] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://eudract.emea.europa.eu/schema/clinical_trial",
            "sequential": True,
        },
    )
    oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "OID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    study_type: Optional[StudyTypeType] = field(
        default=None,
        metadata={
            "name": "StudyType",
            "type": "Attribute",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
            "required": True,
        },
    )
    responsible_party_type: Optional[ResponsiblePartyTypeType] = field(
        default=None,
        metadata={
            "name": "ResponsiblePartyType",
            "type": "Attribute",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
        },
    )


@dataclass
class ClinicalData(OdmcomplexTypeDefinitionClinicalData):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class Study(OdmcomplexTypeDefinitionStudy):
    class Meta:
        namespace = "http://www.cdisc.org/ns/odm/v1.3"


@dataclass
class Odm:
    class Meta:
        name = "ODM"
        namespace = "http://www.cdisc.org/ns/odm/v1.3"

    study: List[Study] = field(
        default_factory=list,
        metadata={
            "name": "Study",
            "type": "Element",
        },
    )
    admin_data: List[AdminData] = field(
        default_factory=list,
        metadata={
            "name": "AdminData",
            "type": "Element",
        },
    )
    reference_data: List[ReferenceData] = field(
        default_factory=list,
        metadata={
            "name": "ReferenceData",
            "type": "Element",
        },
    )
    clinical_data: List[ClinicalData] = field(
        default_factory=list,
        metadata={
            "name": "ClinicalData",
            "type": "Element",
        },
    )
    association: List[Association] = field(
        default_factory=list,
        metadata={
            "name": "Association",
            "type": "Element",
        },
    )
    signature: List[Signature1] = field(
        default_factory=list,
        metadata={
            "name": "Signature",
            "type": "Element",
            "namespace": "http://www.w3.org/2000/09/xmldsig#",
        },
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "name": "Description",
            "type": "Attribute",
        },
    )
    file_type: Optional[FileType] = field(
        default=None,
        metadata={
            "name": "FileType",
            "type": "Attribute",
            "required": True,
        },
    )
    granularity: Optional[Granularity] = field(
        default=None,
        metadata={
            "name": "Granularity",
            "type": "Attribute",
        },
    )
    archival: Optional[YesOnly] = field(
        default=None,
        metadata={
            "name": "Archival",
            "type": "Attribute",
        },
    )
    file_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "FileOID",
            "type": "Attribute",
            "required": True,
            "min_length": 1,
        },
    )
    creation_date_time: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "CreationDateTime",
            "type": "Attribute",
            "required": True,
        },
    )
    prior_file_oid: Optional[str] = field(
        default=None,
        metadata={
            "name": "PriorFileOID",
            "type": "Attribute",
            "min_length": 1,
        },
    )
    as_of_date_time: Optional[XmlDateTime] = field(
        default=None,
        metadata={
            "name": "AsOfDateTime",
            "type": "Attribute",
        },
    )
    odmversion: Optional[Odmversion] = field(
        default=None,
        metadata={
            "name": "ODMVersion",
            "type": "Attribute",
        },
    )
    originator: Optional[str] = field(
        default=None,
        metadata={
            "name": "Originator",
            "type": "Attribute",
        },
    )
    source_system: Optional[str] = field(
        default=None,
        metadata={
            "name": "SourceSystem",
            "type": "Attribute",
        },
    )
    source_system_version: Optional[str] = field(
        default=None,
        metadata={
            "name": "SourceSystemVersion",
            "type": "Attribute",
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "name": "Id",
            "type": "Attribute",
        },
    )
    ctrxmlversion: str = field(
        init=False,
        default="1.0.0",
        metadata={
            "name": "CTRXMLVersion",
            "type": "Attribute",
            "namespace": "http://www.cdisc.org/ns/ctr/v1.0",
            "required": True,
        },
    )
