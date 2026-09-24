<template>
  <span v-if="!isContainer" class="json-primitive">
    <span v-if="keyName !== undefined" class="json-key">{{ formattedKey }}</span
    ><span v-if="keyName !== undefined">: </span
    ><span :class="primitiveClass">{{ formattedPrimitive }}</span
    ><span v-if="!isLast">,</span>
  </span>
  <details v-else ref="detailsEl" open class="json-details">
    <summary>
      <span v-if="keyName !== undefined" class="json-key">{{
        formattedKey
      }}</span
      ><span v-if="keyName !== undefined">: </span
      ><span class="json-bracket">{{ openBracket }}</span
      ><span class="json-meta">{{ summary }}</span
      ><span class="json-summary-tail"
        ><span class="json-bracket">{{ closeBracket }}</span
        ><span v-if="!isLast">,</span></span
      >
    </summary>
    <div class="json-children">
      <div class="json-gutter" @click="collapse" />
      <div class="json-content">
        <JsonNode
          v-for="(child, idx) in entries"
          :key="child.key"
          :value="child.value"
          :key-name="isArray ? undefined : child.key"
          :is-last="idx === entries.length - 1"
          :depth="depth + 1"
        />
      </div>
    </div>
    <div class="json-close">
      <span class="json-bracket">{{ closeBracket }}</span
      ><span v-if="!isLast">,</span>
    </div>
  </details>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  value: { type: [String, Number, Boolean, Array, Object], default: null },
  keyName: { type: [String, Number], default: undefined },
  isLast: { type: Boolean, default: true },
  depth: { type: Number, default: 0 },
})

const detailsEl = ref(null)

function collapse() {
  if (detailsEl.value) detailsEl.value.open = false
}

const isArray = computed(() => Array.isArray(props.value))
const isObject = computed(
  () =>
    props.value !== null && typeof props.value === 'object' && !isArray.value
)
const entries = computed(() => {
  if (isArray.value) return props.value.map((v, i) => ({ key: i, value: v }))
  if (isObject.value)
    return Object.entries(props.value).map(([k, v]) => ({ key: k, value: v }))
  return []
})

// Empty arrays/objects render inline as `[]` / `{}` — nothing to expand,
// so they take the primitive path instead of a <details> with no children.
const isContainer = computed(
  () => (isArray.value || isObject.value) && entries.value.length > 0
)

const openBracket = computed(() => (isArray.value ? '[' : '{'))
const closeBracket = computed(() => (isArray.value ? ']' : '}'))
const summary = computed(() => {
  const n = entries.value.length
  if (n === 0) return ''
  return ` ${n} ${isArray.value ? 'item' : 'key'}${n === 1 ? '' : 's'} `
})

const primitiveClass = computed(() => {
  if (props.value === null) return 'json-null'
  if (typeof props.value === 'string') return 'json-string'
  if (typeof props.value === 'number') return 'json-number'
  if (typeof props.value === 'boolean') return 'json-boolean'
  if (typeof props.value === 'object') return 'json-bracket'
  return ''
})
const formattedPrimitive = computed(() => {
  if (props.value === null) return 'null'
  // JSON.stringify handles quotes/backslashes/control chars correctly.
  if (typeof props.value === 'string') return JSON.stringify(props.value)
  if (isArray.value) return '[]'
  if (isObject.value) return '{}'
  return String(props.value)
})
// Only object keys are rendered (array indices pass keyName=undefined).
// JSON.stringify quotes and escapes correctly.
const formattedKey = computed(() => JSON.stringify(props.keyName))
</script>

<style scoped>
.json-details {
  margin-left: 0;
}
.json-details > summary {
  cursor: pointer;
  list-style: none;
  user-select: none;
  padding: 1px 4px;
  border-radius: 3px;
}
.json-details > summary:hover {
  background-color: #f4f5f8;
}
.json-details > summary::-webkit-details-marker {
  display: none;
}
.json-details > summary::before {
  content: '▶';
  display: inline-block;
  width: 1em;
  font-size: 0.65em;
  color: #939aa7;
  transition: transform 0.1s;
}
.json-details[open] > summary::before {
  transform: rotate(90deg);
}
.json-children {
  display: flex;
  margin-left: 1.25em;
}
.json-gutter {
  flex: 0 0 auto;
  width: 0.75em;
  margin-right: 0.5em;
  cursor: pointer;
  border-left: 1px solid #e9eaed;
  align-self: stretch;
}
.json-gutter:hover {
  border-left-color: #001965;
  background: linear-gradient(to right, rgba(0, 25, 101, 0.06), transparent);
}
.json-content {
  flex: 1 1 auto;
  min-width: 0;
}
.json-close {
  margin-left: 0.85em;
}
/* When expanded, the closing bracket + comma live in .json-close on its
   own line; hide the inline tail in the summary so it doesn't render twice.
   When collapsed, native <details> hides .json-close automatically. */
.json-details[open] > summary .json-summary-tail {
  display: none;
}
.json-primitive {
  display: block;
  padding-left: 1em;
}
.json-key {
  color: #001965;
  font-weight: 500;
}
.json-string {
  color: #2a918b;
  white-space: pre-wrap;
  word-break: break-word;
}
.json-number {
  color: #c44836;
}
.json-boolean {
  color: #005bd2;
  font-weight: 500;
}
.json-null {
  color: #939aa7;
  font-style: italic;
}
.json-bracket {
  color: #747474;
}
.json-meta {
  color: #939aa7;
  font-style: italic;
  font-size: 0.85em;
}
</style>
