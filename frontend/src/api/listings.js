import repository from './repository'

const resource = 'listings/studies'

export default {
  getAllSdtm(uid, options, type) {
    const params = {
      ...options,
    }
    return repository.get(`${resource}/${uid}/sdtm/${type.toLowerCase()}`, {
      params,
    })
  },
  getAllAdam(studyUid, type, params) {
    return repository.get(`${resource}/${studyUid}/adam/${type}`, { params })
  },
}
