const categoryActivityItemClasses = {
  CategoricFindings: 'finding_category',
  NumericFindings: 'finding_category',
  TextualFindings: 'finding_category',
  Events: 'event_category',
  Interventions: 'intervention_category',
}

const subcategoryActivityItemClasses = {
  CategoricFindings: 'finding_subcategory',
  NumericFindings: 'finding_subcategory',
  TextualFindings: 'finding_subcategory',
  Events: 'event_subcategory',
  Interventions: 'intervention_subcategory',
}

const categoryCodelistSubmissionValues = {
  CategoricFindings: 'FINDCAT',
  NumericFindings: 'FINDCAT',
  TextualFindings: 'FINDCAT',
  Events: 'EVNTCAT',
  Interventions: 'INTVCAT',
}

const subcategoryCodelistSubmissionValues = {
  CategoricFindings: 'FINDSCAT',
  NumericFindings: 'FINDSCAT',
  TextualFindings: 'FINDSCAT',
  Events: 'EVNTSCAT',
  Interventions: 'INTVSCAT',
}

const sdtmDomainAbbreviationCodelistUid = 'C66734'

export default {
  categoryActivityItemClasses,
  subcategoryActivityItemClasses,
  categoryCodelistSubmissionValues,
  subcategoryCodelistSubmissionValues,
  sdtmDomainAbbreviationCodelistUid,
}
