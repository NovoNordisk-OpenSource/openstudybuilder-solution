const TIME_UNIT_SUBSET_STUDY_TIME = 'Study Time'
const TIME_UNIT_SUBSET_STUDY_PREFERRED_TIME_UNIT = 'Study Preferred Time Unit'

// Study Epoch lag time carries data migrated from MMA, which recorded these
// durations as days and weeks. The Study Time subset also contains the singular
// day and week, plus year and years, which stay valid for study visits but are
// not offered for a lag time. Mirrored in api
// domains/study_selections/study_epoch.py. Closed set, will not grow.
const LAG_TIME_UNIT_NAMES = Object.freeze(['days', 'weeks'])

export default {
  TIME_UNIT_SUBSET_STUDY_TIME,
  TIME_UNIT_SUBSET_STUDY_PREFERRED_TIME_UNIT,
  LAG_TIME_UNIT_NAMES,
}
