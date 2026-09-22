<template>
  <SimpleFormDialog
    ref="formDialog"
    :title="title"
    :help-items="helpItems"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col cols="6">
            <v-text-field
              v-model="form.name"
              :label="$t('CRFExtensions.attr_name')"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
          <v-col cols="6">
            <v-select
              v-model="form.data_type"
              :label="$t('CRFExtensions.data_type')"
              :items="dataTypes"
              item-title="submission_value"
              item-value="submission_value"
              :rules="[formRules.required]"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col v-if="parentType === crfTypes.NAMESPACE" cols="6">
            <v-select
              v-model="form.compatible_types"
              :label="$t('CRFExtensions.compatible_types')"
              :items="compatibleTypes"
              :rules="[formRules.required]"
              multiple
              clearable
            />
          </v-col>
          <v-col cols="6">
            <v-text-field
              v-model="form.value_regex"
              :label="$t('CRFExtensions.regex_expression')"
              clearable
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import crfs from '@/api/crfs'
import terms from '@/api/controlledTerminology/terms'
import crfTypes from '@/constants/crfTypes'

const props = defineProps({
  open: Boolean,
  editItem: {
    type: Object,
    default: null,
  },
  parentUid: {
    type: String,
    default: null,
  },
  parentType: {
    type: String,
    default: null,
  },
})

const emit = defineEmits(['close'])

const { t } = useI18n()
const formRules = inject('formRules')

const formDialog = ref(null)
const observer = ref(null)

const form = ref({})
const helpItems = ref([])
const dataTypes = ref([])
const compatibleTypes = ref([
  'FormDef',
  'ItemGroupDef',
  'ItemDef',
  'ItemGroupRef',
  'ItemRef',
])

const title = computed(() =>
  props.editItem?.uid
    ? t('CRFExtensions.edit_attr')
    : t('CRFExtensions.new_attr')
)

watch(
  () => props.editItem,
  (value) => {
    initForm(value)
  }
)

onMounted(() => {
  terms.getTermsByCodelist('dataType').then((resp) => {
    dataTypes.value = resp.data.items
  })
  initForm(props.editItem)
})

const cancel = async () => {
  close()
}

const close = () => {
  observer.value?.reset?.()
  emit('close')
}

const submit = async () => {
  if (props.parentType === crfTypes.NAMESPACE) {
    form.value.vendor_namespace_uid = props.parentUid
  } else {
    form.value.vendor_element_uid = props.parentUid
  }

  if (props.editItem?.uid) {
    await crfs.editAttribute(props.editItem.uid, form.value).then(
      () => {
        close()
      },
      () => {
        if (formDialog.value) {
          formDialog.value.working = false
        }
      }
    )
  } else {
    await crfs.createAttribute(form.value).then(
      () => {
        close()
      },
      () => {
        if (formDialog.value) {
          formDialog.value.working = false
        }
      }
    )
  }
}

const initForm = (item) => {
  form.value = item || {}
}
</script>
