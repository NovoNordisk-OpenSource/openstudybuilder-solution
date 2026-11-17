<template>
  <!-- Form attributes -->
  <div
    v-if="row.kind === 'form'"
    class="cell cell--form"
    :class="statusClass"
    :data-cy="`crf-compare-${side}-form-row`"
  >
    <div v-if="showLabel" class="status-label mb-1" :class="labelColorClass">
      <v-icon :icon="labelIcon" size="small" class="mr-1" />{{ labelText }}
    </div>
    <div class="d-flex align-center">
      <v-icon icon="mdi-alpha-f-circle" color="crfForm" class="mr-2" />
      <span class="font-weight-medium" :class="diffClass('name')">{{
        element.name
      }}</span>
    </div>
    <CrfCompareAttributes
      level="form"
      :row="row"
      :side="side"
      :enabled-fields="enabledFields"
      :language="language"
    />
  </div>

  <!-- Collection form header -->
  <div
    v-else-if="row.kind === 'collectionForm'"
    class="cell cell--collection-form"
    :class="[statusClass, { 'cell--blank': !element }]"
    :data-cy="`crf-compare-${side}-collection-form`"
  >
    <template v-if="element">
      <div class="d-flex align-center">
        <v-icon icon="mdi-alpha-f-circle" color="crfForm" class="mr-2" />
        <span class="font-weight-medium">{{ element.name }}</span>
        <v-chip size="x-small" label class="ml-2">
          {{ $t('CRFCompare.version') }} {{ element.version }}
        </v-chip>
        <v-spacer />
        <span v-if="showLabel" class="status-label" :class="labelColorClass">
          <v-icon :icon="labelIcon" size="small" class="mr-1" />{{ labelText }}
        </span>
      </div>
      <div v-if="orderDiffers" class="extra mt-1" :class="diffClass('order')">
        <v-icon icon="mdi-swap-vertical" size="small" class="mr-1" />{{
          $t('CRFCompare.order_differs')
        }}
      </div>
    </template>
  </div>

  <!-- Group header -->
  <div
    v-else-if="row.kind === 'group'"
    class="cell cell--group"
    :class="[statusClass, { 'cell--blank': !element }]"
  >
    <template v-if="element">
      <div class="d-flex align-center">
        <v-btn
          :icon="collapsed ? 'mdi-chevron-down' : 'mdi-chevron-up'"
          size="x-small"
          variant="text"
          class="mr-1"
          :title="
            collapsed
              ? $t('CRFCompare.expand_group')
              : $t('CRFCompare.collapse_group')
          "
          @click="$emit('toggle')"
        />
        <v-icon icon="mdi-alpha-g-circle" color="crfGroup" class="mr-2" />
        <span class="font-weight-medium" :class="diffClass('name')">
          {{ element.name }}
        </span>
        <span
          v-if="element.mandatory"
          class="ml-1"
          :class="diffClass('mandatory')"
          :title="$t('CRFCompare.mandatory')"
          >*</span
        >
        <v-spacer />
        <span v-if="showLabel" class="status-label" :class="labelColorClass">
          <v-icon :icon="labelIcon" size="small" class="mr-1" />{{ labelText }}
        </span>
      </div>
      <div v-if="orderDiffers" class="extra mt-1" :class="diffClass('order')">
        <v-icon icon="mdi-swap-vertical" size="small" class="mr-1" />{{
          $t('CRFCompare.order_differs')
        }}
      </div>
      <div
        v-if="enabledFields.has('keys')"
        class="extra mt-1"
        :class="diffClass('keys')"
      >
        {{ $t('CRFCompare.keys') }}: {{ element.keys }}
      </div>
      <CrfCompareAttributes
        level="group"
        :row="row"
        :side="side"
        :enabled-fields="enabledFields"
        :language="language"
        :is-ghost="isGhost"
      />
    </template>
  </div>

  <!-- Nothing on this side: keeps the rows aligned -->
  <div v-else-if="!element" class="cell cell--blank" :class="lastClass" />

  <!-- Item -->
  <div
    v-else
    class="cell cell--item"
    :class="[statusClass, lastClass]"
    :data-cy="`crf-compare-${side}-item`"
  >
    <div v-if="showLabel" class="status-label mb-1" :class="labelColorClass">
      <v-icon :icon="labelIcon" size="small" class="mr-1" />{{ labelText }}
    </div>

    <div class="d-flex align-center">
      <v-icon icon="mdi-alpha-i-circle" color="crfItem" class="mr-2" />
      <span
        class="item-name"
        :class="[{ 'font-weight-bold': hasOptions }, diffClass('name')]"
      >
        {{ element.name }}
      </span>
      <span
        v-if="element.mandatory"
        class="ml-1"
        :class="diffClass('mandatory')"
        :title="$t('CRFCompare.mandatory')"
        >*</span
      >
    </div>

    <div
      v-if="element.question[language]"
      class="text-caption text-medium-emphasis mt-1"
      :class="diffClass('question')"
    >
      {{ element.question[language] }}
    </div>

    <div v-if="!hasOptions" class="field-box mt-2" :class="diffClass('prompt')">
      {{ element.prompt }}
    </div>

    <div v-for="(line, index) in lines.terms" :key="`t${index}`" class="mt-1">
      <CrfCompareLine :line="line" :side="side" :ghost="isGhost">
        <template v-if="enabledFields.has('sourceValue')" #after>
          <span class="source-value" :class="diffClass('sourceValue')">
            {{ lineEntry(line)?.sourceValue }}
          </span>
        </template>
      </CrfCompareLine>
    </div>
    <div v-for="(line, index) in lines.units" :key="`u${index}`" class="mt-1">
      <CrfCompareLine :line="line" :side="side" :ghost="isGhost" />
    </div>

    <div
      v-if="element.datatype"
      class="text-caption text-medium-emphasis mt-2"
      :class="[diffClass('datatype'), diffClass('length')]"
    >
      {{ element.datatype
      }}<template v-if="element.length"> ({{ element.length }})</template>
    </div>

    <div
      v-for="(line, index) in lines.activityInstances"
      :key="`a${index}`"
      class="mt-1"
    >
      <CrfCompareLine
        :line="line"
        :side="side"
        :ghost="isGhost"
        icon="mdi-link-variant"
      >
        <template #before>
          <span class="text-medium-emphasis mr-1">
            {{ $t('CRFCompare.activity_instance') }}:
          </span>
        </template>
      </CrfCompareLine>
    </div>
    <div
      v-if="enabledFields.has('sdtm') && (element.sdtm || otherHas('sdtm'))"
      class="extra mt-1"
      :class="diffClass('sdtm')"
    >
      {{ $t('CRFCompare.sdtm') }}: {{ element.sdtm }}
    </div>
    <div
      v-if="enabledFields.has('keys')"
      class="extra mt-1"
      :class="diffClass('keys')"
    >
      {{ $t('CRFCompare.keys') }}: {{ element.keys }}
    </div>
    <div
      v-if="enabledFields.has('designNotes')"
      class="extra mt-1"
      :class="diffClass('designNotes')"
    >
      {{ $t('CRFCompare.design_notes') }}:
      {{ element.designNotes[language] }}
    </div>
    <div
      v-if="enabledFields.has('completionInstructions')"
      class="extra mt-1"
      :class="diffClass('completionInstructions')"
    >
      {{ $t('CRFCompare.completion_instructions') }}:
      {{ element.completionInstructions[language] }}
    </div>
    <div v-if="orderDiffers" class="extra mt-1" :class="diffClass('order')">
      <v-icon icon="mdi-swap-vertical" size="small" class="mr-1" />{{
        $t('CRFCompare.order_differs')
      }}
    </div>
    <CrfCompareAttributes
      level="item"
      :row="row"
      :side="side"
      :enabled-fields="enabledFields"
      :language="language"
      :is-ghost="isGhost"
    />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import CrfCompareAttributes from '@/components/library/crfs/crfCompare/CrfCompareAttributes.vue'
