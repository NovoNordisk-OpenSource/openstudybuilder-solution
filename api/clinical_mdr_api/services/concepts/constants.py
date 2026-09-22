"""Placeholder for constant values."""

COSM0S_RESULT_SCALES_MAP = {
    "NumericFinding": "Quantitative",
    "CategoricFinding": "Ordinal",
}

COSM0S_BASE_ITEM_HREF = (
    "https://ncithesaurus.nci.nih.gov/ncitbrowser/ConceptReport.jsp"
    "?dictionary=NCI_Thesaurus&ns=ncit&code={}"
)

# Conversion map between activity item data types and expected COSMoS
# data types for Data Element Concepts
COSMOS_DEC_TYPES_MAP = {
    "Boolean": "boolean",
    "Date": "date",
    "Date Time": "datetime",
    "Float": "decimal",
    "Integer": "integer",
    "Text": "string",
}
