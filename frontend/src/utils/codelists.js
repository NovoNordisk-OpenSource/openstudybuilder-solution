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
export default {
  getTermOrderInCodelist,
}
