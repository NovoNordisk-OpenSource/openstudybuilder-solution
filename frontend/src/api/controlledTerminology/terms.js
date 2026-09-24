import repository from '../repository'

const resource = 'ct/terms'

const knownCodelists = {
  studyType: { attribute: 'codelist_uid', value: 'C99077' },
  trialIntentType: { attribute: 'codelist_uid', value: 'C66736' },
  trialType: { attribute: 'codelist_uid', value: 'C66739' },
  trialPhase: { attribute: 'codelist_uid', value: 'C66737' },
  interventionTypes: { attribute: 'codelist_uid', value: 'C99078' },
  therapeuticArea: {
    attribute: 'codelist_submission_value',
    value: 'THERAREA',
  },
  interventionType: { attribute: 'codelist_uid', value: 'C99078' },
  controlType: { attribute: 'codelist_uid', value: 'C66785' },
  interventionModel: { attribute: 'codelist_uid', value: 'C99076' },
  trialBlindingSchema: { attribute: 'codelist_uid', value: 'C66735' },
  nullValues: { attribute: 'codelist_submission_value', value: 'NULLFLVR' },
  ageUnits: { attribute: 'codelist_uid', value: 'C66781' },
  objectiveLevels: {
    attribute: 'codelist_submission_value',
    value: 'OBJTLEVL',
  },
  units: { attribute: 'codelist_uid', value: 'C71620' },
  visitTypes: { attribute: 'codelist_submission_value', value: 'TIMELB' },
  timepointReferences: {
    attribute: 'codelist_submission_value',
    value: 'TIMEREF',
  },
  epochs: { attribute: 'codelist_uid', value: 'C99079' },
  epochTypes: { attribute: 'codelist_submission_value', value: 'EPOCHTP' },
  epochSubTypes: { attribute: 'codelist_submission_value', value: 'EPOCHSTP' },
  sexOfParticipants: { attribute: 'codelist_uid', value: 'C66732' },
  objectiveCategories: {
    attribute: 'codelist_submission_value',
    value: 'OBJTCAT',
  },
  endpointLevels: { attribute: 'codelist_submission_value', value: 'ENDPLEVL' },
  endpointSubLevels: {
    attribute: 'codelist_submission_value',
    value: 'ENDPSBLV',
  },
  endpointCategories: {
    attribute: 'codelist_submission_value',
    value: 'ENDPCAT',
  },
  endpointSubCategories: {
    attribute: 'codelist_submission_value',
    value: 'ENDPSCAT',
  },
  criteriaTypes: { attribute: 'codelist_submission_value', value: 'CRITRTP' },
  criteriaCategories: {
    attribute: 'codelist_submission_value',
    value: 'CRITCAT',
  },
  criteriaSubCategories: {
    attribute: 'codelist_submission_value',
    value: 'CRITSCAT',
  },
  typeOfTreatment: { attribute: 'codelist_submission_value', value: 'TPOFTRT' },
  routeOfAdministration: { attribute: 'codelist_uid', value: 'C66729' },
  dosageForm: { attribute: 'codelist_uid', value: 'C66726' },
  flowchartGroups: {
    attribute: 'codelist_submission_value',
    value: 'FLWCRTGRP',
  },
  contactModes: { attribute: 'codelist_submission_value', value: 'VISCNTMD' },
  epochAllocations: {
    attribute: 'codelist_submission_value',
    value: 'EPCHALLC',
  },
  armTypes: { attribute: 'codelist_submission_value', value: 'ARMTTP' },
  unitDimensions: { attribute: 'codelist_submission_value', value: 'UNITDIM' },
  unitSubsets: { attribute: 'codelist_submission_value', value: 'UNITSUBS' },
  elementSubTypes: { attribute: 'codelist_submission_value', value: 'ELEMSTP' },
  elementTypes: { attribute: 'codelist_submission_value', value: 'ELEMTP' },
  language: { attribute: 'codelist_submission_value', value: 'LANGUAGE' },
  sdtmDomainAbbreviation: { attribute: 'codelist_uid', value: 'C66734' },
  sendDomainAbbreviation: { attribute: 'codelist_uid', value: 'C111113' },
  originType: { attribute: 'codelist_uid', value: 'C170449' },
  dataType: { attribute: 'codelist_submission_value', value: 'DATATYPE' },
  semanticDataType: {
    attribute: 'codelist_submission_value',
    value: 'SEMTCDT',
  },
  role: { attribute: 'codelist_name', value: 'Role' },
  codmdt: { attribute: 'codelist_submission_value', value: 'CODMDT' },
  originSource: { attribute: 'codelist_uid', value: 'C170450' },
  frequency: { attribute: 'codelist_uid', value: 'C71113' },
  deliveryDevice: { attribute: 'codelist_submission_value', value: 'DLVRDVC' },
  dispensedIn: { attribute: 'codelist_submission_value', value: 'COMPDISP' },
  adverseEvents: { attribute: 'codelist_uid', value: 'C66734' },
  diseaseMilestoneTypes: {
    attribute: 'codelist_submission_value',
    value: 'MIDSTYPE',
  },
  footnoteTypes: { attribute: 'codelist_submission_value', value: 'FTNTTP' },
  repeatingVisitFrequency: {
    attribute: 'codelist_submission_value',
    value: 'REPEATING_VISIT_FREQUENCY',
  },
  dataSupplierType: {
    attribute: 'codelist_submission_value',
    value: 'DATA_SUPPLIER_TYPE',
  },
  findingCategoryDefinition: {
    attribute: 'codelist_submission_value',
    value: 'FINDCAT',
  },
  findingSubCategoryDefinition: {
    attribute: 'codelist_submission_value',
    value: 'FINDSCAT',
  },
  eventCategoryDefinition: {
    attribute: 'codelist_submission_value',
    value: 'EVNTCAT',
  },
  eventSubCategoryDefinition: {
    attribute: 'codelist_submission_value',
    value: 'EVNTSCAT',
  },
  interventionCategoryDefinition: {
    attribute: 'codelist_submission_value',
    value: 'INTVCAT',
  },
  interventionSubCategoryDefinition: {
    attribute: 'codelist_submission_value',
    value: 'INTVSCAT',
  },
  developmentStageCodes: {
    attribute: 'codelist_submission_value',
    value: 'DEVELOPMENT_STAGE',
  },
  reasonForLock: {
    attribute: 'codelist_submission_value',
    value: 'RSNFL',
  },
  reasonForUnlock: {
    attribute: 'codelist_submission_value',
    value: 'RSNFUL',
  },
}

export default {
  getKnownCodelist(name) {
    return knownCodelists[name]
  },
  getAll(params) {
    return repository.get(resource, { params })
  },
  getTermsByCodelist(name, params) {
    const codelist = knownCodelists[name]
    if (codelist !== undefined) {
      const query_params = { page_size: params?.all ? 0 : 100, ...params }
      delete query_params.all
      query_params['sort_by'] = JSON.stringify({ sponsor_preferred_name: true })
      query_params[codelist.attribute] = codelist.value
      return repository.get(`/ct/codelists/terms`, {
        params: query_params,
      })
    }
    throw new Error(`Provided codelist (${name}) is unknown`)
  },
  getTermByUid(termUid) {
    return repository.get(`${resource}/${termUid}/names`)
  },
  getTermsByCodelistUid(params) {
    return repository.get(`${resource}`, { params })
  },
  updateAttributes(term_uid, data) {
    return repository.patch(`${resource}/${term_uid}/attributes`, data)
  },
  updateTrialSummaryParameters(term_uid, data) {
    return repository.patch(
      `${resource}/${term_uid}/names/trial-summary-parameters`,
      data
    )
  },
}
