<template>
  <div>
    <div class="mt-2 mb-8">
      <div class="mb-2 text-secondary text-h6">
        <template v-if="previewText">
          {{ previewText }}
        </template>
        <template v-else>
          {{ $t('ParameterValueSelector.preview') }}
        </template>
      </div>
      <v-card flat class="bg-parameterBackground">
        <v-card-text>
          <NNParameterHighlighter
            :name="namePreview"
            :show-prefix-and-postfix="false"
            :parameters="parameters"
            edition-mode
            :tooltip="false"
          />
        </v-card-text>
      </v-card>
    </div>
    <div v-if="stacked" :class="color">
      <v-row
        v-for="(parameter, index) in parameters"
        :key="index"
        no-gutters
        density="compact"
        cols="3"
      >
        <v-row class="align-start">
          <v-col cols="10">
            <v-text-field
              v-if="parameter.name === 'NumericValue'"
              v-model="parameter.selectedValues"
              :label="parameter.name"
              :disabled="disabled || parameter.skip"
              type="number"
              :rules="
                !loadParameterValuesFromTemplate
                  ? [
                      (value) =>
                        formRules.requiredIfNotNA(value, parameter.skip),
                    ]
                  : []
              "
              @input="update"
            />
            <v-textarea
              v-else-if="parameter.name === 'TextValue'"
              v-model="parameter.selectedValues"
              :label="parameter.name"
              :disabled="disabled || parameter.skip"
              rows="1"
              auto-grow
              :rules="
                !loadParameterValuesFromTemplate
                  ? [
                      (value) =>
                        formRules.requiredIfNotNA(value, parameter.skip),
                    ]
                  : []
              "
              @input="update"
            />
            <MultipleSelect
              v-else
              v-model="parameter.selectedValues"
              :label="parameter.name"
              :items="parameter.terms"
              :item-title="cleanItemName"
              return-object
              :disabled="disabled || parameter.skip"
              shorter-preview
              :rules="
                !loadParameterValuesFromTemplate
                  ? [
                      (value) =>
                        formRules.requiredIfNotNA(value, parameter.skip),
                    ]
                  : []
              "
              @input="update"
            />
          </v-col>
          <v-col cols="2">
            <v-btn
              icon
              class="ml-4"
              :disabled="disabled"
              variant="text"
              @click="clearSelection(parameter)"
            >
              <v-icon v-if="!parameter.skip"> mdi-eye-outline </v-icon>
              <v-icon v-else> mdi-eye-off-outline </v-icon>
            </v-btn>
          </v-col>
        </v-row>
        <v-row
          v-if="
            parameter.selectedValues &&
            parameter.selectedValues.length > 1 &&
            parameter.name !== 'NumericValue' &&
            parameter.name !== 'TextValue'
          "
        >
          <v-col cols="8" class="pl-2">
            <v-select
              v-model="parameter.selectedSeparator"
              :label="$t('ParameterValueSelector.separator')"
              :items="separators"
              density="compact"
              clearable
              :rules="[formRules.required]"
              :disabled="parameter.skip"
              @input="update"
            />
          </v-col>
        </v-row>
      </v-row>
    </div>
    <div v-else :class="color">
      <v-row>
        <v-col
          v-for="(parameter, index) in parameters"
          :key="index"
          no-gutters
          density="compact"
          cols="3"
        >
          <v-row class="align-start">
            <v-col cols="10">
              <v-text-field
                v-if="parameter.name === 'NumericValue'"
                v-model="parameter.selectedValues"
                :label="parameter.name"
                :disabled="parameter.skip"
                type="number"
                density="compact"
                :rules="
                  !loadParameterValuesFromTemplate
                    ? [
                        (value) =>
                          formRules.requiredIfNotNA(value, parameter.skip),
                      ]
                    : []
                "
                @input="update"
              />
              <v-textarea
                v-else-if="parameter.name === 'TextValue'"
                v-model="parameter.selectedValues"
                :label="parameter.name"
                :disabled="parameters[index].skip"
                :rows="1"
                density="compact"
                auto-grow
                :rules="
                  !loadParameterValuesFromTemplate
                    ? [
                        (value) =>
                          formRules.requiredIfNotNA(value, parameter.skip),
                      ]
                    : []
                "
                @input="update"
              />
              <MultipleSelect
                v-else
                v-model="parameter.selectedValues"
                :data-cy="parameter.name"
                :label="parameter.name"
                :items="parameter.terms"
                :item-title="cleanItemName"
                return-object
                :disabled="parameter.skip"
                shorter-preview
                :rules="
                  !loadParameterValuesFromTemplate
                    ? [
                        (value) =>
                          formRules.requiredIfNotNA(value, parameter.skip),
                      ]
                    : []
                "
                @input="update"
              />
            </v-col>
            <v-col cols="2">
              <v-btn
                icon
                class="ml-n4"
                :title="$t('ParameterValueSelector.na_tooltip')"
                variant="text"
                @click="clearSelection(parameter)"
              >
                <v-icon v-if="!parameter.skip"> mdi-eye-outline </v-icon>
                <v-icon v-else> mdi-eye-off-outline </v-icon>
              </v-btn>
            </v-col>
          </v-row>
          <v-row
            v-if="
              parameter.selectedValues &&
              parameter.selectedValues.length > 1 &&
              parameter.name !== 'NumericValue' &&
              parameter.name !== 'TextValue'
            "
          >
            <v-col cols="8" class="pl-2">
              <v-select
                v-model="parameter.selectedSeparator"
                :label="$t('ParameterValueSelector.separator')"
                :items="separators"
                density="compact"
                clearable
                :disabled="parameter.skip"
                :rules="[formRules.required]"
                @input="update"
              />
            </v-col>
          </v-row>
        </v-col>
      </v-row>
    </div>

    <template v-if="withUnformattedVersion">
      <p class="text-secondary text-h6">
        {{ unformattedTextLabel }}
        <v-tooltip
          v-if="maxTemplateLength && namePlainPreview.length > 200"
          location="bottom"
        >
          <template #activator="{ props }">
            <v-badge
              v-bind="props"
              color="warning"
              icon="mdi-exclamation"
              bordered
              inline
            />
          </template>
          <span>{{
            $t('EligibilityCriteriaTable.criteria_length_warning')
          }}</span>
        </v-tooltip>
      </p>
      <div class="pa-4 bg-parameterBackground">
        {{ namePlainPreview }}
      </div>
    </template>
  </div>
