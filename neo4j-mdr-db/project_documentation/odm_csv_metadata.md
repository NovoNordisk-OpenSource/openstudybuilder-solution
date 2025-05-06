# Description of the csv files

## odm_forms.csv:

The csv form is collecting the following information:

| Header value | Definition |
| ------------ | ---------- |
| library      | Please provide here the reference of the library. By default we have the Sponsor one but you may use the Global one |
| oid          | Provide here a Unique Object Identifier like for example F.DM for the Informed Consent & Demography form |
| name         | Please report here the name of the form as written in the dark bleue cell on the first page of the Form (example: Informed Consent and Demography) |
| prompt       | Please provide a short value that could be used instead of the name or the description |
| repeating    | Is this form repeating or not - Reply with a Yes or No. In the Novo Nordisk form this info is at the right end of the dark bleue cell on the first page, on the same level as the title of the form |
| language     | Provide by default the ENG value here. To have more translation, please add new row with the same OID but with additional language like FRA for French |
| description  | Please provide here the description of the Form. You can take here the information from the Design Notes or at the end of the form or even from the Guidance documentation. For multilingual, please provide additional lines |
| instruction  | Please provide here also every instruction that could help the end user in filling this Form |

## odm_itemgroups.csv:

An Item Group describes a type of item group (under it we have a related set of items) that can occur within a study.
The csv item group is collecting the following information:

| Header value | Definition |
| ------------ | ---------- |
| library      | Please provide here the reference of the library. By default we have the Sponsor one but you may use the Global one |
| oid          | Provide here a Unique Object Identifier like for example F.DM for the Informed Consent & Demography form |
| name         | Please report here the name of the form as written in the dark bleue cell on the first page of the Form (example: Informed Consent and Demography) |
| prompt       | Please provide a short value that could be used instead of the name or the description |
| repeating    | The Repeating flag indicates that this type of item group can occur repeatedly within the containing form - Reply with a Yes or No. In the Novo Nordisk form this info is not available |
| isreferencedata | If IsReferenceData is Yes, this type of item group can occur only within a ReferenceData element. If IsReferenceData is No, this type of item group can occur only within a ClinicalData element. The default for this attribute is No |
| sasdatasetname | Provide here the 'old' dataset name as DEMO for example |
| domain | The domain should refer to the SDTM domain - Please refer to the Annotated CRF and provide the SDTM Domain (or dataset name) |
| origin | Can be PROTOCOL, CRF, EXTERNAL SOURCE... |
| purpose | Refer to the SDTM Purpose information |
| comment | Provide a comment as specified in the SDTM Model |
| language     | Provide by default the ENG value here. To have more translation, please add new row with the same OID but with additional language like FRA for French |
| description  | Please provide here the description of the Item Group. For multilingual, please provide additional lines |
| instruction  | Please provide here also every instruction that could help the end user in filling this Item Group |

## odm_items.csv:

An Item describes a type of item group (under it we have a related set of items) that can occur within a study.
The csv item group is collecting the following information:

| Header value  | Definition |
| ------------- | ---------- |
| library       | Please provide here the reference of the library. By default we have the Sponsor one but you may use the Global one |
| oid           | Provide here a Unique Object Identifier like for example F.DM for the Informed Consent & Demography form |
| name          | Please report here the name of the form as written in the dark bleue cell on the first page of the Form (example: Informed Consent and Demography) |
| prompt        | Please provide a short value that could be used instead of the name or the description |
| datatype      | text or integer or float or date or time or datetime or string or boolean or double or hexBinary or base64Binary or hexFloat or base64Float or partialDate or partialTime or partialDatetime or durationDatetime or intervalDatetime or incompleteDatetime or incompleteDate or incompleteTime or URI |
| length        | If DataType=integer, Length=N is a requirement that the receiving system be able to process. If DataType=text, Length=integer is a requirement |
| significantdigits | If DataType=float, Length=N and SignificantDigits=S is a requirement that the receiving system be able to process |
| codelist      | Number of digit for Datatype=float |
| term          | If applicable, specify the dedicated conceptID for each term if we are looking for a subset |
| unit          | Please provide here the uid of the unit to be used by the Item. Only numeric items can have measurement unit |
| sasfieldname  | Please provide here a SAS reference as it may be useful for SAS system to work with |
| sdsvarname    | SDSVarName is an optional attribute which can be used to tag the Item with a business meaning refering to the SDTMIG variable ID |
| origin        | Can be PROTOCOL, CRF, EXTERNAL SOURCE... |
| purpose       | Refer to the SDTM Purpose information |
| comment       | Provide a comment as specified in the SDTM Model |
| language      | Provide by default the ENG value here. To have more translation, please add new row with the same OID but with additional language like FRA for French |
| description   | Please provide here the description of the Item. For multilingual, please provide additional lines |
| instruction   | Please provide here also every instruction that could help the end user in filling this Item |

