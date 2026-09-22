<template>
  <div>
    <SimpleFormDialog
      ref="formRef"
      :title="title"
      :open="open"
      max-width="1200px"
      :no-saving="readOnly"
      @submit="submit"
      @close="cancel"
    >
      <template #body>
        <v-expansion-panels v-model="panels" multiple>
          <v-expansion-panel>
            <v-expansion-panel-title class="text-headline-small">
              {{ $t('CRFForms.standard_attributes') }}
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <v-row>
                <v-col>
                  <v-switch
                    v-model="form.mandatory"
                    :label="$t('CRFReferencesForm.mandatory')"
                    true-value="Yes"
                    false-value="No"
                    :disabled="readOnly"
                  />
                </v-col>
                <v-col>
                  <v-switch
                    v-if="element.uid && element.uid.includes('OdmForm')"
                    v-model="form.locked"
                    :label="$t('CRFReferencesForm.locked')"
                    true-value="Yes"
                    false-value="No"
                    :disabled="readOnly"
                  />
                </v-col>
              </v-row>
            </v-expansion-panel-text>
          </v-expansion-panel>
          <v-expansion-panel
            v-if="
              element.uid &&
              (element.uid.includes('OdmItemGroup') ||
                element.uid.includes('OdmItem'))
            "
          >
            <v-expansion-panel-title class="text-headline-small">
              {{ $t('CRFForms.vendor_extensions_low') }}
            </v-expansion-panel-title>
            <v-expansion-panel-text>
              <CrfExtensionsManagementTable
                :type="type"
                :edit-extensions="selectedExtensions"
                only-attributes
                :read-only="readOnly"
                @set-extensions="setExtensions"
              />
            </v-expansion-panel-text>
          </v-expansion-panel>
        </v-expansion-panels>
      </template>
    </SimpleFormDialog>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import crfs from '@/api/crfs'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import CrfExtensionsManagementTable from '@/components/library/crfs/CrfExtensionsManagementTable.vue'

const props = defineProps({
  open: Boolean,
  element: {
    type: Object,
    default: null,
  },
  readOnly: Boolean,
  parent: {
    type: Object,
    default: null,
  },
})

const notificationHub = inject('notificationHub')

const { t } = useI18n()
const emit = defineEmits(['close'])
const formRef = ref()
const confirm = ref()

const form = ref({})
const elementCopy = ref({})
const selectedExtensions = ref([])
const type = ref('')
const panels = ref([0])

const title = computed(() => {
  return t('CRFReferencesForm.title') + props.element.name
})

watch(
  () => props.element,
  (value) => {
    elementCopy.value = Object.assign(elementCopy.value, value)
    form.value = value
    selectedExtensions.value = form.value.vendor
      ? form.value.vendor.attributes
      : []
    const params = {}
    if (selectedExtensions.value.length > 0) {
      params.filters = {
        uid: { v: selectedExtensions.value.map((attr) => attr.uid), op: 'co' },
      }
      crfs.getAllAttributes(params).then((resp) => {
        resp.data.items.forEach((el) => {
          el.value = selectedExtensions.value.find(
            (attr) => attr.uid === el.uid
          ).value
        })
        selectedExtensions.value = resp.data.items
        selectedExtensions.value.forEach((attr) => (attr.type = 'attr'))
      })
    }
    type.value =
      props.element.uid && props.element.uid.includes('OdmItemGroup')
        ? 'ItemGroupRef'
        : 'ItemRef'
  }
)

onMounted(() => {
  elementCopy.value = Object.assign(elementCopy.value, props.element)
  form.value = props.element
})

function setExtensions(extensions) {
  selectedExtensions.value = extensions
}

async function submit() {
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  }
  if (!form.value.uid.includes('OdmForm')) {
    form.value.vendor.attributes = selectedExtensions.value
  }
  if (form.value.uid.includes('OdmForm')) {
    crfs.addFormsToCollection([form.value], props.parent.uid, false).then(
      () => {
        notificationHub.add({
          type: 'success',
          msg: t('CRFReferencesForm.success_message'),
        })
        emit('close')
      },
      () => {
        formRef.value.working = false
      }
    )
  } else if (form.value.uid.includes('OdmItemGroup')) {
    let parentForm = {}
    await crfs.getCrfForms().then((resp) => {
      parentForm = resp.data.find((el) => el.uid === props.parent.uid)
    })
    form.value.vendor.attributes = selectedExtensions.value
    if (
      parentForm.parent_uids.length > 1 &&
      !(await confirm.value.open(
        t('CRFReferencesForm.warning_templ', {
          count: parentForm.parent_uids.length - 1,
        }),
        options
      ))
    ) {
      emit('close')
      return
    }
    crfs.addItemGroupsToForm([form.value], props.parent.uid, false).then(
      () => {
        notificationHub.add({
          type: 'success',
          msg: t('CRFReferencesForm.success_message'),
        })
        emit('close')
      },
      () => {
        formRef.value.working = false
      }
    )
  } else {
    let group = {}
    await crfs.getCrfGroups().then((resp) => {
      group = resp.data.find((el) => el.uid === props.parent.uid)
    })
    if (group.parent_uids.length === 1) {
      let numberOfParentCollections = 0
      await crfs
        .getRelationships(group.parent_uids[0], 'forms')
        .then(async (resp) => {
          numberOfParentCollections = resp.data.OdmStudyEvent.length
        })
      if (
        numberOfParentCollections > 1 &&
        !(await confirm.value.open(
          t('CRFReferencesForm.collection_warning'),
          options
        ))
      ) {
        emit('close')
        return
      }
    }
    if (
      group.parent_uids.length > 1 &&
      !(await confirm.value.open(
        t('CRFReferencesForm.warning_forms', {
          count: group.parent_uids.length - 1,
        }),
        options
      ))
    ) {
      emit('close')
      return
    }
    crfs.addItemsToItemGroup([form.value], props.parent.uid, false).then(
      () => {
        notificationHub.add({
          type: 'success',
          msg: t('CRFReferencesForm.success_message'),
        })
        emit('close')
      },
      () => {
        formRef.value.working = false
      }
    )
  }
}

function cancel() {
  form.value = Object.assign(form.value, elementCopy.value)
  emit('close')
}
</script>
