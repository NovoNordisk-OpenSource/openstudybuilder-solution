import constants from '@/constants/study'
import repository from './repository'

const resource = 'studies'

export default {
  get(options) {
    const params = {
      ...options,
    }
    return repository.get(
      `${resource}?include_sections=${constants.DESCRIPTION_METADATA}`,
      { params }
    )
  },
  projects_all() {
    const params = {
      page_size: 0,
      sort_by: JSON.stringify({ project_number: true }),
    }
    const url = '/projects'
    return repository.get(url, { params })
  },
  getAll() {
    const url = `/${resource}`
    return repository.get(url, { params: { page_size: 0 } })
  },
  getStudy(studyUid, ignoreErrors) {
    const params = {
      ignoreErrors: ignoreErrors,
    }
    return repository.get(`${resource}/${studyUid}`, { params })
  },
  getStudySnapshotHistory(studyUid, params) {
    return repository.get(`${resource}/${studyUid}/snapshot-history`, {
      params,
    })
  },
  cloneStudy(studyUid, data) {
    return repository.post(`${resource}/${studyUid}/clone`, data)
  },
  deleteStudy(studyUid) {
    return repository.delete(`${resource}/${studyUid}`)
  },
  releaseStudy(studyUid, data) {
    return repository.post(`${resource}/${studyUid}/release`, data)
  },
  lockStudy(studyUid, data) {
    return repository.post(`${resource}/${studyUid}/locks`, data)
  },
  unlockStudy(studyUid) {
    return repository.delete(`${resource}/${studyUid}/locks`)
  },
  updateStudy(studyUid, data) {
    return repository.patch(`${resource}/${studyUid}`, data)
  },
  reorderStudySubpart(studyUid, data) {
    return repository.patch(`${resource}/${studyUid}/order`, data)
  },
  getStudyAuditTrail(studyUid, params) {
    return repository.get(`${resource}/${studyUid}/audit-trail`, { params })
  },
  getStudyPreferredTimeUnit(studyUid) {
    return repository.get(`${resource}/${studyUid}/time-units`, {
      ignoreErrors: true,
    })
  },
  updateStudyPreferredTimeUnit(studyUid, data, protocolSoa) {
    return repository.patch(
      `${resource}/${studyUid}/time-units?for_protocol_soa=${Boolean(protocolSoa)}`,
      data
    )
  },
  getSoAPreferredTimeUnit(studyUid) {
    const params = {
      ignoreErrors: true,
      for_protocol_soa: true,
    }
    return repository.get(`${resource}/${studyUid}/time-units`, { params })
  },
  getSoAPreferences(studyUid) {
    return repository.get(`${resource}/${studyUid}/soa-preferences`)
  },
  updateSoaPreferences(studyUid, data) {
    return repository.patch(`${resource}/${studyUid}/soa-preferences`, data)
  },
  getStudyProtocolTitle(studyUid) {
    return repository.get(`${resource}/${studyUid}/protocol-title`)
  },
  getStudyDescriptionMetadata(studyUid) {
    return repository.get(
      `${resource}/${studyUid}?include_sections=${constants.DESCRIPTION_METADATA}`
    )
  },
  getHighLevelStudyDesignMetadata(studyUid) {
    const includeSections = [constants.HIGH_LEVEL_STUDY_DESIGN_METADATA]
    return repository.get(
      `${resource}/${studyUid}?include_sections=${includeSections}`
    )
  },
  getStudyPopulationMetadata(studyUid) {
    const includeSections = [constants.POPULATION_METADATA]
    return repository.get(
      `${resource}/${studyUid}?include_sections=${includeSections}`
    )
  },
  getStudyInterventionMetadata(studyUid) {
    const includeSections = [constants.INTERVENTION_METADATA]
    return repository.get(
      `${resource}/${studyUid}?include_sections=${includeSections}`
    )
  },
  getStudyFieldsAuditTrail(studyUid, section) {
    const includeSections = []
    if (section !== 'identification_metadata') {
      includeSections.push(section)
      return repository.get(
        `${resource}/${studyUid}/fields-audit-trail?include_sections=${includeSections}&exclude_sections=identification_metadata`
      )
    }
    return repository.get(`${resource}/${studyUid}/fields-audit-trail`)
  },
  getAllStudyObjectives(params) {
    return repository.get('study-objectives', { params })
  },
  getStudyObjectives(studyUid, params) {
    return repository.get(`studies/${studyUid}/study-objectives`, { params })
  },
  getStudyObjective(studyUid, studyObjectiveUid) {
    return repository.get(
      `studies/${studyUid}/study-objectives/${studyObjectiveUid}`
    )
  },
  getStudyObjectivesAuditTrail(studyUid) {
    return repository.get(`studies/${studyUid}/study-objectives/audit-trail`)
  },
  getStudyObjectiveAuditTrail(studyUid, studyObjectiveUid) {
    return repository.get(
      `studies/${studyUid}/study-objectives/${studyObjectiveUid}/audit-trail`
    )
  },
  getStudyObjectivesHtml(studyUid) {
    return repository.get(`studies/${studyUid}/study-objectives.html`)
  },
  getStudyObjectivesDocx(studyUid) {
    return repository.get(`studies/${studyUid}/study-objectives.docx`, {
      responseType: 'arraybuffer',
    })
  },
  selectStudyObjective(studyUid, objectiveUid, objectiveLevelUid) {
    const data = {
      objective_uid: objectiveUid,
      objective_level_uid: objectiveLevelUid,
    }
    return repository.post(`studies/${studyUid}/study-objectives`, data)
  },
  getStudyObjectivePreview(studyUid, data) {
    return repository.post(`studies/${studyUid}/study-objectives/preview`, data)
  },
  createStudyObjective(studyUid, data) {
    return repository.post(
      `studies/${studyUid}/study-objectives?create_objective=true`,
      data
    )
  },
  batchCreateStudyObjectives(studyUid, data) {
    return repository.post(
      `studies/${studyUid}/study-objectives/batch-select`,
      data
    )
  },
  updateStudyObjective(studyUid, studyObjectiveUid, data) {
    return repository.patch(
      `studies/${studyUid}/study-objectives/${studyObjectiveUid}`,
      data
    )
  },
  updateStudyObjectiveLatestVersion(studyUid, studyObjectiveUid) {
    return repository.post(
      `studies/${studyUid}/study-objectives/${studyObjectiveUid}/sync-latest-version`
    )
  },
  updateStudyObjectiveOrder(studyUid, studyObjectiveUid, order) {
    const data = { new_order: order }
    return repository.patch(
      `studies/${studyUid}/study-objectives/${studyObjectiveUid}/order`,
      data
    )
  },
  deleteStudyObjective(studyUid, studyObjectiveUid) {
    return repository.delete(
      `studies/${studyUid}/study-objectives/${studyObjectiveUid}`
    )
  },
  getAllStudyEndpoints(params) {
    return repository.get('study-endpoints', { params })
  },
  getStudyEndpoints(studyUid, params) {
    return repository.get(`studies/${studyUid}/study-endpoints`, { params })
  },
  getStudyEndpoint(studyUid, studyEndpointUid) {
    return repository.get(
      `studies/${studyUid}/study-endpoints/${studyEndpointUid}`
    )
  },
  getStudyEndpointsByObjective(studyUid, objectiveUid) {
    const params = {
      filters: {
        'studyObjective.objective.uid': {
          v: [objectiveUid],
        },
      },
    }
    return repository.get('study-endpoints', { params })
  },
  getStudyEndpointsAuditTrail(studyUid) {
    return repository.get(`studies/${studyUid}/study-endpoints/audit-trail`)
  },
  getStudyEndpointAuditTrail(studyUid, studyEndpointUid) {
    return repository.get(
      `studies/${studyUid}/study-endpoints/${studyEndpointUid}/audit-trail`
    )
  },
  getStudyEndpointPreview(studyUid, data) {
    return repository.post(`studies/${studyUid}/study-endpoints/preview`, data)
  },
  createStudyEndpoint(studyUid, data) {
    return repository.post(
      `studies/${studyUid}/study-endpoints?create_endpoint=true`,
      data
    )
  },
  batchCreateStudyEndpoints(studyUid, data) {
    return repository.post(
      `studies/${studyUid}/study-endpoints/batch-select`,
      data
    )
  },
  selectStudyEndpoint(studyUid, data) {
    return repository.post(`studies/${studyUid}/study-endpoints`, data)
  },
  updateStudyEndpoint(studyUid, studyEndpointUid, data) {
    return repository.patch(
      `studies/${studyUid}/study-endpoints/${studyEndpointUid}`,
      data
    )
  },
  updateStudyEndpointEndpointLatestVersion(studyUid, studyEndpointUid) {
    return repository.post(
      `studies/${studyUid}/study-endpoints/${studyEndpointUid}/sync-latest-endpoint-version`
    )
  },
  updateStudyEndpointTimeframeLatestVersion(studyUid, studyEndpointUid) {
    return repository.post(
      `studies/${studyUid}/study-endpoints/${studyEndpointUid}/sync-latest-timeframe-version`
    )
  },
  updateStudyEndpointOrder(studyUid, studyEndpointUid, order) {
    const data = { new_order: order }
    return repository.patch(
      `studies/${studyUid}/study-endpoints/${studyEndpointUid}/order`,
      data
    )
  },
  deleteStudyEndpoint(studyUid, studyEndpointUid) {
    return repository.delete(
      `studies/${studyUid}/study-endpoints/${studyEndpointUid}`
    )
  },
  updateStudyObjectiveAcceptVersion(studyUid, studyObjectiveUid) {
    return repository.post(
      `studies/${studyUid}/study-objectives/${studyObjectiveUid}/accept-version`
    )
  },
  updateStudyEndpointAcceptVersion(studyUid, studyEndpointUid) {
    return repository.post(
      `studies/${studyUid}/study-endpoints/${studyEndpointUid}/accept-version`
    )
  },
  getStudyCompounds(studyUid, params) {
    return repository.get(`studies/${studyUid}/study-compounds`, { params })
  },
  getStudyCompound(studyUid, studyCompoundUid) {
    return repository.get(
      `studies/${studyUid}/study-compounds/${studyCompoundUid}`
    )
  },
  getStudyCompoundsAuditTrail(studyUid) {
    return repository.get(`studies/${studyUid}/study-compounds/audit-trail`)
  },
  getStudyCompoundAuditTrail(studyUid, studyCompoundUid) {
    return repository.get(
      `studies/${studyUid}/study-compounds/${studyCompoundUid}/audit-trail`
    )
  },
  updateStudyCompound(studyUid, studyCompoundUid, data) {
    return repository.patch(
      `studies/${studyUid}/study-compounds/${studyCompoundUid}`,
      data
    )
  },
  selectStudyCompound(studyUid, data) {
    return repository.post(`studies/${studyUid}/study-compounds`, data)
  },
  deleteStudyCompound(studyUid, studyCompoundUid) {
    return repository.delete(
      `studies/${studyUid}/study-compounds/${studyCompoundUid}`
    )
  },
  getStudyCompoundDosings(studyUid) {
    const params = {
      page_size: 0,
    }
    return repository.get(`studies/${studyUid}/study-compound-dosings`, {
      params,
    })
  },
  getStudyCompoundDosingsAuditTrail(studyUid) {
    return repository.get(
      `studies/${studyUid}/study-compound-dosings/audit-trail`
    )
  },
  getStudyCompoundDosingAuditTrail(studyUid, studyCompoundDosingUid) {
    return repository.get(
      `studies/${studyUid}/study-compound-dosings/${studyCompoundDosingUid}/audit-trail`
    )
  },
  updateStudyCompoundDosing(studyUid, studyCompoundDosingUid, data) {
    return repository.patch(
      `studies/${studyUid}/study-compound-dosings/${studyCompoundDosingUid}`,
      data
    )
  },
  addStudyCompoundDosing(studyUid, data) {
    return repository.post(`studies/${studyUid}/study-compound-dosings`, data)
  },
  deleteStudyCompoundDosing(studyUid, studyCompoundDosingUid) {
    return repository.delete(
      `studies/${studyUid}/study-compound-dosings/${studyCompoundDosingUid}`
    )
  },
  getAllStudyActivities(params) {
    return repository.get('study-activities', { params })
  },
  getStudyActivity(studyUid, activityUid) {
    return repository.get(`studies/${studyUid}/study-activities/${activityUid}`)
  },
  getStudyActivities(studyUid, params) {
    return repository.get(`studies/${studyUid}/study-activities`, { params })
  },
  getStudyActivityInstance(studyUid, instanceUid) {
    return repository.get(
      `studies/${studyUid}/study-activity-instances/${instanceUid}`
    )
  },
  getStudyActivityInstances(studyUid, params) {
    return repository.get(`studies/${studyUid}/study-activity-instances`, {
      params,
    })
  },
  updateStudyActivityInstanceToLatest(studyUid, instanceUid) {
    return repository.post(
      `studies/${studyUid}/study-activity-instances/${instanceUid}/sync-latest-version`
    )
  },
  updateStudyActivityInstance(studyUid, instanceUid, data) {
    return repository.patch(
      `studies/${studyUid}/study-activity-instances/${instanceUid}`,
      data
    )
  },
  batchSelectStudyActivityInstances(studyUid, data) {
    return repository.post(
      `studies/${studyUid}/study-activity-instances/batch-select`,
      data
    )
  },
  getStudyActivityInstancesAuditTrail(studyUid) {
    return repository.get(
      `studies/${studyUid}/study-activity-instances/audit-trail`
    )
  },
  getStudyActivityInstanceAuditTrail(studyUid, instanceUid) {
    return repository.get(
      `studies/${studyUid}/study-activity-instances/${instanceUid}/audit-trail`
    )
  },
  createStudyActivity(studyUid, data) {
    return repository.post(`studies/${studyUid}/study-activities`, data)
  },
  exchangeStudyActivity(studyUid, activityUid, data) {
    return repository.patch(
      `studies/${studyUid}/study-activities/${activityUid}/activity-replacements`,
      data
    )
  },
  async updateStudyActivity(studyUid, studyActivityUid, data) {
    return await repository.patch(
      `studies/${studyUid}/study-activities/${studyActivityUid}`,
      data
    )
  },
  async updateStudyActivityRequest(studyUid, studyActivityUid, data) {
    return await repository.patch(
      `studies/${studyUid}/study-activity-requests/${studyActivityUid}`,
      data
    )
  },
  deleteStudyActivity(studyUid, studyActivityUid) {
    return repository.delete(
      `studies/${studyUid}/study-activities/${studyActivityUid}`
    )
  },
  studyActivityBatchOperations(studyUid, data) {
    return repository.post(`studies/${studyUid}/study-activities/batch`, data)
  },
  getStudyActivitiesAuditTrail(studyUid) {
    return repository.get(`studies/${studyUid}/study-activities/audit-trail`)
  },
  getStudyActivityAuditTrail(studyUid, studyActivityUid) {
    return repository.get(
      `studies/${studyUid}/study-activities/${studyActivityUid}/audit-trail`
    )
  },
  updateStudyActivityOrder(studyUid, studyActivityUid, order) {
    const data = { new_order: order }
    return repository.patch(
      `studies/${studyUid}/study-activities/${studyActivityUid}/order`,
      data
    )
  },
  reorderSoa(studyUid, studySoaGroupUid, order, type) {
    const data = { new_order: order }
    return repository.patch(
      `studies/${studyUid}/${type}/${studySoaGroupUid}/order`,
      data
    )
  },
  async updateStudySoaGroup(studyUid, studySoaGroupUid, data) {
    return repository.patch(
      `studies/${studyUid}/study-soa-groups/${studySoaGroupUid}`,
      data
    )
  },
  async updateStudyActivityGroup(studyUid, studyActivityGroupUid, data) {
    return repository.patch(
      `studies/${studyUid}/study-activity-groups/${studyActivityGroupUid}`,
      data
    )
  },
  async updateStudyActivitySubGroup(studyUid, studyActivitySubGroupUid, data) {
    return repository.patch(
      `studies/${studyUid}/study-activity-subgroups/${studyActivitySubGroupUid}`,
      data
    )
  },
  updateToApprovedActivity(studyUid, studyActivityUid) {
    return repository.patch(
      `studies/${studyUid}/study-activities/${studyActivityUid}/activity-requests-approvals`
    )
  },
  updateToLatestActivityVersion(studyUid, studyActivityUid) {
    return repository.post(
      `studies/${studyUid}/study-activities/${studyActivityUid}/sync-latest-version`
    )
  },
  getStudyActivitySchedules(studyUid, options) {
    const params = {
      ...options,
    }
    return repository.get(`studies/${studyUid}/study-activity-schedules`, {
      params,
    })
  },
  createStudyActivitySchedule(studyUid, data) {
    return repository.post(`studies/${studyUid}/study-activity-schedules`, data)
  },
  deleteStudyActivitySchedule(studyUid, scheduleUid) {
    return repository.delete(
      `studies/${studyUid}/study-activity-schedules/${scheduleUid}`
    )
  },
  studyActivityScheduleBatchOperations(studyUid, data) {
    return repository.post(
      `studies/${studyUid}/study-activity-schedules/batch`,
      data
    )
  },
  studyActivitySoaEditsBatchOperations(studyUid, data) {
    return repository.post(`studies/${studyUid}/soa-edits/batch`, data)
  },
  getAllStudyCriteria(params) {
    return repository.get('study-criteria', { params })
  },
  getStudyCriteria(studyUid) {
    const params = {
      page_size: 0,
    }
    return repository.get(`studies/${studyUid}/study-criteria`, { params })
  },
  getStudyCriteriaObject(studyUid, studyCriteriaUid) {
    return repository.get(
      `studies/${studyUid}/study-criteria/${studyCriteriaUid}`
    )
  },
  getStudyCriteriaWithType(studyUid, criteriaType, params) {
    if (!params.filters) {
      params.filters = {
        'criteria_type.sponsor_preferred_name_sentence_case': {
          v: [criteriaType.name.sponsor_preferred_name_sentence_case],
        },
      }
    } else {
      JSON.parse(params.filters)[
        'criteria_type.sponsor_preferred_name_sentence_case'
      ] = {
        v: [criteriaType.name.sponsor_preferred_name_sentence_case],
      }
    }
    return repository.get(`studies/${studyUid}/study-criteria`, { params })
  },
  getStudyCriteriaAllAuditTrail(studyUid, criteriaTypeUid) {
    return repository.get(
      `studies/${studyUid}/study-criteria/audit-trail?criteria_type_uid=${criteriaTypeUid}`
    )
  },
  getStudyCriteriaAuditTrail(studyUid, studyCriteriaUid) {
    return repository.get(
      `studies/${studyUid}/study-criteria/${studyCriteriaUid}/audit-trail`
    )
  },
  getStudyCriteriaPreview(studyUid, data) {
    return repository.post(`studies/${studyUid}/study-criteria/preview`, data)
  },
  createStudyCriteria(studyUid, data) {
    return repository.post(
      `studies/${studyUid}/study-criteria?create_criteria=true`,
      data
    )
  },
  batchCreateStudyCriteria(studyUid, data) {
    return repository.post(
      `studies/${studyUid}/study-criteria/batch-select`,
      data
    )
  },
  patchStudyCriteria(studyUid, studyCriteriaUid, data) {
    return repository.patch(
      `studies/${studyUid}/study-criteria/${studyCriteriaUid}`,
      data
    )
  },
  updateStudyCriteriaOrder(studyUid, studyCriteriaUid, order) {
    const data = { new_order: order }
    return repository.patch(
      `studies/${studyUid}/study-criteria/${studyCriteriaUid}/order`,
      data
    )
  },
  updateStudyCriteriaKeyCriteria(studyUid, studyCriteriaUid, keyCriteria) {
    const data = { key_criteria: keyCriteria }
    return repository.patch(
      `studies/${studyUid}/study-criteria/${studyCriteriaUid}/key-criteria`,
      data
    )
  },
  deleteStudyCriteria(studyUid, studyCriteriaUid) {
    return repository.delete(
      `studies/${studyUid}/study-criteria/${studyCriteriaUid}`
    )
  },
  updateStudyCriteriaAcceptVersion(studyUid, studyCriteriaUid) {
    return repository.post(
      `studies/${studyUid}/study-criteria/${studyCriteriaUid}/accept-version`
    )
  },
  updateStudyCriteriaLatestVersion(studyUid, studyCriteriaUid) {
    return repository.post(
      `studies/${studyUid}/study-criteria/${studyCriteriaUid}/sync-latest-version`
    )
  },
  getAllStudyActivityInstructions(params) {
    return repository.get('study-activity-instructions', { params })
  },
  getStudyActivityInstructions(studyUid, params) {
    return repository.get(`studies/${studyUid}/study-activity-instructions`, {
      params,
    })
  },
  studyActivityInstructionBatchOperations(studyUid, data) {
    return repository.post(
      `studies/${studyUid}/study-activity-instructions/batch`,
      data
    )
  },
  deleteStudyActivityInstruction(studyUid, studyActivityInstructionUid) {
    return repository.delete(
      `studies/${studyUid}/study-activity-instructions/${studyActivityInstructionUid}`
    )
  },
  create(data) {
    return repository.post(`${resource}`, data)
  },
  updateIdentification(uid, data) {
    const payload = {
      current_metadata: {
        identification_metadata: data,
      },
    }
    if (data.study_parent_part_uid) {
      payload.study_parent_part_uid = data.study_parent_part_uid
    }
    return repository.patch(`${resource}/${uid}`, payload)
  },
  updateStudyType(uid, data, parentUid) {
    const payload = {
      current_metadata: {
        high_level_study_design: data,
      },
    }
    if (parentUid) {
      payload.study_parent_part_uid = parentUid
    }
    return repository.patch(`${resource}/${uid}`, payload)
  },
  updateStudyPopulation(uid, data, parentUid) {
    const payload = {
      current_metadata: {
        study_population: data,
      },
      study_parent_part_uid: parentUid,
    }
    return repository.patch(`${resource}/${uid}`, payload)
  },
  updateStudyIntervention(studyUid, data) {
    const payload = {
      current_metadata: {
        study_intervention: data,
      },
    }
    return repository.patch(`${resource}/${studyUid}`, payload)
  },
  updateStudyDescription(studyUid, data) {
    const payload = {
      current_metadata: {
        study_description: data,
      },
    }
    return repository.patch(`${resource}/${studyUid}`, payload)
  },
  getStudySoAHistory(studyUid, params) {
    return repository.get(`${resource}/${studyUid}/detailed-soa-history`, {
      params,
    })
  },
  getStudyProtocolFlowchart(studyUid, params) {
    return repository.get(`${resource}/${studyUid}/flowchart`, { params })
  },
  getStudyProtocolFlowchartHtml(studyUid, params) {
    return repository.get(`${resource}/${studyUid}/flowchart.html`, { params })
  },
  getStudyProtocolFlowchartDocx(studyUid, params) {
    return repository.get(`${resource}/${studyUid}/flowchart.docx`, {
      responseType: 'blob',
      params,
    })
  },
  exportStudyDetailedSoa(studyUid) {
    const headers = { Accept: 'text/csv' }
    return repository.get(`${resource}/${studyUid}/detailed-soa-exports`, {
      headers,
      responseType: 'blob',
    })
  },
  exportStudyDetailedSoaExcel(studyUid) {
    const headers = {
      Accept:
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }
    return repository.get(`${resource}/${studyUid}/detailed-soa-exports`, {
      headers,
      responseType: 'blob',
    })
  },
  exportStudyOperationalSoa(studyUid) {
    const headers = { Accept: 'text/csv' }
    return repository.get(`${resource}/${studyUid}/operational-soa-exports`, {
      headers,
      responseType: 'blob',
    })
  },
  exportStudyOperationalSoaExcel(studyUid) {
    const headers = {
      Accept:
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }
    return repository.get(`${resource}/${studyUid}/operational-soa.xlsx`, {
      headers,
      responseType: 'blob',
    })
  },
  exportStudyProtocolSoaExcel(studyUid) {
    const headers = {
      Accept:
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    }
    return repository.get(`${resource}/${studyUid}/protocol-soa-exports`, {
      headers,
      responseType: 'blob',
    })
  },
  exportStudyProtocolSoa(studyUid) {
    const headers = { Accept: 'text/csv' }
    return repository.get(`${resource}/${studyUid}/protocol-soa-exports`, {
      headers,
      responseType: 'blob',
    })
  },
  getStudyProtocolInterventionsTableHtml(studyUid) {
    return repository.get(`${resource}/${studyUid}/interventions.html`)
  },
  getStudyProtocolInterventionsTableDocx(studyUid) {
    return repository.get(`${resource}/${studyUid}/interventions.docx`, {
      responseType: 'arraybuffer',
    })
  },
  copyFromStudy(uid, options) {
    return repository.get(`${resource}/${uid}/copy-component`, {
      params: options,
    })
  },
  getStudyDesignFigureSvg(studyUid) {
    return repository.get(`${resource}/${studyUid}/design.svg`)
  },
  getStudyDesignFigureSvgArray(studyUid) {
    return repository.get(`${resource}/${studyUid}/design.svg`, {
      responseType: 'arraybuffer',
    })
  },
  getStudyDiseaseMilestones(studyUid, params) {
    return repository.get(`${resource}/${studyUid}/study-disease-milestones`, {
      params,
    })
  },
  getStudyDiseaseMilestone(studyUid, diseaseMilestoneUid) {
    return repository.get(
      `${resource}/${studyUid}/study-disease-milestones/${diseaseMilestoneUid}`
    )
  },
  getStudyDiseaseMilestonesAuditTrail(studyUid) {
    return repository.get(
      `${resource}/${studyUid}/study-disease-milestones/audit-trail`
    )
  },
  getStudyDiseaseMilestoneAuditTrail(studyUid, diseaseMilestoneUid) {
    return repository.get(
      `${resource}/${studyUid}/study-disease-milestones/${diseaseMilestoneUid}/audit-trail`
    )
  },
  createStudyDiseaseMilestone(studyUid, data) {
    return repository.post(
      `${resource}/${studyUid}/study-disease-milestones`,
      data
    )
  },
  updateStudyDiseaseMilestone(studyUid, diseaseMilestoneUid, data) {
    return repository.patch(
      `${resource}/${studyUid}/study-disease-milestones/${diseaseMilestoneUid}`,
      data
    )
  },
  updateStudyDiseaseMilestoneOrder(studyUid, diseaseMilestoneUid, new_order) {
    const data = { new_order: new_order }
    return repository.patch(
      `${resource}/${studyUid}/study-disease-milestones/${diseaseMilestoneUid}/order`,
      data
    )
  },
  deleteStudyDiseaseMilestone(studyUid, diseaseMilestoneUid) {
    return repository.delete(
      `${resource}/${studyUid}/study-disease-milestones/${diseaseMilestoneUid}`
    )
  },
  getCtrOdmXml(studyUid) {
    return repository.get(`${resource}/${studyUid}/ctr/odm.xml`)
  },
  downloadCtrOdmXml(studyUid) {
    return repository.get(`${resource}/${studyUid}/ctr/odm.xml`, {
      responseType: 'arraybuffer',
    })
  },
  getAllStudyFootnotes(params) {
    return repository.get('study-soa-footnotes', { params })
  },
  getStudyFootnotes(studyUid, params) {
    return repository.get(`studies/${studyUid}/study-soa-footnotes`, { params })
  },
  getStudyFootnote(studyUid, footnoteUid) {
    return repository.get(
      `studies/${studyUid}/study-soa-footnotes/${footnoteUid}`
    )
  },
  getStudyFootnotesAuditTrail(studyUid) {
    return repository.get(`studies/${studyUid}/study-soa-footnote/audit-trail`)
  },
  getStudyFootnoteAuditTrail(studyUid, studyFootnoteUid) {
    return repository.get(
      `studies/${studyUid}/study-soa-footnotes/${studyFootnoteUid}/audit-trail`
    )
  },
  getStudyFootnotePreview(studyUid, data) {
    return repository.post(
      `studies/${studyUid}/study-soa-footnotes/preview`,
      data
    )
  },
  createStudyFootnote(studyUid, data, createFootnote) {
    if (createFootnote === undefined) {
      createFootnote = false
    }
    return repository.post(
      `${resource}/${studyUid}/study-soa-footnotes?create_footnote=${createFootnote}`,
      data
    )
  },
  selectStudyFootnote(studyUid, footnoteUid, referencedItems) {
    const data = {
      footnote_uid: footnoteUid,
      referenced_items: referencedItems,
    }
    return repository.post(
      `${resource}/${studyUid}/study-soa-footnotes?create_footnote=false`,
      data
    )
  },
  batchCreateStudyFootnotes(studyUid, data) {
    return repository.post(
      `studies/${studyUid}/study-soa-footnotes/batch-select`,
      data
    )
  },
  updateStudyFootnote(studyUid, studyFootnoteUid, data) {
    return repository.patch(
      `${resource}/${studyUid}/study-soa-footnotes/${studyFootnoteUid}`,
      data
    )
  },
  batchUpdateStudyFootnotes(studyUid, data) {
    return repository.patch(
      `${resource}/${studyUid}/study-soa-footnotes/batch-edit`,
      data
    )
  },
  deleteStudyFootnote(studyUid, studyFootnoteUid) {
    return repository.delete(
      `${resource}/${studyUid}/study-soa-footnotes/${studyFootnoteUid}`
    )
  },
  updateStudyFootnoteVersion(studyUid, studyFootnoteUid) {
    return repository.post(
      `${resource}/${studyUid}/study-soa-footnotes/${studyFootnoteUid}/sync-latest-version`
    )
  },
  acceptStudyFootnoteVersion(studyUid, studyFootnoteUid) {
    return repository.post(
      `${resource}/${studyUid}/study-soa-footnotes/${studyFootnoteUid}/accept-version`
    )
  },
  getDdfUsdmJson(studyUid) {
    return repository.get(`ddf/v3/studyDefinitions/${studyUid}`)
  },
  getDdfIchM11(studyUid) {
    return repository.get(`ddf/v3/studyDefinitions/${studyUid}/m11`)
  },
  getStudyStandardVersions(studyUid) {
    return repository.get(`${resource}/${studyUid}/study-standard-versions`)
  },
  createStudyStandardVersions(studyUid, data) {
    return repository.post(
      `${resource}/${studyUid}/study-standard-versions`,
      data
    )
  },
  updateStudyStandardVersion(studyUid, standardVersionUid, data) {
    return repository.patch(
      `${resource}/${studyUid}/study-standard-versions/${standardVersionUid}`,
      data
    )
  },
  deleteStudyStandardVersion(studyUid, standardVersionUid) {
    return repository.delete(
      `${resource}/${studyUid}/study-standard-versions/${standardVersionUid}`
    )
  },
  getStudyStandardVersionAuditTrail(studyUid, standardVersionUid) {
    return repository.get(
      `studies/${studyUid}/study-standard-versions/${standardVersionUid}/audit-trail`
    )
  },
  getStudyStandardVersionsAuditTrail(studyUid) {
    return repository.get(
      `studies/${studyUid}/study-standard-versions/audit-trail`
    )
  },
  getPharmaCm(studyUid) {
    return repository.get(`${resource}/${studyUid}/pharma-cm`)
  },
  getPharmaCmXml(studyUid) {
    return repository.get(`${resource}/${studyUid}/pharma-cm.xml`)
  },
  getStructureOverview(params) {
    return repository.get(`${resource}/structure-overview`, { params })
  },
  getStructureStatistics(studyUid) {
    return repository.get(`${resource}/${studyUid}/structure-statistics`)
  },
}
