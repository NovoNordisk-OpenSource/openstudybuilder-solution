import repository from '../repositoryStandardsImport'

export default {
  get(catalogue, effectiveDate) {
    return repository.get(
      `packages/files/${encodeURIComponent(catalogue)}/diff`,
      { params: { effective_date: effectiveDate } }
    )
  },
  // Every catalogue of a release with its bands counted rather than listed: one call,
  // where a card per catalogue would otherwise mean a full diff each.
  getSummaries(effectiveDate) {
    return repository.get('packages/files/diff-summaries', {
      params: { effective_date: effectiveDate },
    })
  },
  // One codelist or term across the last `releases` releases of its catalogue, the one
  // at `effectiveDate` included.
  getConceptHistory(
    catalogue,
    conceptType,
    conceptId,
    effectiveDate,
    releases = 5
  ) {
    return repository.get(
      `packages/files/${encodeURIComponent(catalogue)}/history/${conceptType}/${encodeURIComponent(conceptId)}`,
      { params: { effective_date: effectiveDate, releases } }
    )
  },
  getPreviousRelease(catalogue, effectiveDate) {
    return repository.get(
      `packages/files/${encodeURIComponent(catalogue)}/previous-release`,
      { params: { effective_date: effectiveDate } }
    )
  },
}
