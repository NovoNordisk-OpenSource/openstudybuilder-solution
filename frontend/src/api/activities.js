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

  getActivityGroupDetails(uid, version) {
    const params = { version }
    return repository.get(`${resource}/activity-groups/${uid}/details`, {
      params,
    })
  },

  getActivityGroupSubgroups(uid, version, options = {}) {
    const params = {
      version,
      ...options,
    }
    return repository.get(`${resource}/activity-groups/${uid}/subgroups`, {
      params,
    })
  },
  getCOSMoSOverview(source, uid) {
    return repository.get(`${resource}/${source}/${uid}/overview.cosmos`)
  },
  getVersions(source, uid, subitem = null) {
    const subitemPath = subitem ? `/${subitem}` : ''
    return repository.get(`${resource}/${source}/${uid}${subitemPath}/versions`)
  },
  getAuditTrail(source, options) {
    const params = {
      page_number: options ? options.page : 1,
      total_count: true,
    }
    if (options) {
      params.page_size = options.itemsPerPage
    }
    return repository.get(`${resource}/${source}`, { params })
  },
  inactivate(uid, source, subitem = null) {
    const subitemPath = subitem ? `/${subitem}` : ''
    return repository.delete(
      `${resource}/${source}/${uid}${subitemPath}/activations`
    )
  },
  reactivate(uid, source, subitem = null) {
    const subitemPath = subitem ? `/${subitem}` : ''
    return repository.post(
      `${resource}/${source}/${uid}${subitemPath}/activations`
    )
  },
  delete(uid, source) {
    return repository.delete(`${resource}/${source}/${uid}`)
  },
  approve(uid, source, params, subitem = null) {
    const subitemPath = subitem ? `/${subitem}` : ''
    return repository.post(
      `${resource}/${source}/${uid}${subitemPath}/approvals`,
      {},
      { params }
    )
  },
  newVersion(uid, source, subitem = null) {
    const subitemPath = subitem ? `/${subitem}` : ''
    return repository.post(
      `${resource}/${source}/${uid}${subitemPath}/versions`
    )
  },
  batchUpdateInstanceGroupings(data) {
    return repository.post(
      `${resource}/activity-instances/groupings/batch-update`,
      data
    )
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
      page_size: 0,
      sort_by: { name: true },
    }
    return repository.get(`${resource}/activity-groups/${group}/subgroups`, {
      params,
    })
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
  getSubGroupActivities(subgroup, group = null, options = {}) {
    const params = {
      activity_group_uid: group,
      activity_subgroup_uid: subgroup,
      page_size: 0,
      sort_by: { name: true },
      ...options,
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
  update(uid, data, params, source, subitem = null) {
    const patch_data = {
      ...data,
    }
    const subitemPath = subitem ? `/${subitem}` : ''
    if (
      ['activities', 'activity-groups', 'activity-sub-groups'].includes(source)
    ) {
      return repository.put(
        `${resource}/${source}/${uid}${subitemPath}`,
        patch_data,
        {
          params,
        }
      )
    }
    return repository.patch(
      `${resource}/${source}/${uid}${subitemPath}`,
      patch_data,
      {
        params,
      }
    )
  },
  createFromActivityRequest(data) {
    return repository.post(`${resource}/activities/sponsor-activities`, data)
  },
  getVersionDetail(uid, version, params) {
    return repository.get(
      `${resource}/activities/${uid}/versions/${version}/groupings`,
      { params }
    )
  },
  getVersionInstances(uid, version, params) {
    return repository.get(
      `${resource}/activities/${uid}/versions/${version}/instances`,
      { params }
    )
  },
  getAllVersionsInstances(uid) {
    return repository.get(`${resource}/activities/${uid}/versions/instances`)
  },

  getSubgroupActivities(activity_subgroup_uid, options = {}) {
    const params = {
      ...options,
    }
    return repository.get(
      `${resource}/activity-sub-groups/${activity_subgroup_uid}/activities`,
      { params }
    )
  },
  getSubgroupGroups(activity_subgroup_uid, options = {}) {
    const params = {
      ...options,
    }
    return repository.get(
      `${resource}/activity-sub-groups/${activity_subgroup_uid}/activity-groups`,
      { params }
    )
  },

  // New endpoints for Activity Instance overview page
  getActivityInstanceGroupings(activity_instance_uid, version, params = {}) {
    const queryParams = {
      ...params,
    }
    if (version) {
      queryParams.version = version
    }
    return repository.get(
      `${resource}/activity-instances/${activity_instance_uid}/groupings`,
      { params: queryParams }
    )
  },

  getActivityInstanceItems(activity_instance_uid, version, params = {}) {
    const queryParams = {
      ...params,
    }
    if (version) {
      queryParams.version = version
    }
    return repository.get(
      `${resource}/activity-instances/${activity_instance_uid}/activity-items`,
      { params: queryParams }
    )
  },
}
