<template>
  <SimpleFormDialog
    ref="dialogRef"
    :title="$t('StandardsImport.resolve_inconsistency')"
    :open="open"
    @close="$emit('close')"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-select
          v-model="strategy"
          :label="$t('StandardsImport.strategy')"
          :items="allowedStrategies"
          :rules="[formRules.required]"
          data-cy="standards-import-strategy-select"
        >
          <template #item="{ item, props }">
            <v-list-item v-bind="props">
              <template #append>
                <EnumInfoTooltip enum-key="resolution_strategy" :value="item" />
              </template>
            </v-list-item>
          </template>
        </v-select>
        <v-select
          v-if="needsCatalogue"
          v-model="catalogue"
          :label="$t('StandardsImport.catalogue')"
          :items="catalogueOptions"
          :rules="[formRules.required]"
        />
        <v-select
          v-if="strategy === 'PICK_VALUE'"
          v-model="value"
          :label="$t('StandardsImport.value')"
          :items="valueOptions"
          item-title="title"
          item-value="value"
          :rules="[formRules.required]"
        />
        <v-text-field
          v-if="strategy === 'CUSTOM_VALUE'"
          v-model="value"
          :label="$t('StandardsImport.value')"
          :rules="[formRules.required]"
        />
        <!-- A finding about one term already names it; only a codelist-wide one needs
             to be told which term to drop. -->
        <v-text-field
          v-if="
            strategy === 'DROP_TERM_FROM_CODELIST' &&
            !props.item?.related_concept_id
          "
          v-model="value"
          :label="$t('StandardsImport.term_to_drop')"
          :rules="[formRules.required]"
        />
        <!-- With a single sponsor term the API picks it itself, so asking only makes
             sense when the CDISC term collides with several. -->
        <v-select
          v-if="
            DISPLACING_STRATEGIES.includes(strategy) &&
            sponsorTermOptions.length > 1
          "
          v-model="value"
          :label="$t('StandardsImport.sponsor_term_uid')"
          :items="sponsorTermOptions"
          :rules="[formRules.required]"
          data-cy="standards-import-sponsor-term-select"
        />
        <!-- Said up front rather than left to the refusal: the API checks again live
             and turns the decision down while the sponsor term is still in use. -->
        <v-alert
          v-if="sponsorTermInUse"
          type="warning"
          variant="tonal"
          density="compact"
          class="alert-bordered mb-4"
          data-cy="standards-import-sponsor-term-in-use"
          :text="
            $t('StandardsImport.sponsor_term_in_use', props.item.usage_count)
          "
        />
        <v-text-field
          v-if="needsPattern"
          v-model="pattern"
          :label="$t('StandardsImport.pattern')"
          :rules="[formRules.required]"
        />
        <v-text-field
          v-if="strategy === 'REGEX_REPLACE'"
          v-model="value"
          :label="$t('StandardsImport.replacement')"
        />
        <template v-if="needsSteps">
          <div class="text-subtitle-2 mt-2">
            {{ $t('StandardsImport.steps') }}
          </div>
          <v-row
            v-for="(step, index) in steps"
            :key="index"
            dense
            align="center"
          >
            <v-col cols="5">
              <v-text-field
                v-model="step.pattern"
                :label="$t('StandardsImport.pattern')"
                :rules="[formRules.required]"
              />
            </v-col>
            <v-col cols="5">
              <v-text-field
                v-model="step.replacement"
                :label="$t('StandardsImport.replacement')"
              />
            </v-col>
            <v-col cols="2">
              <v-btn
                icon="mdi-delete-outline"
                variant="text"
                :disabled="steps.length === 1"
                :aria-label="$t('StandardsImport.remove_step')"
                @click="steps.splice(index, 1)"
              />
            </v-col>
          </v-row>
          <v-btn
            variant="text"
            prepend-icon="mdi-plus"
            @click="steps.push({ pattern: '', replacement: '' })"
          >
            {{ $t('StandardsImport.add_step') }}
          </v-btn>
        </template>
        <v-checkbox
          v-if="strategy === 'USE_SUBMISSION_VALUE'"
          v-model="titleCase"
          :label="$t('StandardsImport.title_case')"
          hide-details
        />
        <v-textarea
          v-model="note"
          :label="$t('StandardsImport.note')"
          rows="2"
        />
        <v-checkbox
          v-if="canSaveAsRule"
          v-model="saveAsRule"
          :label="$t('StandardsImport.save_as_rule')"
          hide-details
        />
        <v-select
          v-if="canSaveAsRule && saveAsRule"
          v-model="ruleScope"
          :label="$t('StandardsImport.rule_scope')"
          :items="RULE_SCOPES"
          :rules="[formRules.required]"
        >
          <template #item="{ item, props }">
            <v-list-item v-bind="props">
              <template #append>
                <EnumInfoTooltip enum-key="rule_scope" :value="item" />
              </template>
            </v-list-item>
          </template>
        </v-select>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import EnumInfoTooltip from '@/components/tools/EnumInfoTooltip.vue'
import inconsistenciesApi from '@/api/standardsImport/inconsistencies'
import { useStandardsImportResolutionStrategiesStore } from '@/stores/standardsImportResolutionStrategies'

