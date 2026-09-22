import repository from './repository'

const resource = 'odms'

export default {
  get(source, params) {
    if (!source) {
      return repository.get(`${resource}`, params)
    }
    return repository.get(`${resource}/${source}`, params)
  },
  reactivate(source, uid) {
    return repository.post(`${resource}/${source}/${uid}/activations`)
  },
  inactivate(source, uid) {
    return repository.delete(`${resource}/${source}/${uid}/activations`)
  },
  newVersion(source, uid, params) {
    return repository.post(
      `${resource}/${source}/${uid}/versions`,
      null,
      params
    )
  },
  approve(source, uid) {
    return repository.post(`${resource}/${source}/${uid}/approvals`)
  },
  delete(source, uid) {
    return repository.delete(`${resource}/${source}/${uid}`)
  },
  createForm(data) {
    return repository.post(`${resource}/forms`, data)
  },
  updateForm(data, uid) {
    return repository.patch(`${resource}/forms/${uid}`, data)
  },
  getForm(uid) {
    return repository.get(`${resource}/forms/${uid}`)
  },
  createItemGroup(data) {
    return repository.post(`${resource}/item-groups`, data)
  },
  updateItemGroup(data, uid) {
    return repository.patch(`${resource}/item-groups/${uid}`, data)
  },
  getItemGroup(uid) {
    return repository.get(`${resource}/item-groups/${uid}`)
  },
  getCollectionAuditTrail(uid) {
    return repository.get(`${resource}/study-events/${uid}/versions`)
  },
  getFormAuditTrail(uid) {
    return repository.get(`${resource}/forms/${uid}/versions`)
  },
  getGroupAuditTrail(uid) {
    return repository.get(`${resource}/item-groups/${uid}/versions`)
  },
  getItemAuditTrail(uid) {
    return repository.get(`${resource}/items/${uid}/versions`)
  },
  createItem(data) {
    return repository.post(`${resource}/items`, data)
  },
  updateItem(data, uid) {
    return repository.patch(`${resource}/items/${uid}`, data)
  },
  getItem(uid) {
    return repository.get(`${resource}/items/${uid}`)
  },
  getCollection(uid) {
    return repository.get(`${resource}/study-events/${uid}`)
  },
  createCollection(data) {
    return repository.post(`${resource}/study-events`, data)
  },
  updateCollection(data, uid) {
    return repository.patch(`${resource}/study-events/${uid}`, data)
  },
  addFormsToCollection(data, uid, sync) {
    return repository.post(
      `${resource}/study-events/${uid}/forms?override=${sync}`,
      data
    )
  },
  addItemGroupsToForm(data, uid, sync) {
    return repository.post(
      `${resource}/forms/${uid}/item-groups?override=${sync}`,
      data
    )
  },
  addItemsToItemGroup(data, uid, sync) {
    return repository.post(
      `${resource}/item-groups/${uid}/items?override=${sync}`,
      data
    )
  },
  getReport(params) {
    return repository.post(
      `${resource}/metadata/report?${params.targets}target_type=${params.target_type}${params.allowed_namespaces}`
    )
  },
  getXml(params) {
    return repository.post(
      `${resource}/metadata/xmls/export?${params.targets}target_type=${params.target_type}&stylesheet=${params.selectedStylesheet}${params.allowed_namespaces}`
    )
  },
  getPdf(params) {
    return repository.post(
      `${resource}/metadata/xmls/export?${params.targets}target_type=${params.target_type}&stylesheet=${params.selectedStylesheet}&pdf=true${params.allowed_namespaces}`,
      {},
      {
        responseType: 'arraybuffer',
        headers: {
          Accept: 'application/octet-stream',
        },
      }
    )
  },
  getXsl(type) {
    return repository.get(`${resource}/metadata/xmls/stylesheets/${type}`)
  },
  getAliases(params) {
    return repository.get(`${resource}/metadata/aliases`, { params })
  },
  getTranslatedTexts(params) {
    return repository.get(`${resource}/metadata/translated-texts`, { params })
  },
  getRelationships(uid, type) {
    return repository.get(`${resource}/${type}/${uid}/relationships`)
  },
  getCrfForms() {
    return repository.get(`${resource}/forms/study-events`)
  },
  getCrfGroups() {
    return repository.get(`${resource}/item-groups/forms`)
  },
  getAllNamespaces(params) {
    return repository.get(`${resource}/vendor-namespaces`, { params })
  },
  getNamespace(uid) {
    return repository.get(`${resource}/vendor-namespaces/${uid}`)
  },
  createNamespace(data) {
    return repository.post(`${resource}/vendor-namespaces`, data)
  },
  deleteNamespace(uid) {
    return repository.delete(`${resource}/vendor-namespaces/${uid}`)
  },
  editNamespace(uid, data) {
    return repository.patch(`${resource}/vendor-namespaces/${uid}`, data)
  },
  getAllAttributes(params) {
    return repository.get(`${resource}/vendor-attributes`, { params })
  },
  createAttribute(data) {
    return repository.post(`${resource}/vendor-attributes`, data)
  },
  editAttribute(uid, data) {
    return repository.patch(`${resource}/vendor-attributes/${uid}`, data)
  },
  getAllElements(params) {
    return repository.get(`${resource}/vendor-elements`, { params })
  },
  createElement(data) {
    return repository.post(`${resource}/vendor-elements`, data)
  },
  editElement(uid, data) {
    return repository.patch(`${resource}/vendor-elements/${uid}`, data)
  },
}
