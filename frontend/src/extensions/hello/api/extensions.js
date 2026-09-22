import repository from '../../../api/repositoryExtensions'

export default {
  getDataFromApi(params = {}) {
    return repository.get(`/hello/some-data`, { params })
  },
}
