// Statuses come from EffectiveDateStatus in the standards_import API. READY is
// reached only after an import failed, so it reads as a warning rather than a
// success here.
export function releaseStatusColor(status) {
  switch (status) {
    case 'IMPORTED':
      return 'success'
    case 'ANALYZED':
      return 'info'
    case 'BLOCKED':
      return 'error'
    case 'IMPORTING':
    case 'READY':
      return 'warning'
    default:
      return 'secondary'
  }
}

// An InconsistencyType from the standards_import API as a reader would write it:
// CONFLICTING_VALUES -> "Conflicting values". The enum value itself stays what the
// API filters and documents by, so this is for display only.
export function findingTypeLabel(type) {
  if (!type) {
    return ''
  }
  const words = type.toLowerCase().replaceAll('_', ' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
}

// InconsistencyStatus from the standards_import API, in the order a reviewer works
// through them: what blocks import, then what still waits on an acknowledgement, then
// what is settled.
export const FINDING_STATUSES = [
  'OPEN',
  'INFORMATIONAL',
  'AUTO_RESOLVED',
  'RESOLVED',
  'IGNORED',
  'ACKNOWLEDGED',
]

// What a reviewer can still do with a finding. An INFORMATIONAL one is settled the same
// way an OPEN one is - acknowledging it is a resolution - and AUTO_RESOLVED has no
// stored decision to take back, so there is nothing to undo there.
export function canResolveFinding(finding) {
  return ['OPEN', 'INFORMATIONAL'].includes(finding.status)
}

export function canUndoFinding(finding) {
  return ['RESOLVED', 'IGNORED', 'ACKNOWLEDGED'].includes(finding.status)
}

export function findingStatusColor(status) {
  switch (status) {
    case 'OPEN':
      return 'error'
    case 'INFORMATIONAL':
      return 'warning'
    case 'AUTO_RESOLVED':
      return 'info'
    case 'IGNORED':
      return 'secondary'
    default:
      return 'success'
  }
}

// How a finding's candidates are laid out, by InconsistencyType. A type missing here
// (a new one the API adds) falls back to the plain candidate chips.
const FINDING_DETAIL_GROUPS = {
  CONFLICTING_VALUES: 'disagreement',
  UNWANTED_QUOTES: 'disagreement',
  CONFLICTING_SUBMISSION_VALUES: 'disagreement',
  SPONSOR_NAME: 'naming',
  SPONSOR_NAME_DIVERGED: 'naming',
  CODELIST_PAIRING: 'naming',
  SPONSOR_TERM_DUPLICATE: 'duplicate',
  SPONSOR_TERM_SEMANTIC_DUPLICATE: 'duplicate',
  SPONSOR_CODELIST_DUPLICATE: 'duplicate',
  INCONSISTENT_TERM_SETS: 'membership',
  CDISC_TERM_SUBMISSION_VALUE_CHANGED: 'membership',
  CDISC_TERM_REMOVED_FROM_CODELIST: 'membership',
}

export function findingDetailGroup(type) {
  return FINDING_DETAIL_GROUPS[type] || null
}

// A candidate or property value as text: list properties are joined, an absent one
// is left empty for the caller to show as it sees fit.
export function formatFindingValue(value) {
  if (Array.isArray(value)) {
    return value.join(', ')
  }
  return value ?? ''
}

// The leading word of a collision candidate: a MatchTier for a string comparison, a
// model's confidence (upper-cased, `UNKNOWN` when it gave none) for a semantic one.
const COLLISION_LEVELS = [
  'EXACT',
  'CASE_INSENSITIVE',
  'NORMALIZED',
  'HIGH',
  'MEDIUM',
  'LOW',
  'UNKNOWN',
]

// The API writes a sponsor collision as one string, `LEVEL:sponsor_uid:prose` (see
// `describe_match` / `describe_candidate`), because a candidate holds a single value.
// Everything after the second colon is prose and may contain colons itself. Returns
// null for a value that is not in that shape.
export function parseCollisionCandidate(value) {
  if (typeof value !== 'string') {
    return null
  }
  const first = value.indexOf(':')
  const second = first < 0 ? -1 : value.indexOf(':', first + 1)
  if (second < 0) {
    return null
  }
  const level = value.slice(0, first)
  if (!COLLISION_LEVELS.includes(level)) {
    return null
  }
  const sponsorUid = value.slice(first + 1, second)
  return {
    level,
    sponsorUid: sponsorUid === '-' ? null : sponsorUid,
    text: value.slice(second + 1),
  }
}

// EXACT is the only level that breaks a uniqueness rule; the rest are judgement calls.
export function collisionLevelColor(level) {
  switch (level) {
    case 'EXACT':
      return 'error'
    case 'CASE_INSENSITIVE':
    case 'HIGH':
      return 'warning'
    case 'NORMALIZED':
    case 'MEDIUM':
      return 'info'
    default:
      return 'secondary'
  }
}

// A term-set candidate is `concept_id:submission_value`. A concept id holds no colon,
// the submission value might.
export function parseTermSetEntry(entry) {
  const separator = typeof entry === 'string' ? entry.indexOf(':') : -1
  if (separator < 0) {
    return { conceptId: String(entry ?? ''), submissionValue: '' }
  }
  return {
    conceptId: entry.slice(0, separator),
    submissionValue: entry.slice(separator + 1),
  }
}

// The attribute keys the review endpoints report are snake_case; the package diff
// already names these same attributes in camelCase, and one set of labels is enough.
const ATTRIBUTE_KEY = {
  preferred_term: 'preferredTerm',
  submission_value: 'submissionValue',
}

// ChangeStatus (codelists) or TermChangeStatus (terms) from the standards_import API.
export function changeStatusColor(status) {
  switch (status) {
    case 'NEW':
      return 'success'
    case 'UPDATED':
    case 'CHANGED':
      return 'warning'
    case 'DELETED':
      return 'error'
    default:
      return 'secondary'
  }
}

// The `StandardsImport.diff_field_*` i18n key labelling one attribute.
export function attributeLabelKey(field) {
  return `StandardsImport.diff_field_${ATTRIBUTE_KEY[field] || field}`
}

// Which step of the import a release is at, rather than its raw status: ANALYZED
// and BLOCKED are reached both by analysis and by the assessment that follows it, so
// the timestamps decide which of the two the release has got to. An analysis newer
// than the last assessment puts it back at the analysis step — unless it left
// nothing open (ANALYZED), which is the analysis step done and the assessment next.
//
// `pendingDecisions` counts the CDISC conflict decisions made since the last
// analysis. Settling the last open conflict already turns BLOCKED into ANALYZED, but
// those decisions only reach the staged values with the next analysis, so until then
// the release is still at the analysis step. Callers without the findings to hand
// leave it at 0.
//
// `canImport` is the API's own verdict (`can_import` of the release dashboard): nothing
// left blocks the import, so the release is waiting on its approval - the importing
// step - even though its status is still ANALYZED. Callers without the dashboard to
// hand leave it false.
// Returns the suffix of a `StandardsImport.stage_*` i18n key, or null.
export function releaseStage(
  release,
  { pendingDecisions = 0, canImport = false } = {}
) {
  switch (release?.status) {
    case 'FILES_STAGED':
      return 'review'
    case 'ANALYZING':
      return 'analysis'
    case 'ASSESSING':
      return 'assessment'
    case 'ANALYZED':
    case 'BLOCKED': {
      if (canImport) {
        return 'importing'
      }
      const { analyzed_at: analyzedAt, assessed_at: assessedAt } = release
      if (assessedAt && new Date(assessedAt) > new Date(analyzedAt)) {
        return 'assessment'
      }
      return release.status === 'ANALYZED' && !pendingDecisions
        ? 'assessment'
        : 'analysis'
    }
    case 'IMPORTING':
    case 'READY':
      return 'importing'
    case 'IMPORTED':
      return 'imported'
    default:
      return null
  }
}

// The review views' outlined buttons that act as switches read their state from this
// icon (and their colour), so the label stays put whichever way they are set.
export function toggleIcon(on) {
  return on ? 'mdi-checkbox-marked-circle' : 'mdi-checkbox-blank-circle-outline'
}
