import repository from '../repositoryStandardsImport'

const resource = 'effective-dates'

export default {
  getAll(effectiveDate, catalogue) {
    return repository.get(`${resource}/${effectiveDate}/changelog`, {
      params: catalogue ? { catalogue } : {},
    })
  },
  upload(effectiveDate, sourceFile, fileContent) {
    return repository.post(
      `${resource}/${effectiveDate}/changelog`,
      fileContent,
      {
        params: { source_file: sourceFile },
        // The terminology-change sheets are the legacy binary .xls, the one
        // workbook CDISC still publishes in that format. Everything else here
        // is .xlsx, which has a different media type entirely.
        headers: { 'Content-Type': 'application/vnd.ms-excel' },
      }
    )
  },
}
