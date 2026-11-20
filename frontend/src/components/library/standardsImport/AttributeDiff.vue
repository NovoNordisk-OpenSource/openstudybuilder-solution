<template>
  <!-- One attribute's before and after as a word-level diff: most of these values are
       long definitions where only a phrase moved. `side` picks which half to draw -
       both inline, or only what one side holds, for a two-column layout. -->
  <div class="diff-text">
    <span
      v-for="(segment, index) in shownSegments"
      :key="index"
      :class="segmentClass(segment)"
      >{{ segment.value }}</span
    >
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { diffWordsWithSpace } from 'diff'

const { t } = useI18n()

const props = defineProps({
  oldValue: {
    type: [String, Array, Boolean, Number],
    default: null,
  },
  newValue: {
    type: [String, Array, Boolean, Number],
    default: null,
  },
  side: {
    type: String,
    default: 'inline',
    validator: (value) => ['inline', 'old', 'new'].includes(value),
  },
})

// Values arrive as strings, booleans (`extensible`), lists (`synonyms`), or absent.
function formatValue(value) {
  if (Array.isArray(value)) {
    return value.length
      ? [...value].sort().join(', ')
      : t('StandardsImport.diff_empty_value')
  }
  if (typeof value === 'boolean') {
    return value
      ? t('StandardsImport.diff_true')
      : t('StandardsImport.diff_false')
  }
  if (value === null || value === undefined || value === '') {
    return t('StandardsImport.diff_empty_value')
  }
  return String(value)
}

// `diffWordsWithSpace` keeps whitespace as part of the segments, so the rendered
// diff reproduces the original spacing instead of collapsing it.
const segments = computed(() =>
  diffWordsWithSpace(formatValue(props.oldValue), formatValue(props.newValue))
)

// The old side has no use for what was added, nor the new side for what was removed.
const shownSegments = computed(() => {
  if (props.side === 'old') {
    return segments.value.filter((segment) => !segment.added)
  }
  if (props.side === 'new') {
    return segments.value.filter((segment) => !segment.removed)
  }
  return segments.value
})

function segmentClass(segment) {
  if (segment.removed) {
    return 'diff-removed text-red-darken-4 bg-red-lighten-4'
  }
  if (segment.added) {
    return 'diff-added text-green-darken-4 bg-green-lighten-4'
  }
  return ''
}
</script>

<style scoped>
.diff-text {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}
.diff-removed {
  text-decoration: line-through;
  border-radius: 2px;
}
.diff-added {
  border-radius: 2px;
}
</style>
