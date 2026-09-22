// Mirrors TSParameterRequiredLevel / TSParameterCardinality StrEnums in
// api/clinical_mdr_api/domains/controlled_terminologies/ct_term_name.py
const REQUIRED_LEVEL_OPTIONS = [
  'Required',
  'Conditionally Required',
  'If Applicable',
  'Optional',
]

const CARDINALITY_OPTIONS = ['One', 'Many']

export default {
  REQUIRED_LEVEL_OPTIONS,
  CARDINALITY_OPTIONS,
}
