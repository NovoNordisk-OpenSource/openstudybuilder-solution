import repository from './repository'

const resource = 'ct'

export default {
  getCatalogues() {
    return repository.get(`${resource}/catalogues`)
  },
  getPackages(params) {
    return repository.get(`${resource}/packages`, { params })
  },
  getSponsorPackages(catalogueName) {
    const params = {
      sponsor_only: true,
    }
    if (catalogueName) {
      params.catalogue_name = catalogueName
    }
    return repository.get(`${resource}/packages`, { params })
  },
  getPackagesDates(catalogueName) {
    const params = { catalogue_name: catalogueName }
    return repository.get(`${resource}/packages/dates`, { params })
  },
  getPackagesChanges(catalogueName, fromDate, toDate) {
    const params = {
      catalogue_name: catalogueName,
      old_package_date: fromDate,
      new_package_date: toDate,
    }
    return repository.get(`${resource}/packages/changes`, { params })
  },
  getPackagesCodelistChanges(codelistUid, catalogueName, fromDate, toDate) {
    const params = {
      catalogue_name: catalogueName,
      old_package_date: fromDate,
      new_package_date: toDate,
    }
    return repository.get(`${resource}/packages/${codelistUid}/changes`, {
      params,
    })
  },
  createSponsorPackage(data) {
    return repository.post(`${resource}/packages/sponsor`, data)
  },
  getCodelists(options) {
    const params = {
      ...options,
    }
    if (params.page_size === -1) {
      params.page_size = 1000
    }
    return repository.get(`${resource}/codelists`, { params })
  },
  getCodelistNames(codelistUid) {
    return repository.get(`${resource}/codelists/${codelistUid}/names`)
  },
  getCodelistNamesVersions(codelistUid) {
    return repository.get(`${resource}/codelists/${codelistUid}/names/versions`)
  },
  updateCodelistNames(codelistUid, data) {
    return repository.patch(`${resource}/codelists/${codelistUid}/names`, data)
  },
  newCodelistNamesVersion(codelistUid) {
    return repository.post(
      `${resource}/codelists/${codelistUid}/names/versions`
    )
  },
  approveCodelistNames(codelistUid) {
    return repository.post(
      `${resource}/codelists/${codelistUid}/names/approvals`
    )
  },
  getCodelistAttributes(codelistUid) {
    return repository.get(`${resource}/codelists/${codelistUid}/attributes`)
  },
  getCodelistAttributesVersions(codelistUid) {
    return repository.get(
      `${resource}/codelists/${codelistUid}/attributes/versions`
    )
  },
  newCodelistAttributesVersion(codelistUid) {
    return repository.post(
      `${resource}/codelists/${codelistUid}/attributes/versions`
    )
  },
  approveCodelistAttributes(codelistUid) {
    return repository.post(
      `${resource}/codelists/${codelistUid}/attributes/approvals`
    )
  },
  getPairedCodelists(codelistUid) {
    return repository.get(`${resource}/codelists/${codelistUid}/paired`)
  },
  updatePairedCodelists(codelistUid, data) {
    return repository.patch(`${resource}/codelists/${codelistUid}/paired`, data)
  },
  getTermCodelists(termUid) {
    return repository.get(`${resource}/terms/${termUid}/codelists`)
  },
  getTermParents(termUid) {
    return repository.get(`${resource}/terms/${termUid}/parents`)
  },
  addTermParent(termUid, parentUid, relationshipType) {
    const params = {
      parent_uid: parentUid,
      relationship_type: relationshipType,
    }
    return repository.post(
      `${resource}/terms/${termUid}/parents`,
      {},
      { params }
    )
  },
  deleteTermParent(termUid, parentUid, relationshipType) {
    const params = {
      parent_uid: parentUid,
      relationship_type: relationshipType,
    }
    return repository.delete(`${resource}/terms/${termUid}/parents`, { params })
  },
  getCodelistTerms(params) {
    return repository.get(`${resource}/terms`, { params })
  },
  getCodelistTermsNames(params) {
    return repository.get(`${resource}/terms/names`, { params })
  },
  getCodelistTermNames(termUid) {
    return repository.get(`${resource}/terms/${termUid}/names`)
  },
  getCodelistTermNamesVersions(termUid, params) {
    return repository.get(`${resource}/terms/${termUid}/names/versions`, {
      params,
    })
  },
  newCodelistTermNamesVersion(termUid) {
    return repository.post(`${resource}/terms/${termUid}/names/versions`)
  },
  approveCodelistTermNames(termUid) {
    return repository.post(`${resource}/terms/${termUid}/names/approvals`)
  },
  inactivateCodelistTermNames(termUid) {
    return repository.delete(`${resource}/terms/${termUid}/names/activations`)
  },
  reactivateCodelistTermNames(termUid) {
    return repository.post(`${resource}/terms/${termUid}/names/activations`)
  },
  deleteCodelistTermNames(termUid) {
    return repository.delete(`${resource}/terms/${termUid}/names`)
  },
  getCodelistTermsAttributes(codelistUid, options) {
    const params = {
      ...options,
      codelist_uid: codelistUid,
    }
    return repository.get(`${resource}/terms/attributes`, { params })
  },
  getCodelistTermAttributes(termUid) {
    return repository.get(`${resource}/terms/${termUid}/attributes`)
  },
  getCodelistTermAttributesVersions(termUid, params) {
    return repository.get(`${resource}/terms/${termUid}/attributes/versions`, {
      params,
    })
  },
  newCodelistTermAttributesVersion(termUid) {
    return repository.post(`${resource}/terms/${termUid}/attributes/versions`)
  },
  approveCodelistTermAttributes(termUid) {
    return repository.post(`${resource}/terms/${termUid}/attributes/approvals`)
  },
  inactivateCodelistTermAttributes(termUid) {
    return repository.delete(
      `${resource}/terms/${termUid}/attributes/activations`
    )
  },
  reactivateCodelistTermAttributes(termUid) {
    return repository.post(
      `${resource}/terms/${termUid}/attributes/activations`
    )
  },
  deleteCodelistTermAttributes(termUid) {
    return repository.delete(`${resource}/terms/${termUid}/attributes`)
  },
  createCodelistTerm(data) {
    return repository.post(`${resource}/terms`, data)
  },
  addTermToCodelist(codelistUid, data) {
    return repository.post(`${resource}/codelists/${codelistUid}/terms`, data)
  },
  removeTermFromCodelist(codelistUid, termUid) {
    return repository.delete(
      `${resource}/codelists/${codelistUid}/terms/${termUid}`
    )
  },
  updateCodelistTermOrderSubmval(termUid, data) {
    return repository.patch(`${resource}/terms/${termUid}/codelists`, data)
  },
  updateCodelistTermNames(termUid, data) {
    return repository.patch(`${resource}/terms/${termUid}/names`, data)
  },
  updateCodelistTermAttributes(termUid, data) {
    return repository.patch(`${resource}/terms/${termUid}/attributes`, data)
  },
  updateCodelistAttributes(codelistUid, data) {
    return repository.patch(
      `${resource}/codelists/${codelistUid}/attributes`,
      data
    )
  },
  createCodelist(data) {
    return repository.post(`${resource}/codelists`, data)
  },
  getStats() {
    return repository.get(`${resource}/stats`)
  },
}
