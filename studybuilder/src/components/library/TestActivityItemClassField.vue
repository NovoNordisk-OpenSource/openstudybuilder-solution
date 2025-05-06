<template>
  <v-card class="bg-nnBaseLight" rounded="lg" border="sm" flat>
    <v-card-text>
      <div class="d-flex mb-6">
        <v-select
          :model-value="props.testNameAic.uid"
          :label="$t('ActivityInstanceForm.activity_item_class')"
          :items="[props.testNameAic]"
          bg-color="white"
          item-title="name"
          item-value="uid"
          disabled
          variant="outlined"
          density="compact"
          class="w-50"
          hide-details
        />
        <SelectActivityItemTermField
          v-model="model"
          v-model:search="search"
          :label="$t('ActivityInstanceForm.name_submission_value')"
          :activity-item-class="props.testNameAic"
          :data-domain="props.dataDomain"
          item-title="name_submission_value"
          class="ml-4 w-50"
          :disabled="props.disabled"
          :rules="[formRules.required]"
        />
      </div>
      <div class="d-flex">
        <v-select
          :model-value="props.testCodeAic.uid"
          :label="$t('ActivityInstanceForm.activity_item_class')"
          :items="[props.testCodeAic]"
          bg-color="white"
          item-title="name"
          item-value="uid"
          disabled
          variant="outlined"
          density="compact"
          class="w-50"
          hide-details
        />
        <SelectActivityItemTermField
          v-model="model"
          v-model:search="search"
          :label="$t('ActivityInstanceForm.code_submission_value')"
          :activity-item-class="props.testCodeAic"
          :data-domain="props.dataDomain"
          item-title="code_submission_value"
          class="ml-4 w-50"
          :rules="[formRules.required]"
        />
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup>
import { inject, ref } from 'vue'
import SelectActivityItemTermField from './SelectActivityItemTermField.vue'

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

const model = defineModel()
const search = ref('')
</script>
