<template>
  <v-tooltip
    v-if="tooltip && name.length > tooltipLength"
    location="top"
    content-class="tooltip"
  >
    <template #activator="{ props }">
      <span v-bind="props">
        <div
          class="template-readonly"
          v-html="sanitizeHTML(getShortVersion())"
        />
      </span>
    </template>
    <span>
      <div
        class="template-readonly"
        v-html="sanitizeHTML(getFormattedParts())"
      />
    </span>
  </v-tooltip>
  <div
    v-else
    class="template-readonly"
    v-html="sanitizeHTML(getFormattedParts())"
  />
</template>

<script setup>
import { computed } from 'vue'
import { sanitizeHTML } from '@/utils/sanitize'

const props = defineProps({
  value: {
    type: Array,
    default: () => [],
  },
  // the name including the parameters
  name: {
    type: String,
    default: '',
  },
  prefix: {
    type: String,
    default: '[',
  },
  postfix: {
    type: String,
    default: ']',
  },
  showPrefixAndPostfix: {
    type: Boolean,
    default: true,
  },
  parameters: {
    type: Array,
    default: () => [],
  },
  editionMode: {
    type: Boolean,
    default: false,
  },
  defaultColor: {
    type: String,
    default: 'green',
  },
  tooltip: {
    type: Boolean,
    default: true,
  },
  tooltipLength: {
    type: Number,
    default: 200,
  },
})

const computedPostfix = computed(() => {
  return props.postfix === '' ||
    props.postfix === null ||
    props.postfix === undefined
    ? ' '
    : props.postfix
})

const nameParts = computed(() => {
  const nameArray = []
  let parameterIndex = 0

  let chars = ''
  for (const char of props.name) {
    if (char === props.prefix) {
      nameArray.push({
        isParameter: false,
        value: chars,
      })
      if (props.showPrefixAndPostfix) {
        chars = char
      } else {
        chars = ''
      }
    } else if (char === computedPostfix.value) {
      if (props.showPrefixAndPostfix) {
        chars += char
      }
      nameArray.push({
        isParameter: true,
        index: parameterIndex,
        value: chars,
      })
      parameterIndex++
      chars = ''
    } else {
      chars += char
    }
  }
  nameArray.push({
    isParameter: false,
    value: chars,
  })
  return nameArray
})

function getNamePartClass(namePart) {
  if (!namePart.isParameter) {
    return 'preview-text text-black'
  }
  if (props.editionMode && props.parameters[namePart.index]) {
    if (
      !props.parameters.length ||
      !props.parameters[namePart.index].selectedValues ||
      !props.parameters[namePart.index].selectedValues.length
    ) {
      return 'preview-parameter'
    }
    return 'preview-parameter--selected'
  }
  return `parameter--${props.defaultColor}`
}

function getFormattedParts() {
  let result = ''

  nameParts.value.forEach((namePart, index) => {
    if (namePart.isParameter) {
      result += `<span class="${getNamePartClass(namePart, index)}">${namePart.value}</span>`
    } else {
      result += namePart.value
    }
  })
  return result
}

function getShortVersion() {
  const long = getFormattedParts()
  let short = ''
  let length = 0
  while (
    short.replace(/<\/?[^>]+(>|$)/g, '').length <= props.tooltipLength &&
    length < long.length
  ) {
    short += long[length]
    length++
  }
  return short + '<l>...'
}
</script>

<style lang="scss">
.template-readonly {
  min-height: 30px;

  p {
    margin-bottom: 4px;
  }
}
.preview-parameter {
  color: rgb(var(--v-theme-orange));

  &--selected {
    color: rgb(var(--v-theme-green));
  }
}
.parameter {
  &--orange {
    color: rgb(var(--v-theme-orange));
  }
  &--green {
    color: rgb(var(--v-theme-green));
  }
  &--primary {
    color: rgb(var(--v-theme-primary));
  }
}
.param-dropdown {
  width: 160px;
  display: inline-block;
}
.tooltip {
  background-color: white;
  color: black;
  border: 1px solid #737373;
}
</style>
