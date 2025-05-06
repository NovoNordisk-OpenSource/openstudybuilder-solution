import repository from './repository'

const resource = 'concepts/activities'

export default {
  get(options, source) {
    const params = {
      ...options,
    }
    return repository.get(`${resource}/${source}`, { params })
  },
  getObject(source, uid) {
    return repository.get(`${resource}/${source}/${uid}`)
  },
  getObjectOverview(source, uid, version, format) {
    const params = { version }
    const headers = {}
    if (format === 'yaml') {
      headers.Accept = 'application/x-yaml'
    }
    return repository.get(`${resource}/${source}/${uid}/overview`, {
      params,
      headers,
    })
  },
  getCOSMoSOverview(source, uid) {
    return repository.get(`${resource}/${source}/${uid}/overview.cosmos`)
  },
  getVersions(source, uid) {
    return repository.get(`${resource}/${source}/${uid}/versions`)
  },
  getAuditTrail(source, options) {
    const params = {
      page_number: options ? options.page : 1,
      total_count: true,
    }
    if (options) {
      params.page_size = options.itemsPerPage
    }
    return repository.get(`${resource}/${source}/versions`, { params })
  },
  inactivate(uid, source) {
    return repository.delete(`${resource}/${source}/${uid}/activations`)
  },
  reactivate(uid, source) {
    return repository.post(`${resource}/${source}/${uid}/activations`)
  },
  delete(uid, source) {
    return repository.delete(`${resource}/${source}/${uid}`)
  },
  approve(uid, source, params) {
    return repository.post(
      `${resource}/${source}/${uid}/approvals`,
      {},
      { params }
    )
  },
  newVersion(uid, source) {
    return repository.post(`${resource}/${source}/${uid}/versions`)
  },
  rejectActivityRequest(uid, data) {
    const params = {
      ...data,
    }
    return repository.patch(
      `${resource}/activities/${uid}/activity-request-rejections`,
      params
    )
  },
  getCompounds() {
    return repository.get(`${resource}/compounds`)
  },
  getHeaderData(options) {
    const params = {
      ...options,
    }
    return repository.get(`${resource}/headers`, { params })
  },
  getGroups(params) {
    return repository.get(`${resource}/activity-groups`, { params })
  },
  getSubGroups(group) {
    const params = {
      activity_group_uid: group,
      page_size: 0,
      sort_by: { name: true },
    }
    return repository.get(`${resource}/activity-sub-groups`, { params })
  },
  getAllGroups(options) {
    const params = {
      ...options,
    }
    return repository.get(`${resource}/activity-groups`, { params })
  },
  getAllSubGroups(options) {
    const params = {
      ...options,
    }
    return repository.get(`${resource}/activity-sub-groups`, { params })
  },
  getSubGroupActivities(subgroup, group = null) {
    const params = {
      activity_group_uid: group,
      activity_subgroup_uid: subgroup,
      page_size: 0,
      sort_by: { name: true },
    }
    return repository.get(`${resource}/activities`, { params })
  },
  create(data, source) {
    const params = {
      ...data,
    }
    return repository.post(`${resource}/${source}`, params)
  },
  getPreview(data, source) {
    return repository.post(`${resource}/${source}/preview`, data)
  },
  update(uid, data, params, source) {
    const patch_data = {
      ...data,
    }
    return repository.patch(`${resource}/${source}/${uid}`, patch_data, {
      params,
    })
  },
  createFromActivityRequest(data) {
    return repository.post(`${resource}/activities/sponsor-activities`, data)
  },
}
