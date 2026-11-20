<template>
  <template v-for="def in defs" :key="def.name">
    <template v-if="def.kind === 'list'">
      <div v-if="!row.detail?.lists[def.name]?.length" class="extra mt-1">
        {{ $t(`CRFCompare.attributes.${def.name}`) }}: {{ EMPTY }}
      </div>
      <div
        v-for="(line, index) in row.detail?.lists[def.name] || []"
        :key="`${def.name}${index}`"
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
              {{ $t(`CRFCompare.attributes.${def.name}`) }}:
            </span>
          </template>
        </CrfCompareLine>
      </div>
    </template>
    <div v-else class="extra mt-1" :class="diffClass(def.name)">
      {{ $t(`CRFCompare.attributes.${def.name}`) }}:
      {{ valueOf(def) || EMPTY }}
    </div>
  </template>
</template>

<script setup>
import { computed } from 'vue'
import { ATTRIBUTES, attributeKey } from '@/utils/crfCompare'
import CrfCompareLine from '@/components/library/crfs/crfCompare/CrfCompareLine.vue'

const props = defineProps({
  level: { type: String, required: true },
  row: { type: Object, required: true },
  side: { type: String, required: true },
  enabledFields: { type: Set, required: true },
  language: { type: String, default: 'en' },
  isGhost: { type: Boolean, default: false },
})

const EMPTY = '-'

const defs = computed(() =>
  ATTRIBUTES[props.level].filter((def) =>
    props.enabledFields.has(attributeKey(props.level, def.name))
  )
)

// A side with no element of its own shows the other side's as a ghost.
const element = computed(
  () =>
    props.row[props.side] || props.row[props.side === 'left' ? 'right' : 'left']
)

function read(candidate, def) {
  const value = candidate?.attrs?.[def.name]
  return def.kind === 'text' ? value?.[props.language] || '' : value || ''
}

function valueOf(def) {
  return read(element.value, def)
}

function diffClass(name) {
  return props.side === 'left' &&
    !props.isGhost &&
    props.row.detail?.scalars.has(name)
    ? 'diff-value'
    : ''
}
</script>

<style scoped>
.extra {
  font-size: 0.8125rem;
  white-space: pre-wrap;
}
.diff-value {
  color: rgb(var(--v-theme-warning));
}
</style>
