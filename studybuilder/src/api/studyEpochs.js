import repository from './repository'

const resource = 'studies'

export default {
  getFilteredEpochs(studyUid, options) {
    const params = {
      ...options,
    }
    return repository.get(`${resource}/${studyUid}/study-epochs`, { params })
  },
  getStudyEpochs(studyUid, options) {
    const params = {
      ...options,
    }
    params.page_size = 0
    return repository.get(`${resource}/${studyUid}/study-epochs`, { params })
  },
  getStudyEpoch(studyUid, epochUid) {
    return repository.get(`${resource}/${studyUid}/study-epochs/${epochUid}`)
  },
  getStudyVisit(studyUid, visitUid) {
    return repository.get(`${resource}/${studyUid}/study-visits/${visitUid}`)
  },
  getStudyVisits(studyUid, options) {
    const params = {
      ...options,
    }
    return repository.get(`${resource}/${studyUid}/study-visits`, { params })
  },
  getAmountOfVisitsInStudyEpoch(studyUid, studyEpochUid) {
    return repository.get(
      `${resource}/${studyUid}/get-amount-of-visits-in-epoch/${studyEpochUid}`
    )
  },
  getGlobalAnchorVisit(studyUid) {
    return repository.get(`${resource}/${studyUid}/global-anchor-visit`, {
      ignoreErrors: true,
    })
  },
  getAnchorVisitsInGroupOfSubvisits(studyUid) {
    return repository.get(
      `${resource}/${studyUid}/anchor-visits-in-group-of-subvisits`
    )
  },
  getAnchorVisitsForSpecialVisit(studyUid, epochUid) {
    const params = {
      study_epoch_uid: epochUid
    }
    return repository.get(
      `${resource}/${studyUid}/anchor-visits-for-special-visit`, { params }
    )
  },
  addStudyVisit(studyUid, data) {
    return repository.post(`${resource}/${studyUid}/study-visits`, data)
  },
  getStudyVisitPreview(studyUid, data) {
    return repository.post(`${resource}/${studyUid}/study-visits/preview`, data)
  },
  updateStudyVisit(studyUid, studyVisitUid, data) {
    return repository.patch(
      `${resource}/${studyUid}/study-visits/${studyVisitUid}`,
      data
    )
  },
  deleteStudyVisit(studyUid, studyVisitUid) {
    return repository.delete(
      `${resource}/${studyUid}/study-visits/${studyVisitUid}`
    )
  },
  getStudyVisitVersions(studyUid, studyVisitUid) {
    return repository.get(
      `${resource}/${studyUid}/study-visits/${studyVisitUid}/audit-trail`
    )
  },
  getGroups(studyUid) {
    return repository.get(`${resource}/${studyUid}/allowed-consecutive-groups`)
  },
  reorderStudyEpoch(studyUid, studyEpochUid, order) {
    return repository.patch(
      `${resource}/${studyUid}/study-epochs/${studyEpochUid}/order/${order}`
    )
  },
  addStudyEpoch(studyUid, data) {
    return repository.post(`${resource}/${studyUid}/study-epochs`, data)
  },
  updateStudyEpoch(studyUid, studyEpochUid, data) {
    return repository.patch(
      `${resource}/${studyUid}/study-epochs/${studyEpochUid}`,
      data
    )
  },
  deleteStudyEpoch(studyUid, studyEpochUid) {
    return repository.delete(
      `${resource}/${studyUid}/study-epochs/${studyEpochUid}`
    )
  },
  getStudyEpochVersions(studyUid, studyEpochUid) {
    return repository.get(
      `${resource}/${studyUid}/study-epochs/${studyEpochUid}/audit-trail`
    )
  },
  getStudyArmVersions(studyUid, studyArmUid) {
    return repository.get(
      `${resource}/${studyUid}/study-arms/${studyArmUid}/audit-trail`
    )
  },
  getStudyBranchVersions(studyUid, studyBranchUid) {
    return repository.get(
      `${resource}/${studyUid}/study-branch-arms/${studyBranchUid}/audit-trail`
    )
  },
  getAllowedConfigs() {
    return repository.get('epochs/allowed-configs')
  },
  getPreviewEpoch(studyUid, data) {
    return repository.post(`${resource}/${studyUid}/study-epochs/preview`, data)
  },
  getStudyArmsVersions(studyUid) {
    return repository.get(`${resource}/${studyUid}/study-arms/audit-trail`)
  },
  getStudyBranchesVersions(studyUid) {
    return repository.get(
      `${resource}/${studyUid}/study-branch-arm/audit-trail`
    )
  },
  getStudyVisitsVersions(studyUid) {
    return repository.get(`${resource}/${studyUid}/study-visits/audit-trail`)
  },
  getStudyEpochsVersions(studyUid) {
    return repository.get(`${resource}/${studyUid}/study-epochs/audit-trail`)
  },
  createCollapsibleVisitGroup(studyUid, visitUids, visitTemplateUid) {
    const data = {
      visits_to_assign: visitUids,
    }
    if (visitTemplateUid) {
      data.overwrite_visit_from_template = visitTemplateUid
    }
    return repository.post(
      `${resource}/${studyUid}/consecutive-visit-groups`,
      data,
      { ignoreErrors: true }
    )
  },
  deleteCollapsibleVisitGroup(studyUid, groupName) {
    return repository.delete(
      `${resource}/${studyUid}/consecutive-visit-groups/${groupName}`
    )
  },
}
