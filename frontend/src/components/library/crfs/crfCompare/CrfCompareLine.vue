<template>
  <div class="line d-flex align-center" :class="stateClass">
    <template v-if="entry">
      <v-icon :icon="icon" size="x-small" class="mr-2" />
      <slot name="before" />
      <span>{{ entry.label }}</span>
      <slot name="after" />
    </template>
    <span v-else>&nbsp;</span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  line: { type: Object, required: true },
  side: { type: String, required: true },
  icon: { type: String, default: 'mdi-radiobox-blank' },
  ghost: { type: Boolean, default: false },
})

// Each side shows the other side's line as a ghost when it has none of its
// own. state is relative to the left cell: 'added' is left-only, 'missing'
// right-only. Left marks its own-only lines green and the right-only ones red;
// the right mirrors that.
const entry = computed(
  () =>
    props.line[props.side] ||
    props.line[props.side === 'left' ? 'right' : 'left']
)
const stateClass = computed(() => {
  if (props.line.state === 'changed') return 'line--changed'
  const ownOnly = props.side === 'left' ? 'added' : 'missing'
  const otherOnly = props.side === 'left' ? 'missing' : 'added'
  if (props.line.state === ownOnly) return 'line--added'
  if (props.line.state === otherOnly) return 'line--missing'
  return ''
})
</script>

<style scoped>
.line {
  min-height: 24px;
}
.line--added {
  color: rgb(var(--v-theme-success));
}
.line--changed {
  color: rgb(var(--v-theme-warning));
}
.line--missing {
  color: rgb(var(--v-theme-error));
}
</style>
