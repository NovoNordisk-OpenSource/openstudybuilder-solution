import repository from './repository'

const resource = 'libraries'

export default {
  get(isEditable) {
    let url = `/${resource}`
    if (isEditable !== undefined) {
      url += `?is_editable=${isEditable}`
    }
    return repository.get(url)
  },
  getEditable() {
    return this.get(true)
  },
}
