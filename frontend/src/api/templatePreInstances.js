import repository from './repository'

export default (baseType) => {
  const baseUrl = `/${baseType}-pre-instances`
  return {
    get(params) {
      return repository.get(baseUrl, { params })
    },
    getVersions(uid) {
      return repository.get(`${baseUrl}/${uid}/versions`)
    },
    getAuditTrail(options) {
      const params = {
        page_number: options ? options.page : 1,
        total_count: true,
      }
      if (options) {
        params.page_size = options.itemsPerPage
      }
      if (options.filters) {
        params.filters = options.filters
      }
      return repository.get(`${baseUrl}/audit-trail`, { params })
    },
    getParameters(uid, params) {
      return repository.get(`${baseType}-templates/${uid}/parameters`, {
        params,
      })
    },
    create(templateUid, data) {
      const url = `/${baseType}-templates/${templateUid}/pre-instances`
      return repository.post(url, data)
    },
    update(uid, data) {
      return repository.patch(`${baseUrl}/${uid}`, data)
    },
    approve(uid) {
      return repository.post(`${baseUrl}/${uid}/approvals`)
    },
    approveCascade(uid, cascade) {
      return repository.post(`${baseUrl}/${uid}/approvals?cascade=${cascade}`)
    },
    updateIndexings(uid, data) {
      return repository.patch(`${baseUrl}/${uid}/indexings`, data)
    },
    createNewVersion(uid, data) {
      return repository.post(`${baseUrl}/${uid}/versions`, data)
    },
    inactivate(uid) {
      return repository.delete(`${baseUrl}/${uid}/activations`)
    },
    reactivate(uid) {
      return repository.post(`${baseUrl}/${uid}/activations`)
    },
    delete(uid) {
      return repository.delete(`${baseUrl}/${uid}`)
    },
  }
}
