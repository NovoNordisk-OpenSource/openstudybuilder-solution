import repository from '../repositoryStandardsImport'

const resource = 'effective-dates'

export default {
  getAll(effectiveDate) {
    return repository.get(`${resource}/${effectiveDate}/pairings`)
  },
  upload(effectiveDate, sourceFile, fileContent) {
    return repository.post(
      `${resource}/${effectiveDate}/pairings`,
      fileContent,
      {
        params: { source_file: sourceFile },
        headers: {
          'Content-Type':
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        },
      }
    )
  },
}
