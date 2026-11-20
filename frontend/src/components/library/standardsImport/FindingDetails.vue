<template>
  <!-- What a finding is about, laid out by kind: the candidates mean something different
       for each type, so the same bare chips would hide which value is which. A type
       this does not know falls back to those chips. -->
  <div data-cy="standards-import-finding-details">
    <template v-if="group === 'disagreement'">
      <div v-if="subject" class="text-caption text-medium-emphasis">
        {{ subject }}
      </div>
      <div v-if="finding.type === 'UNWANTED_QUOTES'" class="text-caption">
        {{ $t('StandardsImport.finding_detail_quoted') }}
      </div>
      <div
        v-for="(candidate, index) in finding.candidates"
        :key="index"
        class="d-flex align-center flex-wrap"
      >
        <v-chip size="small" class="mr-2 my-1">
          {{ displayValue(candidate.value) }}
        </v-chip>
        <span
          v-if="candidate.catalogues?.length"
          class="text-caption text-medium-emphasis"
        >
          {{
            $t('StandardsImport.finding_detail_supplied_by', {
              catalogues: candidate.catalogues.join(', '),
            })
          }}
        </span>
      </div>
    </template>

    <template v-else-if="group === 'naming'">
      <template v-if="finding.type === 'CODELIST_PAIRING'">
        <div class="text-caption text-medium-emphasis">
          {{ $t('StandardsImport.finding_detail_pairs_with') }}
        </div>
        <v-chip
          v-for="(candidate, index) in finding.candidates"
          :key="index"
          size="small"
          class="mr-1 my-1"
        >
          {{ displayValue(candidate.value) }}
        </v-chip>
      </template>
      <template v-else>
        <div
          v-for="(candidate, index) in finding.candidates"
          :key="index"
          class="mb-1"
        >
          <div class="text-caption text-medium-emphasis">
            {{ candidateLabel(candidate) }}
          </div>
          <v-chip size="small" class="mr-2">
            {{ displayValue(candidate.value) }}
          </v-chip>
          <span
            v-if="candidate.catalogues?.length"
            class="text-caption text-medium-emphasis"
          >
            {{
              $t('StandardsImport.finding_detail_supplied_by', {
                catalogues: candidate.catalogues.join(', '),
              })
            }}
          </span>
        </div>
        <div v-if="memberships.length" class="text-caption">
          <span class="text-medium-emphasis">
            {{ $t('StandardsImport.finding_detail_in_codelists') }}
          </span>
          <span
            v-for="[codelistId, submissionValue] in memberships"
            :key="codelistId"
          >
            <v-chip size="x-small" class="ml-1" variant="outlined">
              {{ codelistId }}: {{ submissionValue }}
            </v-chip>
          </span>
        </div>
      </template>
    </template>

    <template v-else-if="group === 'duplicate'">
      <div
        v-for="(candidate, index) in finding.candidates"
        :key="index"
        class="mb-2"
      >
        <template v-if="collision(candidate)">
          <v-chip
            size="x-small"
            variant="tonal"
            class="mr-2"
            :color="collisionLevelColor(collision(candidate).level)"
          >
            {{ levelLabel(collision(candidate).level) }}
          </v-chip>
          <span>{{ collision(candidate).text }}</span>
          <div
            v-if="sponsorUid(candidate)"
            class="text-caption text-medium-emphasis"
          >
            {{
              $t('StandardsImport.finding_detail_sponsor_uid', {
                uid: sponsorUid(candidate),
              })
            }}
          </div>
        </template>
        <template v-else>
          {{ displayValue(candidate.value) }}
        </template>
      </div>
    </template>

    <template v-else-if="group === 'membership'">
      <template v-if="finding.type === 'INCONSISTENT_TERM_SETS'">
        <div
          v-for="(candidate, index) in finding.candidates"
          :key="index"
          class="mb-2"
        >
          <div class="text-caption text-medium-emphasis">
            {{
              candidate.catalogues?.length
                ? $t('StandardsImport.finding_detail_only_in', {
                    catalogues: candidate.catalogues.join(', '),
                  })
                : $t('StandardsImport.finding_detail_terms')
            }}
          </div>
          <v-chip
            v-for="entry in termSet(candidate)"
            :key="entry.conceptId"
            size="small"
            class="mr-1 mb-1"
          >
            {{ entry.submissionValue || entry.conceptId }}
            <span class="text-caption text-medium-emphasis ml-1">
              {{ entry.conceptId }}
            </span>
          </v-chip>
          <span v-if="!termSet(candidate).length" class="text-medium-emphasis">
            &mdash;
          </span>
        </div>
      </template>
      <template
        v-else-if="finding.type === 'CDISC_TERM_SUBMISSION_VALUE_CHANGED'"
      >
        <div class="text-caption text-medium-emphasis">
          {{ $t(attributeLabelKey('submission_value')) }}
        </div>
        <div class="d-flex align-center flex-wrap">
          <template
            v-for="(candidate, index) in finding.candidates"
            :key="index"
          >
            <v-icon v-if="index" size="16" class="mx-2">mdi-arrow-right</v-icon>
            <div>
              <v-chip size="small">{{ displayValue(candidate.value) }}</v-chip>
              <div class="text-caption text-medium-emphasis">
                {{ candidateLabel(candidate) }}
              </div>
            </div>
          </template>
        </div>
      </template>
      <template v-else>
        <div class="text-caption text-medium-emphasis">
          {{ $t('StandardsImport.finding_detail_removed') }}
        </div>
        <div
          v-for="(candidate, index) in finding.candidates"
          :key="index"
          class="d-flex align-center flex-wrap"
        >
          <v-chip size="small" class="mr-2 my-1">
            {{ displayValue(candidate.value) }}
          </v-chip>
          <span class="text-caption text-medium-emphasis">
            {{ candidateLabel(candidate) }}
          </span>
        </div>
      </template>
    </template>

    <template v-else>
      <v-chip
        v-for="(candidate, index) in finding.candidates"
        :key="index"
        size="small"
        class="mr-1 mb-1"
      >
        {{ displayValue(candidate.value) }}
        <v-tooltip
          v-if="candidate.source || candidate.catalogues?.length"
          location="top"
        >
          <template #activator="{ props: tooltipProps }">
            <v-icon v-bind="tooltipProps" size="14" class="ml-1">
              mdi-information-outline
            </v-icon>
          </template>
          {{ candidate.source || candidate.catalogues.join(', ') }}
        </v-tooltip>
      </v-chip>
    </template>

    <div><FindingUsageChip :finding="finding" /></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import FindingUsageChip from './FindingUsageChip.vue'
