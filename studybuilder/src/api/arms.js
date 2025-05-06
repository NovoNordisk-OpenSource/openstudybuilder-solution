import repository from './repository'

const resource = 'studies'

export default {
  getAllForStudy(uid, options) {
    return repository.get(`${resource}/${uid}/study-arms`, options)
  },
  getStudyArm(studyUid, armUid) {
    return repository.get(`${resource}/${studyUid}/study-arms/${armUid}`)
  },
  create(uid, data) {
    const params = {
      ...data,
    }
    return repository.post(`${resource}/${uid}/study-arms`, params)
  },
  edit(uid, data, armUid) {
    const params = {
      ...data,
    }
    return repository.patch(`${resource}/${uid}/study-arms/${armUid}`, params)
  },
  delete(studyUid, armUid) {
    return repository.delete(`${resource}/${studyUid}/study-arms/${armUid}`)
  },
  getStudyElements(uid, options) {
    const params = {
      ...options,
    }
    return repository.get(`${resource}/${uid}/study-elements`, { params })
  },
  getStudyElement(uid, elementUid) {
    return repository.get(`${resource}/${uid}/study-elements/${elementUid}`)
  },
  addStudyElement(uid, data) {
    return repository.post(`${resource}/${uid}/study-elements`, data)
  },
  editStudyElement(uid, elementUid, data) {
    return repository.patch(
      `${resource}/${uid}/study-elements/${elementUid}`,
      data
    )
  },
  deleteStudyElement(uid, elementUid) {
    return repository.delete(`${resource}/${uid}/study-elements/${elementUid}`)
  },
  getStudyElementsAllowedConfigs() {
    return repository.get('study-elements/allowed-element-configs')
  },
  getAllStudyCells(uid) {
    return repository.get(`${resource}/${uid}/study-design-cells`)
  },
  createStudyCell(uid, data) {
    return repository.post(`${resource}/${uid}/study-design-cells`, data)
  },
  updateStudyCell(uid, cellUid, data) {
    return repository.patch(
      `${resource}/${uid}/study-design-cells/${cellUid}`,
      data
    )
  },
  deleteStudyCell(uid, cellUid) {
    return repository.delete(`${resource}/${uid}/study-design-cells/${cellUid}`)
  },
  getAllBranchArms(uid, options) {
    const params = {
      ...options,
    }
    return repository.get(`${resource}/${uid}/study-branch-arms`, { params })
  },
  getStudyBranchArm(studyUid, branchArmUid) {
    return repository.get(
      `${resource}/${studyUid}/study-branch-arms/${branchArmUid}`
    )
  },
  createBranchArm(uid, data) {
    return repository.post(`${resource}/${uid}/study-branch-arms`, data)
  },
  editBranchArm(uid, branchArmUid, data) {
    return repository.patch(
      `${resource}/${uid}/study-branch-arms/${branchArmUid}`,
      data
    )
  },
  deleteBranchArm(uid, branchArmUid) {
    return repository.delete(
      `${resource}/${uid}/study-branch-arms/${branchArmUid}`
    )
  },
  updateBranchArmOrder(uid, branchArmUid, newOrder) {
    return repository.patch(
      `${resource}/${uid}/study-branch-arms/${branchArmUid}/order`,
      { new_order: newOrder }
    )
  },
  updateArmOrder(uid, armUid, newOrder) {
    return repository.patch(`${resource}/${uid}/study-arms/${armUid}/order`, {
      new_order: newOrder,
    })
  },
  updateElementOrder(uid, elementUid, newOrder) {
    return repository.patch(
      `${resource}/${uid}/study-elements/${elementUid}/order`,
      { new_order: newOrder }
    )
  },
  getAllBranchesForArm(uid, armUid) {
    return repository.get(`${resource}/${uid}/study-branch-arms/arm/${armUid}`)
  },
  getAllCohorts(uid, options) {
    const params = {
      ...options,
    }
    return repository.get(`${resource}/${uid}/study-cohorts`, { params })
  },
  getStudyCohort(studyUid, cohortUid) {
    return repository.get(`${resource}/${studyUid}/study-cohorts/${cohortUid}`)
  },
  getAllCohortsForArm(uid, armUid) {
    const params = { armUid: armUid }
    return repository.get(`${resource}/${uid}/study-cohorts`, { params })
  },
  createCohort(uid, data) {
    return repository.post(`${resource}/${uid}/study-cohorts`, data)
  },
  editCohort(uid, cohortUid, data) {
    return repository.patch(
      `${resource}/${uid}/study-cohorts/${cohortUid}`,
      data
    )
  },
  updateCohortOrder(uid, cohortUid, newOrder) {
    return repository.patch(
      `${resource}/${uid}/study-cohorts/${cohortUid}/order`,
      { new_order: newOrder }
    )
  },
  deleteCohort(uid, cohortUid) {
    return repository.delete(`${resource}/${uid}/study-cohorts/${cohortUid}`)
  },
  cellsBatchUpdate(uid, data) {
    return repository.post(`${resource}/${uid}/study-design-cells/batch`, data)
  },
  getAllCellsForArm(uid, armUid, data) {
    return repository.get(
      `${resource}/${uid}/study-design-cells/arm/${armUid}`,
      data
    )
  },
  getAllCellsForBranch(uid, branchArmUid, data) {
    return repository.get(
      `${resource}/${uid}/study-design-cells/branch-arm/${branchArmUid}`,
      data
    )
  },
  getStudyCohortVersions(studyUid, studyCohortUid) {
    return repository.get(
      `${resource}/${studyUid}/study-cohorts/${studyCohortUid}/audit-trail`
    )
  },
  getStudyElementVersions(studyUid, studyElementUid) {
    return repository.get(
      `${resource}/${studyUid}/study-elements/${studyElementUid}/audit-trail`
    )
  },
  getStudyCohortsVersions(studyUid) {
    return repository.get(`${resource}/${studyUid}/study-cohort/audit-trail`)
  },
  getStudyElementsVersions(studyUid) {
    return repository.get(`${resource}/${studyUid}/study-element/audit-trail`)
  },
}
