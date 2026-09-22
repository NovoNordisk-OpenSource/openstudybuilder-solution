import repository from './repository'

export default (basePath) => {
  return {
    get(params) {
      const url = `${basePath}`
      return repository.get(url, { params })
    },
    getTemplate(uid) {
      return repository.get(`${basePath}/${uid}`)
    },
    getParameters(uid, params) {
      return repository.get(`${basePath}/${uid}/parameters`, { params })
    },
    getObjectTemplateParameters(uid) {
      return repository.get(`${basePath}/${uid}/parameters`)
    },
    getVersions(uid) {
      return repository.get(`${basePath}/${uid}/versions`)
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
      return repository.get(`${basePath}/audit-trail`, { params })
    },
    create(data) {
      return repository.post(`${basePath}`, data)
    },
    update(uid, data) {
      return repository.patch(`${basePath}/${uid}`, data)
    },
    approve(uid) {
      return repository.post(`${basePath}/${uid}/approvals`)
    },
    approveCascade(uid, cascade) {
      return repository.post(`${basePath}/${uid}/approvals?cascade=${cascade}`)
    },
    createNewVersion(uid, data) {
      return repository.post(`${basePath}/${uid}/versions`, data)
    },
    inactivate(uid) {
      return repository.delete(`${basePath}/${uid}/activations`)
    },
    reactivate(uid) {
      return repository.post(`${basePath}/${uid}/activations`)
    },
    delete(uid) {
      return repository.delete(`${basePath}/${uid}`)
    },
    preValidate(data) {
      return repository.post(`${basePath}/pre-validate`, data)
    },
    updateIndexings(uid, data) {
      return repository.patch(`${basePath}/${uid}/indexings`, data)
    },
    addPreInstance(uid, data) {
      return repository.post(`${basePath}/${uid}/pre-instances`, data)
    },
  }
}
