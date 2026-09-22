<template>
  <v-card class="bg-nnBaseLight" rounded="lg" border="sm" flat v-bind="$attrs">
    <v-card-text>
      <div class="d-flex align-center">
        <div class="flex-grow-1">
          <div class="d-flex mb-6">
            <v-select
              :model-value="props.testNameAic.uid"
              :label="$t('ActivityInstanceForm.activity_item_class')"
              :items="[props.testNameAic]"
              bg-color="white"
              item-title="display_name"
              item-value="uid"
              disabled
              class="w-50"
            />
            <SelectActivityItemTermField
              ref="nameTermField"
              :key="props.testNameAic.uid"
              v-model="model"
              v-model:codelist="nameCodelist"
              v-model:search="search"
              :label="$t('ActivityInstanceForm.name_submission_value')"
              :activity-item-class="props.testNameAic"
              :data-domain="props.dataDomain"
              item-title="submission_value"
              class="ml-4 w-50"
              :disabled="props.disabled"
              :rules="[formRules.required]"
              @updatecodelist="changeCodelist"
            />
          </div>
          <div class="d-flex">
            <v-select
              :model-value="props.testCodeAic.uid"
              :label="$t('ActivityInstanceForm.activity_item_class')"
              :items="[props.testCodeAic]"
              bg-color="white"
              item-title="display_name"
              item-value="uid"
              disabled
              class="w-50"
            />
            <SelectActivityItemTermField
              ref="codeTermField"
              :key="props.testCodeAic.uid"
              v-model="model"
              v-model:codelist="codeCodelist"
              v-model:search="search"
              :label="$t('ActivityInstanceForm.code_submission_value')"
              :activity-item-class="props.testCodeAic"
              :data-domain="props.dataDomain"
              item-title="submission_value"
              class="ml-4 w-50"
              :rules="[formRules.required]"
              :disabled="props.disabled"
              @updatecodelist="changeCodelist"
            />
          </div>
        </div>
        <div>
          <v-btn
            color="primary"
            variant="outlined"
            class="ml-4"
            icon="mdi-text-box-search-outline"
            size="small"
            @click="openTermsSelectionForm()"
          >
          </v-btn>
        </div>
      </div>
    </v-card-text>
  </v-card>
  <TermsSelectionForm
    v-model:codelist="nameCodelist"
    v-model:term-selection="model"
    :open="showTermsSelectionForm"
    :title="$t('TestActivityItemClassField.advanced_search_title')"
    max-width="1200px"
    paired-codelist-mode
    @close="closeTermsSelectionForm"
  />
</template>

<script setup>
import { computed, inject, ref } from 'vue'
import SelectActivityItemTermField from './SelectActivityItemTermField.vue'
import TermsSelectionForm from '@/components/library/TermsSelectionForm.vue'

const nameTermField = ref(null)
const codeTermField = ref(null)

const hasInvalidTerms = computed(
  () =>
    (nameTermField.value?.hasInvalidTerms ?? false) ||
    (codeTermField.value?.hasInvalidTerms ?? false)
)

defineExpose({
  hasInvalidTerms,
})

const props = defineProps({
  testCodeAic: {
    type: Object,
    default: null,
  },
  testNameAic: {
    type: Object,
    default: null,
  },
  dataDomain: {
    type: String,
    default: null,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
})

const formRules = inject('formRules')

const model = defineModel({ type: String })
const codeCodelist = defineModel('codeCodelist', { type: String })
const nameCodelist = defineModel('nameCodelist', { type: String })

const search = ref('')
const showTermsSelectionForm = ref(false)

function openTermsSelectionForm() {
  showTermsSelectionForm.value = true
}
const closeTermsSelectionForm = () => {
  showTermsSelectionForm.value = false
}

const changeCodelist = (codelist) => {
  if (!codelist) return
  if (
    codelist.paired_codes_codelist_uid &&
    codelist.paired_codes_codelist_uid !== codeCodelist.value
  ) {
    codeCodelist.value = codelist.paired_codes_codelist_uid
  } else if (
    codelist.paired_names_codelist_uid &&
    codelist.paired_names_codelist_uid !== nameCodelist.value
  ) {
    nameCodelist.value = codelist.paired_names_codelist_uid
  }
}
</script>
