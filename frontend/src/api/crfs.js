import repository from './repository'
import i18n from '@/plugins/i18n'
import { notificationHub } from '@/plugins/notificationHub'
import { useErrorHandler } from '@/composables/errorHandler'

const resource = 'odms'

function versionParams(version) {
  return version ? { params: { version } } : undefined
}

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
  // Used by the CRF tree, where a Final parent can show an outdated Final
  // child although a newer Draft of that child already exists.
  async newVersionInTree(source, uid) {
    try {
      return await repository.post(
        `${resource}/${source}/${uid}/versions`,
        null,
        {
          ignoreErrors: true,
        }
      )
    } catch (error) {
      if (
        error.response?.data?.message ===
        'New draft version can be created only for FINAL versions.'
      ) {
        notificationHub.add({
          msg: i18n.global.t('CRFTree.new_version_draft_exists'),
          type: 'warning',
          timeout: 0,
        })
        return null
      }
      useErrorHandler(error)
      throw error
    }
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
  getForm(uid, version) {
    return repository.get(`${resource}/forms/${uid}`, versionParams(version))
  },
  createItemGroup(data) {
    return repository.post(`${resource}/item-groups`, data)
  },
  updateItemGroup(data, uid) {
    return repository.patch(`${resource}/item-groups/${uid}`, data)
  },
  getItemGroup(uid, version) {
    return repository.get(
      `${resource}/item-groups/${uid}`,
      versionParams(version)
    )
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
  getItem(uid, version) {
    return repository.get(`${resource}/items/${uid}`, versionParams(version))
  },
  getCollection(uid, version) {
    return repository.get(
      `${resource}/study-events/${uid}`,
      versionParams(version)
    )
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
  // Parses an ODM XML file without storing it. Answers with
  // { forms: [{ form, groups: [{ ref, group, items: [{ ref, item }] }] }] }.
  parseOdmXml(xmlFile, { mapperFile, exporter } = {}) {
    const data = new FormData()
    data.append('xml_file', xmlFile)
    if (mapperFile) {
      data.append('mapper_file', mapperFile)
    }
    return repository.post(`${resource}/metadata/xmls/parse`, data, {
      params: exporter ? { exporter } : undefined,
    })
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
