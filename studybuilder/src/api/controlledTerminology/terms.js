import repository from '../repository'

const resource = 'ct/terms'

const knownCodelists = {
  studyType: { attribute: 'codelist_uid', value: 'C99077' },
  trialIntentType: { attribute: 'codelist_uid', value: 'C66736' },
  trialType: { attribute: 'codelist_uid', value: 'C66739' },
  trialPhase: { attribute: 'codelist_uid', value: 'C66737' },
  interventionTypes: { attribute: 'codelist_uid', value: 'C99078' },
  therapeuticArea: { attribute: 'codelist_name', value: 'Therapeutic area' },
  interventionType: { attribute: 'codelist_uid', value: 'C99078' },
  controlType: { attribute: 'codelist_uid', value: 'C66785' },
  interventionModel: { attribute: 'codelist_uid', value: 'C99076' },
  trialBlindingSchema: { attribute: 'codelist_uid', value: 'C66735' },
  nullValues: { attribute: 'codelist_name', value: 'Null Flavor' },
  ageUnits: { attribute: 'codelist_uid', value: 'C66781' },
  objectiveLevels: { attribute: 'codelist_name', value: 'Objective Level' },
  units: { attribute: 'codelist_uid', value: 'C71620' },
  visitTypes: { attribute: 'codelist_name', value: 'VisitType' },
  timepointReferences: {
    attribute: 'codelist_name',
    value: 'Time Point Reference',
  },
  epochs: { attribute: 'codelist_uid', value: 'C99079' },
  epochTypes: { attribute: 'codelist_name', value: 'Epoch Type' },
  epochSubTypes: { attribute: 'codelist_name', value: 'Epoch Sub Type' },
  sexOfParticipants: { attribute: 'codelist_uid', value: 'C66732' },
  objectiveCategories: {
    attribute: 'codelist_name',
    value: 'Objective Category',
  },
  endpointLevels: { attribute: 'codelist_name', value: 'Endpoint Level' },
  endpointSubLevels: {
    attribute: 'codelist_name',
    value: 'Endpoint Sub Level',
  },
  endpointCategories: {
    attribute: 'codelist_name',
    value: 'Endpoint Category',
  },
  endpointSubCategories: {
    attribute: 'codelist_name',
    value: 'Endpoint Sub Category',
  },
  criteriaTypes: { attribute: 'codelist_name', value: 'Criteria Type' },
  criteriaCategories: {
    attribute: 'codelist_name',
    value: 'Criteria Category',
  },
  criteriaSubCategories: {
    attribute: 'codelist_name',
    value: 'Criteria Sub Category',
  },
  typeOfTreatment: { attribute: 'codelist_name', value: 'Type of Treatment' },
  routeOfAdministration: { attribute: 'codelist_uid', value: 'C66729' },
  dosageForm: { attribute: 'codelist_uid', value: 'C66726' },
  flowchartGroups: { attribute: 'codelist_name', value: 'Flowchart Group' },
  contactModes: { attribute: 'codelist_name', value: 'Visit Contact Mode' },
  epochAllocations: { attribute: 'codelist_name', value: 'Epoch Allocation' },
  armTypes: { attribute: 'codelist_name', value: 'Arm Type' },
  unitDimensions: { attribute: 'codelist_name', value: 'Unit Dimension' },
  unitSubsets: { attribute: 'codelist_name', value: 'Unit Subset' },
  elementSubTypes: { attribute: 'codelist_name', value: 'Element Sub Type' },
  elementTypes: { attribute: 'codelist_name', value: 'Element Type' },
  language: { attribute: 'codelist_name', value: 'Language' },
  sdtmDomainAbbreviation: { attribute: 'codelist_uid', value: 'C66734' },
  sendDomainAbbreviation: { attribute: 'codelist_uid', value: 'C111113' },
  originType: { attribute: 'codelist_uid', value: 'C170449' },
  dataType: { attribute: 'codelist_name', value: 'Data type' },
  frequency: { attribute: 'codelist_uid', value: 'C71113' },
  deliveryDevice: { attribute: 'codelist_name', value: 'Delivery Device' },
  dispensedIn: { attribute: 'codelist_name', value: 'Compound Dispensed In' },
  adverseEvents: { attribute: 'codelist_uid', value: 'C66734' },
  diseaseMilestoneTypes: {
    attribute: 'codelist_name',
    value: 'Disease Milestone Type',
  },
  footnoteTypes: { attribute: 'codelist_name', value: 'Footnote Type' },
  footnoteCategories: {
    attribute: 'codelist_name',
    value: 'Footnote Category',
  },
  footnoteSubCategories: {
    attribute: 'codelist_name',
    value: 'Footnote Sub Category',
  },
  repeatingVisitFrequency: {
    attribute: 'codelist_name',
    value: 'Repeating Visit Frequency',
  },
}

export default {
  getAll(params) {
    return repository.get(resource, { params })
  },
  getByCodelist(name, options) {
    const codelist = knownCodelists[name]
    if (codelist !== undefined) {
      const params = { page_size: options?.all ? 0 : 100 }
      if (!options?.unSorted) {
        params.sort_by = JSON.stringify({ 'name.sponsor_preferred_name': true })
      }
      params[codelist.attribute] = codelist.value
      return repository.get(`${resource}`, { params })
    }
    throw new Error(`Provided codelist (${name}) is unknown`)
  },
  getNamesByCodelist(name, params) {
    const codelist = knownCodelists[name]
    if (codelist !== undefined) {
      if (!params) {
        params = { page_size: 100 }
      }
      params[codelist.attribute] = codelist.value
      return repository.get(`${resource}/names`, { params })
    }
    throw new Error(`Provided codelist (${name}) is unknown`)
  },
  getAttributesByCodelist(name) {
    const codelist = knownCodelists[name]
    if (codelist !== undefined) {
      const params = { page_size: 100 }
      params[codelist.attribute] = codelist.value
      return repository.get(`${resource}/attributes`, { params })
    }
    throw new Error(`Provided codelist (${name}) is unknown`)
  },
  getTermByUid(termUid) {
    return repository.get(`${resource}/${termUid}/names`)
  },
  getTermsByCodelistUid(params) {
    return repository.get(`${resource}`, { params })
  },
}