import CrfCompareLine from '@/components/library/crfs/crfCompare/CrfCompareLine.vue'

const props = defineProps({
  row: { type: Object, required: true },
  side: { type: String, required: true },
  enabledFields: { type: Set, required: true },
  language: { type: String, default: 'en' },
  collapsed: { type: Boolean, default: false },
  lastInGroup: { type: Boolean, default: false },
})
defineEmits(['toggle'])

const { t } = useI18n()

const STATUS_PRESENTATION = {
  added: { icon: 'mdi-plus-circle-outline', color: 'success' },
  removed: { icon: 'mdi-alert-outline', color: 'error', cls: 'missing' },
  missing: { icon: 'mdi-alert-outline', color: 'error' },
  changed: { icon: 'mdi-alert-circle-outline', color: 'warning' },
}

// Each side shows the other side's element as a ghost when it has none of its
// own: left-only rows read "Removed" on the right, right-only rows "Missing"
// on the left.
const otherSide = computed(() => (props.side === 'left' ? 'right' : 'left'))
const ownElement = computed(() => props.row[props.side])
const element = computed(() => ownElement.value || props.row[otherSide.value])
const isGhost = computed(() => !ownElement.value && !!element.value)

// Left shows the row's status; the right shows its mirror image.
const effectiveStatus = computed(() => {
  if (props.side === 'left') return props.row.status
  if (props.row.status === 'added') return 'removed'
  if (props.row.status === 'missing') return 'added'
  return 'same'
})
const presentation = computed(() => STATUS_PRESENTATION[effectiveStatus.value])
const showLabel = computed(() => !!presentation.value)
const labelIcon = computed(() => presentation.value?.icon)
const labelColorClass = computed(() => `text-${presentation.value?.color}`)
const labelText = computed(() =>
  t(
    `CRFCompare.${effectiveStatus.value === 'changed' ? 'difference' : effectiveStatus.value}`
  )
)
const statusClass = computed(() => {
  const status = effectiveStatus.value
  if (status === 'same') return ''
  return `cell--${STATUS_PRESENTATION[status]?.cls || status}`
})
const orderDiffers = computed(() => !!props.row.detail?.scalars.has('order'))
const lastClass = computed(() => ({ 'cell--last': props.lastInGroup }))

