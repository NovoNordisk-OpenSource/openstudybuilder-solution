const DESCRIPTION_METADATA = 'study_description'
const HIGH_LEVEL_STUDY_DESIGN_METADATA = 'high_level_study_design'
const INTERVENTION_METADATA = 'study_intervention'
const POPULATION_METADATA = 'study_population'

const STOP_RULE_NONE = 'NONE'

const TERM_NOT_APPLICABLE = 'C48660'
const TERM_NOT_APPLICABLE_SUBMVAL = 'NA'
const NULL_FLAVOR_CODELIST_SUBMVAL = 'NULLFLVR'
const TERM_POSITIVE_INF_SUBMVAL = 'PINF'

const STUDY_TIME_UNIT_DAY = 'day'
const STUDY_TIME_UNIT_WEEK = 'week'

const REGISTRY_IDENTIFIERS = [
  'ct_gov_id',
  'eudract_id',
  'universal_trial_number_utn',
  'japanese_trial_registry_id_japic',
  'investigational_new_drug_application_number_ind',
  'eu_trial_number',
  'civ_id_sin_number',
  'national_clinical_trial_number',
  'japanese_trial_registry_number_jrct',
  'national_medical_products_administration_nmpa_number',
  'eudamed_srn_number',
  'investigational_device_exemption_ide_number',
  'eu_pas_number',
]

export default {
  DESCRIPTION_METADATA,
  HIGH_LEVEL_STUDY_DESIGN_METADATA,
  INTERVENTION_METADATA,
  POPULATION_METADATA,
  STOP_RULE_NONE,
  TERM_NOT_APPLICABLE,
  TERM_NOT_APPLICABLE_SUBMVAL,
  TERM_POSITIVE_INF_SUBMVAL,
  NULL_FLAVOR_CODELIST_SUBMVAL,
  STUDY_TIME_UNIT_DAY,
  STUDY_TIME_UNIT_WEEK,
  REGISTRY_IDENTIFIERS,
}
