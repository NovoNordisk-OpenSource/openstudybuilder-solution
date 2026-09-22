<template>
  <SimpleFormDialog
    ref="formRef"
    :title="title"
    :help-items="helpItems"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.inn"
              :label="$t('ActiveSubstance.inn')"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.analyte_number"
              :label="$t('ActiveSubstance.analyte_number')"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.short_number"
              :label="$t('ActiveSubstance.short_number')"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.long_number"
              :label="$t('ActiveSubstance.long_number')"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.unii_term_uid"
              :label="$t('ActiveSubstance.unii')"
              :items="substances"
              :filter-keys="[
                'raw.name',
                'raw.dictionary_id',
                'raw.pclass.name',
                'raw.pclass.dictionary_id',
              ]"
              item-title="dictionary_id"
              item-value="term_uid"
            >
              <template #item="{ props, internalItem: item }">
                <v-list-item
                  v-bind="props"
                  :title="`${item.raw.name} (${item.raw.dictionary_id})`"
                >
                  <v-list-item-subtitle class="pa-2">
                    <template v-if="item.raw.pclass">
                      {{ $t('ActiveSubstance.pharma_class') }}
                      {{ item.raw.pclass.name }} ({{
                        item.raw.pclass.dictionary_id
                      }})
                    </template>
                    <template v-else> - </template>
                  </v-list-item-subtitle>
                </v-list-item>
              </template>
            </v-autocomplete>
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import dictionariesApi from '@/api/dictionaries'
import activeSubstances from '@/api/concepts/activeSubstances'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import libConstants from '@/constants/libraries'
import { useFormStore } from '@/stores/form'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const props = defineProps({
  activeSubstanceUid: {
    type: String,
    default: null,
  },
  open: Boolean,
})
const emit = defineEmits(['close', 'created', 'updated'])
const formStore = useFormStore()

const form = ref({})
const formRef = ref()
const substances = ref([])

const helpItems = [
  'ActiveSubstanceForm.inn',
  'ActiveSubstanceForm.analyte_number',
  'ActiveSubstanceForm.name',
  'ActiveSubstanceForm.id',
  'ActiveSubstanceForm.unii',
]

const title = computed(() => {
  return props.activeSubstanceUid
    ? t('ActiveSubstanceForm.edit_title')
    : t('ActiveSubstanceForm.add_title')
})

watch(
  () => props.activeSubstanceUid,
  (value) => {
    if (value) {
      loadFormData()
    } else {
      form.value = {}
    }
  },
  { immediate: true }
)

function close() {
  emit('close')
  notificationHub.clearErrors()
  form.value = {}
}

function loadFormData() {
  if (props.activeSubstanceUid !== null) {
    activeSubstances.getObject(props.activeSubstanceUid).then((resp) => {
      form.value = resp.data
      if (resp.data.unii) {
        form.value.unii_term_uid = resp.data.unii.substance_term_uid
      }
      formStore.save(form.value)
    })
  }
}

async function add(data) {
  data.library_name = libConstants.LIBRARY_SPONSOR
  await activeSubstances.create(data)
  emit('created')
  notificationHub.add({
    msg: t('ActiveSubstanceForm.add_success'),
    type: 'success',
  })
}
async function update(data) {
  notificationHub.clearErrors()

  if (formStore.isEmpty || formStore.isEqual(form.value)) {
    close()
    notificationHub.add({ type: 'info', msg: t('_global.no_changes') })
    return
  }
  data.change_description = t('_global.work_in_progress')
  await activeSubstances.update(props.activeSubstanceUid, data)
  emit('updated')
  notificationHub.add({
    msg: t('ActiveSubstanceForm.update_success'),
    type: 'success',
  })
}
async function submit() {
  notificationHub.clearErrors()

  const data = { ...form.value }
  try {
    if (!props.activeSubstanceUid) {
      await add(data)
    } else {
      await update(data)
    }
    close()
  } finally {
    formRef.value.working = false
  }
}

dictionariesApi
  .getSubstances({ page_size: 0, sort_by: { name: true } })
  .then((resp) => {
    substances.value = resp.data.items
  })
</script>
