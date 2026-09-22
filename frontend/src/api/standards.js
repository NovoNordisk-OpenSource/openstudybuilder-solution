import repository from './repository'

const resource = 'standards'

export default {
  getAllModels(params) {
    return repository.get(`${resource}/data-models`, { params })
  },
  getModelByUid(uid) {
    return repository.get(`${resource}/data-models/${uid}`)
  },
  getDatasetClasses(params) {
    return repository.get(`${resource}/dataset-classes`, { params })
  },
  getClassVariables(params) {
    return repository.get(`${resource}/class-variables`, { params })
  },
  getAllGuides(params) {
    return repository.get(`${resource}/data-model-igs`, { params })
  },
  getDatasets(params) {
    return repository.get(`${resource}/datasets`, { params })
  },
  getDatasetVariables(params) {
    return repository.get(`${resource}/dataset-variables`, { params })
  },
  getSponsorModels(params) {
    return repository.get(`${resource}/sponsor-models/models`, { params })
  },
  getSponsorModelDatasets(params) {
    return repository.get(`${resource}/sponsor-models/datasets`, { params })
  },
  getSponsorModelDatasetVariables(params) {
    return repository.get(`${resource}/sponsor-models/dataset-variables`, {
      params,
    })
  },
  getSponsorModelSchema(schemaVersion, libraryName = undefined) {
    const params = libraryName ? { library_name: libraryName } : undefined
    return repository.get(
      `${resource}/sponsor-models/schema/${schemaVersion}`,
      {
        params,
      }
    )
  },
  getSponsorModelSchemas(params) {
    return repository.get(`${resource}/sponsor-models/schema`, { params })
  },
}
