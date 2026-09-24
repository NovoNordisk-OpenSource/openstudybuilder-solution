import repository from './repository'

export default (basePath) => {
  return {
    get(status) {
      const params = {
        page_size: 0,
      }
      if (status) {
        params.status = status
      }
      return repository.get(`${basePath}`, { params })
    },
    getFiltered(params) {
      return repository.get(`${basePath}`, { params })
    },
    getAllVersions(params) {
      return repository.get(`${basePath}/versions`, { params })
    },
    getObject(uid) {
      return repository.get(`${basePath}/${uid}`)
    },
    getObjectByName(name) {
      const params = {
        page_size: 0,
        filters: {
          name: {
            v: [name],
            op: 'eq',
          },
        },
      }
      return repository.get(`${basePath}`, { params })
    },
    getObjectParameters(uid, params) {
      return repository.get(`${basePath}/${uid}/parameters`, { params })
    },
    getVersions(uid) {
      return repository.get(`${basePath}/${uid}/versions`)
    },
    getStudies(uid) {
      return repository.get(`${basePath}/${uid}/studies`)
    },
    getPreview(data) {
      return repository.post(`${basePath}/preview`, data)
    },
    create(data) {
      return repository.post(`${basePath}`, data)
    },
    update(uid, data) {
      return repository.patch(`${basePath}/${uid}`, data)
    },
    deleteObject(uid) {
      return repository.delete(`${basePath}/${uid}`)
    },
    approve(uid) {
      return repository.post(`${basePath}/${uid}/approvals`)
    },
    inactivate(uid) {
      return repository.delete(`${basePath}/${uid}/activations`)
    },
    reactivate(uid) {
      return repository.post(`${basePath}/${uid}/activations`)
    },
    newVersion(uid) {
      return repository.post(`${basePath}/${uid}/versions`)
    },
  }
}
