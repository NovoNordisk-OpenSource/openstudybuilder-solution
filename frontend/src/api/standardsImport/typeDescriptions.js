import repository from '../repositoryStandardsImport'

export default {
  get() {
    return repository.get('type-descriptions')
  },
}
