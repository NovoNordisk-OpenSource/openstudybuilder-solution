<template>
  <SimpleFormDialog
    ref="dialog"
    :title="title"
    :open="open"
    max-width="1000px"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col cols="6">
            <v-text-field
              v-model="form.name"
              :label="$t('CRFExtensions.ele_name')"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
          <v-col>
            <v-select
              v-model="form.compatible_types"
              :label="$t('CRFExtensions.compatible_types')"
              :items="compatibleTypes"
              multiple
              clearable
            />
          </v-col>
        </v-row>
        <v-row v-if="editItem.uid === undefined">
          <v-col cols="6">
            <v-select
              v-model="attribute"
              :label="$t('CRFExtensions.add_existing_attr')"
              :items="existingAttributes"
              return-object
              item-title="name"
              item-value="uid"
              clearable
              @update:model-value="addExistingAttribute"
            />
          </v-col>
          <div class="mt-6">
            {{ $t('_global.or') }}
          </div>
          <v-col cols="3">
            <v-btn
              dark
              size="small"
              class="mt-2"
              color="primary"
              @click="addNewAttribute"
            >
              {{ $t('CRFExtensions.add_new_attr') }}
            </v-btn>
          </v-col>
        </v-row>
        <v-row v-for="attr in attributesToCreate" :key="attr.key">
          <v-col cols="3">
            <v-text-field
              v-model="attr.name"
              :disabled="editItem.uid !== undefined"
              :label="$t('CRFExtensions.attr_name')"
              clearable
            />
          </v-col>
          <v-col cols="3">
            <v-select
              v-model="attr.data_type"
              :disabled="editItem.uid !== undefined"
              :label="$t('CRFExtensions.data_type')"
              :items="dataTypes"
              item-title="submission_value"
              item-value="submission_value"
              clearable
            />
          </v-col>
          <v-col cols="3">
            <v-btn
              :disabled="editItem.uid !== undefined"
              class="ml-2"
              dark
              size="small"
              color="primary"
              icon="mdi-delete-outline"
              @click="removeAttribute(attr)"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { inject, onMounted, ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'

import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import crfs from '@/api/crfs'
import terms from '@/api/controlledTerminology/terms'

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
})

const emit = defineEmits(['close'])

const { t } = useI18n()

const formRules = inject('formRules')

const form = ref({})
const dataTypes = ref([])
const attribute = ref(null)
const attributes = ref([])
const attributesKeyIndex = ref(0)
const existingAttributes = ref([])
const attributesToCreate = ref([])
const compatibleTypes = ['FormDef', 'ItemGroupDef', 'ItemDef']

const dialog = ref(null)
const observer = ref(null)

const title = computed(() =>
  props.editItem?.uid ? t('CRFExtensions.edit_ele') : t('CRFExtensions.new_ele')
)

watch(
  () => props.editItem,
  (value) => {
    initForm(value)
  }
)

watch(
  attributes,
  () => {
    existingAttributes.value = attributes.value
  },
  { deep: true }
)

onMounted(async () => {
  terms.getTermsByCodelist('dataType').then((resp) => {
    dataTypes.value = resp.data.items
  })

  await crfs.getAllAttributes({ page_size: 0 }).then((resp) => {
    const seen = new Set()
    attributes.value = resp.data.items.filter((item) => {
      const key = `${item.name}|${item.data_type}|${item.regex}`
      if (seen.has(key)) return false
      seen.add(key)
      return true
    })
  })
})

const addNewAttribute = () => {
  if (!attributesToCreate.value.find((attr) => attr.name === '')) {
    attributesToCreate.value.push({
      key: attributesKeyIndex.value,
      name: '',
      data_type: '',
    })
    attributesKeyIndex.value += 1
  }
}

const addExistingAttribute = (newAttribute) => {
  if (newAttribute) {
    attributesToCreate.value.push(newAttribute)
    existingAttributes.value = existingAttributes.value.filter(
      (attr) => attr.uid !== newAttribute.uid
    )
    attribute.value = null
  }
}

const removeAttribute = (attributeToRemove) => {
  attributesToCreate.value = attributesToCreate.value.filter(
    (attr) => attr.key !== attributeToRemove.key
  )
  if (attributeToRemove.uid) {
    existingAttributes.value.push(attributeToRemove)
  }
}

const close = () => {
  observer.value?.reset?.()
  attributesToCreate.value = []
  form.value = {}
  emit('close')
}

const cancel = async () => {
  close()
}

const submit = async () => {
  form.value.vendor_namespace_uid = props.parentUid

  if (form.value.uid) {
    form.value.change_description = t('_global.change_description')
    await crfs.editElement(form.value.uid, form.value).then(
      () => {
        close()
      },
      () => {
        if (dialog.value) dialog.value.working = false
      }
    )
  } else {
    let elementUid = ''
    try {
      const resp = await crfs.createElement(form.value)
      elementUid = resp.data.uid
      if (attributesToCreate.value.length > 0 && elementUid !== '') {
        for (const attr of attributesToCreate.value) {
          delete attr.compatible_types
          attr.vendor_element_uid = elementUid
          await crfs.createAttribute(attr)
        }
      }
      close()
    } catch (_error) {
      if (dialog.value) dialog.value.working = false
    }
  }
}

const initForm = (item) => {
  form.value = item || {}
  attributes.value.forEach((attr) => {
    if (
      attr.vendor_element &&
      attr.vendor_element.uid === props.editItem?.uid
    ) {
      attributesToCreate.value.push(attr)
    }
  })
}
</script>
