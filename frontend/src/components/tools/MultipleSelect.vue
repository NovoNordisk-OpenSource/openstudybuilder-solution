<template>
  <v-autocomplete
    v-model:search="search"
    v-bind="$attrs"
    v-model="value"
    multiple
    data-cy="autocomplete-input-field"
    clearable
    bg-color="white"
    color="nnBaseBlue"
    base-color="nnBaseBlue"
    hide-no-data
    @change="search = ''"
  >
    <template v-if="shorterPreview" #selection="{ index }">
      <div v-if="index === 0">
        <span>{{
          value[0].name.length > 25
            ? value[0].name.replace(/[<>]/g, '').substring(0, 25) + '...'
            : value[0].name.replace(/[<>]/g, '')
        }}</span>
      </div>
      <span v-if="index === 1" class="text-grey caption mr-1">
        (+{{ value.length - 1 }})
      </span>
    </template>
  </v-autocomplete>
</template>

<script>
export default {
  props: {
    initialData: {
      type: Array,
      default: () => [],
    },
    shorterPreview: {
      type: Boolean,
      default: false,
    },
    modelValue: {
      type: Array,
      default: () => [],
    },
  },
  emits: ['update:modelValue'],
  data() {
    return {
      search: '',
    }
  },
  computed: {
    value: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      },
    },
  },
}
</script>