const { t } = useI18n()
const formRules = inject('formRules')
const notificationHub = inject('notificationHub')
const resolutionStrategiesStore = useStandardsImportResolutionStrategiesStore()

const RULE_SCOPES = ['OCCURRENCE', 'CONCEPT', 'PROPERTY', 'GLOBAL']

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  item: {
    type: Object,
    default: () => ({}),
  },
})
const emit = defineEmits(['close', 'resolved'])

const dialogRef = ref()
const strategy = ref(null)
const catalogue = ref(null)
const value = ref(null)
const pattern = ref(null)
const steps = ref([{ pattern: '', replacement: '' }])
const titleCase = ref(false)
const note = ref('')
const saveAsRule = ref(false)
const ruleScope = ref('OCCURRENCE')

const allowedStrategies = computed(() =>
  resolutionStrategiesStore.getAllowedStrategies(
    props.item?.type,
    props.item?.match_tier
  )
)

// The strategies that take the sponsor term out from under whatever refers to it - the
// API's `NEEDS_AN_UNUSED_TERM`. `usage_count` is as of the last assessment.
const DISPLACING_STRATEGIES = [
  'REMOVE_SPONSOR_FROM_CODELIST',
  'RETIRE_SPONSOR_TERM',
]
const sponsorTermInUse = computed(
  () =>
    DISPLACING_STRATEGIES.includes(strategy.value) &&
    props.item?.type === 'SPONSOR_TERM_DUPLICATE' &&
    props.item?.usage_count > 0
)

// One entry per sponsor term: a term can collide on more than one field.
const sponsorTermOptions = computed(() => {
  const byUid = new Map()
  for (const candidate of props.item?.candidates || []) {
    if (candidate.sponsor_term_uid && !byUid.has(candidate.sponsor_term_uid)) {
      byUid.set(candidate.sponsor_term_uid, {
        value: candidate.sponsor_term_uid,
        title: candidate.value,
      })
    }
  }
  return [...byUid.values()]
})

const selectedStrategyDescription = computed(() =>
  resolutionStrategiesStore.getStrategyDescription(strategy.value)
)
const needsCatalogue = computed(() =>
  (selectedStrategyDescription.value?.needs || []).includes('catalogue')
)
const needsPattern = computed(() =>
  (selectedStrategyDescription.value?.needs || []).includes('pattern')
)
const needsSteps = computed(() =>
  (selectedStrategyDescription.value?.needs || []).includes('steps')
)
const canSaveAsRule = computed(
  () => selectedStrategyDescription.value?.can_save_as_rule ?? true
)

// A candidate value can come from several catalogues at once, so flatten the
// lists and de-duplicate rather than reading a single `catalogue` field.
const catalogueOptions = computed(() => [
  ...new Set(
    (props.item?.candidates || []).flatMap(
      (candidate) => candidate.catalogues || []
    )
  ),
])
const valueOptions = computed(() =>
  (props.item?.candidates || []).map((candidate) => ({
    value: candidate.value,
    title: candidate.source
      ? `${candidate.value} (${candidate.source})`
      : `${candidate.value} (${(candidate.catalogues || []).join(', ')})`,
  }))
)

watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      resolutionStrategiesStore.fetchResolutionStrategies()
      strategy.value = null
      catalogue.value = null
      value.value = null
      pattern.value = null
      steps.value = [{ pattern: '', replacement: '' }]
      titleCase.value = false
      note.value = ''
      saveAsRule.value = false
      ruleScope.value = 'OCCURRENCE'
    }
  }
)

// A value typed for one strategy would otherwise be sent, unseen, with the next.
watch(strategy, () => {
  value.value = null
})

watch(canSaveAsRule, (allowed) => {
  if (!allowed) {
    saveAsRule.value = false
  }
})

function submit() {
  const data = { strategy: strategy.value, note: note.value }
  if (needsCatalogue.value) {
    data.catalogue = catalogue.value
  }
  if (
    strategy.value === 'PICK_VALUE' ||
    strategy.value === 'CUSTOM_VALUE' ||
    strategy.value === 'DROP_TERM_FROM_CODELIST' ||
    strategy.value === 'REMOVE_SPONSOR_FROM_CODELIST' ||
    strategy.value === 'RETIRE_SPONSOR_TERM' ||
    strategy.value === 'REGEX_REPLACE'
  ) {
    data.value = value.value
  }
  if (needsPattern.value) {
    data.pattern = pattern.value
  }
  if (needsSteps.value) {
    data.steps = steps.value.filter((step) => step.pattern)
  }
  if (strategy.value === 'USE_SUBMISSION_VALUE') {
    data.title_case = titleCase.value
  }
  if (canSaveAsRule.value && saveAsRule.value) {
    data.save_as_rule = true
    data.rule_scope = ruleScope.value
  }
  inconsistenciesApi
    .resolve(props.item.uid, data)
    .then((response) => {
      notificationHub.add({
        type: 'success',
        msg: t('StandardsImport.resolution_success'),
      })
      emit('resolved', response.data)
      emit('close')
    })
    .catch(() => {
      notificationHub.add({
        type: 'error',
        msg: t('StandardsImport.resolution_error'),
      })
      dialogRef.value.working = false
    })
}
</script>