</template>

<script>
import constants from '@/constants/parameters'
import templateParameters from '@/utils/templateParameters'
import MultipleSelect from '@/components/tools/MultipleSelect.vue'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import templateParameterTypes from '@/api/templateParameterTypes'

export default {
  components: {
    MultipleSelect,
    NNParameterHighlighter,
  },
  inject: ['formRules'],
  props: {
    modelValue: {
      type: Array,
      default: () => [],
    },
    template: {
      type: String,
      default: '',
    },
    color: {
      type: String,
      default: 'white',
    },
    loadParameterValuesFromTemplate: {
      type: Boolean,
      default: false,
    },
    previewText: {
      type: String,
      default: '',
    },
    stacked: {
      type: Boolean,
      default: false,
    },
    disabled: {
      type: Boolean,
      default: false,
    },
    withUnformattedVersion: {
      type: Boolean,
      default: true,
    },
    unformattedLabel: {
      type: String,
      required: false,
      default: '',
    },
    maxTemplateLength: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['update:modelValue'],
  data() {
    return {
      parameters: [],
      separators: [' and ', ' or ', ' and/or '],
    }
  },
  computed: {
    namePreview() {
      return this.cleanName(this.getNamePreview())
    },
    namePlainPreview() {
      let namePreview = this.cleanName(this.getNamePreview())
      namePreview = namePreview
        .replaceAll('</li>', '; ')
        .replaceAll('<li>', ' ')
      if (namePreview !== undefined) {
        const tag = new DOMParser().parseFromString(namePreview, 'text/html')
        if (tag.documentElement.textContent) {
          return tag.documentElement.textContent.replaceAll(/\[|\]/g, '')
        }
      }
      return ''
    },
    unformattedTextLabel() {
      return this.unformattedLabel
        ? this.unformattedLabel
        : this.$t('_global.plain_text_version')
    },
  },
  watch: {
    /*
     ** Here we delay the execution of the watcher to avoid unexpected behaviour when the user leaves his finger pressed
     ** on a key for example.
     */
    template: {
      async handler(value) {
        if (this.updatingParameters) {
          return
        }
        setTimeout(async () => {
          if (value !== this.template) {
            return
          }
          this.updatingParameters = true
          if (this.loadParameterValuesFromTemplate && value) {
            this.parameters = []
            const extractedParams =
              templateParameters.getTemplateParametersFromTemplate(value)
            if (extractedParams.length !== this.modelValue.length) {
              this.$emit('update:modelValue', [])
            }
            for (const param of extractedParams) {
              const resp = await templateParameterTypes.getTerms(param)
              // remove any term with an empty name or where the name only consists of whitespaces
              const data = resp.data.filter(
                (term) => term.name.trim().length > 0
              )
              this.parameters.push({
                name: param,
                terms: data,
              })
            }
            if (this.modelValue.length) {
              this.modelValue.forEach((param, index) => {
                if (param.selectedValues) {
                  this.parameters[index].selectedValues = param.selectedValues
                }
                if (param.selectedSeparator) {
                  this.parameters[index].selectedSeparator =
                    param.selectedSeparator
                }
              })
            }
          }
          this.updatingParameters = false
        }, 100)
      },
      immediate: true,
    },
    modelValue(newVal) {
      if (newVal) {
        this.parameters = [...newVal]
      }
    },
  },
  created() {
    // Force skip property initialization to avoid a strange side
    // effect with selection clearing and textvalue fields...
    for (const parameter of this.modelValue) {
      if (parameter.skip === undefined) {
        parameter.skip = false
      }
    }
  },
  mounted() {
    this.parameters = [...this.modelValue]
  },
  methods: {
    clearSelection(parameter) {
      parameter.selectedValues = []
      parameter.selectedSeparator = null
      parameter.skip = !parameter.skip
      this.update()
    },
    cleanName(value) {
      const rules = {
        '([])': '[]',
        '[NA]': '[]',
        ',,': ',',
        '  ': ' ',
        '[] []': '',
        '[] ([': '([',
        '[) []': '])',
        '] and []': ']',
        '[] and [': '[',
        '], []': ']',
        '[], [': '[',
        '] or []': ']',
        '[] or [': '[',
        '] with [],': ']',
        '] []': ']',
        '[] [': '[',
        '[]': '',
      }
      for (const original of Object.keys(rules)) {
        value = value.replace(original, rules[original])
      }
      return value.trim()
    },
    cleanItemName(item) {
      // Return the name without any html tags such as <p> or </p>
      return `${item.name.replace(/<\/?[^>]+(>)/g, '')}`
    },
    getNamePreview(hideEmptyParams) {
      if (!this.template) {
        return ''
      }
      if (!this.parameters.length) {
        return this.template
      }
      let result = ''
      let paramIndex = 0
      let inParam = false
      for (const c of this.template) {
        if (c === '[') {
          inParam = true
        } else if (c === ']') {
          if (paramIndex < this.parameters.length) {
            if (
              this.parameters[paramIndex].selectedValues &&
              this.parameters[paramIndex].selectedValues.length
            ) {
              if (
                this.parameters[paramIndex].name === constants.NUM_VALUE ||
                this.parameters[paramIndex].name === constants.TEXT_VALUE
              ) {
                result += '[' + this.parameters[paramIndex].selectedValues + ']'
              } else {
                let valueNames = null
                if (paramIndex === 0 && result.length < 4) {
                  valueNames = this.parameters[paramIndex].selectedValues.map(
                    (v) => v.name.charAt(0).toUpperCase() + v.name.slice(1)
                  )
                } else {
                  valueNames = this.parameters[paramIndex].selectedValues.map(
                    (v) => v.name
                  )
                }
                const concatenation = this.parameters[paramIndex]
                  .selectedSeparator
                  ? valueNames.join(
                      this.parameters[paramIndex].selectedSeparator
                    )
                  : valueNames.join(' ')
                result += `[${concatenation}]`
              }
            } else if (this.parameters[paramIndex].skip) {
              result += hideEmptyParams ? '' : '[]'
            } else {
              result += `[${this.parameters[paramIndex].name}]`
            }
          }
          paramIndex++
          inParam = false
        } else if (!inParam) {
          result += c
        }
      }
      return result
    },
    update() {
      this.$emit('update:modelValue', this.parameters)
    },
  },
}
</script>
