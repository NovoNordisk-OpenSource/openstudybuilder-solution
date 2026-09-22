function getTermPayload(form, name) {
  if (form[name]) {
    return {
      term_uid: form[name].term_uid,
      name: form[name].sponsor_preferred_name || form[name].name,
    }
  }
  return null
}

function getTermsPayload(form, name) {
  const result = []
  if (!form[name]) {
    return null
  }
  form[name].forEach((term) => {
    result.push({
      term_uid: term.term_uid,
      name: term.sponsor_preferred_name || term.name,
    })
  })
  return result
}

export default {
  getTermsPayload,
  getTermPayload,
}
