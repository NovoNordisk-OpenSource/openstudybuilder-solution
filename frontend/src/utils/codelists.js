function getTermOrderInCodelist(term, codelistUid) {
  let order = ''
  if (term.codelists) {
    term.codelists.forEach((x) => {
      if (x.codelist_uid === codelistUid) {
        order = x.order
      }
    })
  }
  return order
}

// Each missing term is reported once per page load
const reportedMissingTerms = new Set()

// Resolves a term_uid by submission value (not renamable like sponsor_preferred_name); null and a one-time warning if absent
function findTermUidBySubmissionValue(terms, submissionValue, codelistName) {
  if (!terms?.length) {
    return null
  }
  const termUid =
    terms.find((term) => term.submission_value === submissionValue)?.term_uid ??
    null
  const reportKey = `${codelistName}/${submissionValue}`
  if (termUid === null && !reportedMissingTerms.has(reportKey)) {
    reportedMissingTerms.add(reportKey)
    console.warn(
      `Term '${submissionValue}' not found in the ${codelistName} codelist, its special handling is disabled.`
    )
  }
  return termUid
}

export default {
  getTermOrderInCodelist,
  findTermUidBySubmissionValue,
}
