import repository from '../repositoryStandardsImport'

const resource = 'effective-dates'

export default {
  // The API requires a body even when it asserts nothing, hence the empty object.
  // `expectedCatalogues` makes it refuse a release holding any other set: the import is
  // append-only, so a catalogue missing from it could never be added afterwards.
  run(effectiveDate, expectedCatalogues) {
    const body = expectedCatalogues?.length
      ? { expected_catalogues: expectedCatalogues }
      : {}
    return repository.post(`${resource}/${effectiveDate}/import`, body)
  },
}
