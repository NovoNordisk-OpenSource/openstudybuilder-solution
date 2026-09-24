const LIBRARY_SPONSOR = 'Sponsor'
const LIBRARY_USER_DEFINED = 'User Defined'
const LIBRARY_REQUESTED = 'Requested'
const LIBRARY_UCUM = 'UCUM'
const LIBRARY_ARCHIVED = 'Archived'
const LIBRARY_SNOMED = 'SNOMED'
const LIBRARY_MED_RT = 'MED-RT'
const LIBRARY_UNII = 'UNII'

// Libraries returned as editable by the API but which must not be offered as a
// target library in pickers, nor listed as a CT library in the sidebar.
const EXCLUDED_LIBRARIES = new Set([
  LIBRARY_SNOMED,
  LIBRARY_MED_RT,
  LIBRARY_UNII,
  LIBRARY_UCUM,
  LIBRARY_USER_DEFINED,
  LIBRARY_REQUESTED,
  LIBRARY_ARCHIVED,
])

export default {
  LIBRARY_SPONSOR,
  LIBRARY_USER_DEFINED,
  LIBRARY_REQUESTED,
  LIBRARY_UCUM,
  LIBRARY_ARCHIVED,
  LIBRARY_SNOMED,
  LIBRARY_MED_RT,
  LIBRARY_UNII,
  EXCLUDED_LIBRARIES,
}
