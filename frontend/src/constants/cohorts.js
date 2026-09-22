const MANUAL = 'Manual'
const FULL = 'Study with cohorts, branches and subpopulations'
// Sentinel for the "Select from studies" creation method. It is NOT a design
// class and must never be sent to the backend as one (it is saved as MANUAL).
const SELECT = 'SelectFromStudies'

export default {
  MANUAL,
  FULL,
  SELECT,
}