import {
  attributeLabelKey,
  collisionLevelColor,
  findingDetailGroup,
  findingTypeLabel,
  formatFindingValue,
  parseCollisionCandidate,
  parseTermSetEntry,
} from '@/utils/standardsImport'

const { t, te } = useI18n()

const props = defineProps({
  finding: {
    type: Object,
    required: true,
  },
})

const group = computed(() => findingDetailGroup(props.finding.type))

// A submission-value finding is about that attribute without naming it as a property.
const subject = computed(() => {
  const { property, type } = props.finding
  if (property) {
    const key = attributeLabelKey(property)
    return te(key) ? t(key) : property
  }
  return ['CONFLICTING_SUBMISSION_VALUES', 'UNWANTED_QUOTES'].includes(type)
    ? t(attributeLabelKey('submission_value'))
    : ''
})

const memberships = computed(() =>
  Object.entries(props.finding.submission_values || {})
)

function displayValue(value) {
  return formatFindingValue(value) || '—'
}

// The API words a candidate's origin itself (held in MDR, naming rules, this release),
// so it is the label as it stands; the first letter is raised to read as one.
function candidateLabel(candidate) {
  if (!candidate.source && props.finding.type === 'SPONSOR_NAME') {
    return t('StandardsImport.finding_detail_sponsor_name_set')
  }
  const source = candidate.source || ''
  return source.charAt(0).toUpperCase() + source.slice(1)
}

function collision(candidate) {
  return parseCollisionCandidate(candidate.value)
}

function sponsorUid(candidate) {
  return candidate.sponsor_term_uid || collision(candidate)?.sponsorUid || null
}

const CONFIDENCE_LEVELS = ['HIGH', 'MEDIUM', 'LOW', 'UNKNOWN']

function levelLabel(level) {
  const label = findingTypeLabel(level)
  return CONFIDENCE_LEVELS.includes(level)
    ? t('StandardsImport.finding_detail_confidence', { level: label })
    : label
}

function termSet(candidate) {
  const entries = Array.isArray(candidate.value)
    ? candidate.value
    : [candidate.value].filter(Boolean)
  return entries.map(parseTermSetEntry)
}
</script>
