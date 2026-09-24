import repository from './repository'

const resource = 'studies'

export default {
  armsBatchActions(studyUid, data) {
    return repository.post(`${resource}/${studyUid}/study-arms/batch`, data)
  },
  copyArmsFromStudy(studyUid, sourceStudyUid) {
    return repository.post(
      `${resource}/${studyUid}/study-arms/copy-from-study/${sourceStudyUid}`
    )
  },
  cohortsBatchActions(studyUid, data) {
    return repository.post(`${resource}/${studyUid}/study-cohorts/batch`, data)
  },
  branchesBatchActions(studyUid, data) {
    return repository.post(
      `${resource}/${studyUid}/study-branch-arms/batch`,
      data
    )
  },
  setStudyDesignClass(studyUid, data) {
    return repository.post(`${resource}/${studyUid}/study-design-classes`, data)
  },
  getStudyDesignClass(studyUid) {
    return repository.get(`${resource}/${studyUid}/study-design-classes`, {
      ignoreErrors: true,
    })
  },
  changeStudyDesignClass(studyUid, data) {
    return repository.put(`${resource}/${studyUid}/study-design-classes`, data)
  },
  checkDesignClassEditable(studyUid) {
    //This endpoint checks if there are any arms and cohorts for a study
    return repository.get(
      `${resource}/${studyUid}/study-design-classes/editions-allowed`
    )
  },
  getStudyStructure(studyUid) {
    return repository.get(
      `${resource}/${studyUid}/study-arms-branches-and-cohorts`
    )
  },
  removeArm(studyUid, armUid) {
    return repository.delete(`${resource}/${studyUid}/study-arms/${armUid}`)
  },
  removeCohort(uid, cohortUid, deleteBranches = false) {
    return repository.delete(
      `${resource}/${uid}/study-cohorts/${cohortUid}?delete_linked_branches=${deleteBranches}`
    )
  },
  getSourceVariable(studyUid) {
    return repository.get(`${resource}/${studyUid}/study-source-variables`)
  },
  setSourceVariable(studyUid, data) {
    return repository.post(
      `${resource}/${studyUid}/study-source-variables`,
      data
    )
  },
  editSourceVariable(studyUid, data) {
    return repository.put(
      `${resource}/${studyUid}/study-source-variables`,
      data
    )
  },
}
