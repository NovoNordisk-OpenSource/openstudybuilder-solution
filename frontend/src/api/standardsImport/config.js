import repository from '../repositoryStandardsImport'

const resource = 'config'

export default {
  getCataloguePriority() {
    return repository.get(`${resource}/catalogue-priority`)
  },
  setMandatoryCatalogues(catalogues) {
    return repository.put(`${resource}/mandatory-catalogues`, { catalogues })
  },
  getImportEnabled() {
    return repository.get(`${resource}/import-enabled`)
  },
  setImportEnabled(enabled) {
    return repository.put(`${resource}/import-enabled`, { enabled })
  },
  setExpectedWorkbooks(catalogues) {
    return repository.put(`${resource}/expected-workbooks`, { catalogues })
  },
}