const lines = computed(
  () =>
    props.row.detail?.lists || { terms: [], units: [], activityInstances: [] }
)
const hasOptions = computed(() => lines.value.terms.length > 0)

function lineEntry(line) {
  return line[props.side] || line[otherSide.value]
}

function diffClass(field) {
  return props.side === 'left' &&
    !isGhost.value &&
    props.row.detail?.scalars.has(field)
    ? 'diff-value'
    : ''
}

function otherHas(field) {
  const other = props.row[otherSide.value]
  return !!other?.[field]
}
</script>

<style scoped>
.cell {
  padding: 12px 16px;
  border-inline: 1px solid rgb(var(--v-theme-dfltBackgroundLight1));
  min-width: 0;
  overflow-wrap: anywhere;
}
.cell--item {
  border-top: 1px solid rgb(var(--v-theme-dfltBackgroundLight1));
}
.cell--form {
  margin-bottom: 8px;
  border: 1px solid rgb(var(--v-theme-dfltBackgroundLight1));
  border-radius: 8px;
}
.cell--collection-form {
  padding-block: 10px;
  margin-top: 24px;
  border: 1px solid rgb(var(--v-theme-dfltBackgroundLight1));
  border-radius: 8px;
}
.cell--collection-form.cell--blank {
  border-color: transparent;
}
.cell--group {
  padding-block: 8px;
  margin-top: 16px;
  border: 1px solid rgb(var(--v-theme-dfltBackgroundLight1));
  border-radius: 8px 8px 0 0;
  background-color: rgb(var(--v-theme-dfltBackgroundLight1));
}
.cell--blank {
  background-color: transparent;
}
.cell--group.cell--blank {
  border-color: transparent;
}
.cell--last {
  border-bottom: 1px solid rgb(var(--v-theme-dfltBackgroundLight1));
  border-radius: 0 0 8px 8px;
}
.cell--added {
  background-color: rgba(var(--v-theme-success), 0.1);
}
.cell--missing {
  background-color: rgba(var(--v-theme-error), 0.08);
}
.cell--changed {
  background-color: rgba(var(--v-theme-warning), 0.12);
}
.status-label {
  font-size: 0.8125rem;
  display: inline-flex;
  align-items: center;
}
.field-box {
  min-height: 40px;
  padding: 8px 12px;
  border: 1px solid rgba(var(--v-theme-on-surface), 0.3);
  border-radius: 8px;
  color: rgba(var(--v-theme-on-surface), 0.5);
  background-color: rgb(var(--v-theme-surface));
}
.diff-value {
  color: rgb(var(--v-theme-warning));
}
.extra {
  font-size: 0.8125rem;
  white-space: pre-wrap;
}
.source-value {
  margin-left: 6px;
  font-size: 0.75rem;
  opacity: 0.7;
}
</style>
