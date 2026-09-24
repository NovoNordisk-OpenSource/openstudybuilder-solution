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
          <v-col cols="12">
            <v-text-field
              v-model="form.name"
              :label="$t('_global.name')"
              :rules="[formRules.required]"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-textarea
              v-model="form.definition"
              :label="$t('UCUM.description')"
              :rules="[formRules.required]"
              clearable
              auto-grow
              rows="1"
            />
          </v-col>
        </v-row>
        <v-row v-if="editedTerm">
          <v-col cols="12">
            <v-textarea
              v-model="form.change_description"
              :label="$t('_global.change_description')"
              :rules="[formRules.required]"
              clearable
              auto-grow
              rows="1"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import dictionaries from '@/api/dictionaries'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import constants from '@/constants/libraries'
import _isEmpty from 'lodash/isEmpty'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const props = defineProps({
  editedTerm: {
    type: Object,
    default: null,
  },
  codelistUid: {
    type: String,
    default: null,
  },
  open: Boolean,
})

const emit = defineEmits(['save', 'close'])

const helpItems = ['UCUM.code', 'UCUM.description']

const form = ref({})
const formRef = ref()

const title = computed(() => {
  return props.editedTerm
    ? t('UCUMCodeForm.edit_title')
    : t('UCUMCodeForm.add_title')
})

watch(
  () => props.codelistUid,
  () => {
    form.value.codelist_uid = props.codelistUid
  }
)

watch(
  () => props.editedTerm,
  (value) => {
    if (!_isEmpty(value)) {
      dictionaries.retrieve(value.term_uid).then((resp) => {
        form.value = {
          name: resp.data.name,
          definition: resp.data.definition,
        }
      })
    }
  },
  { immediate: true }
)

function close() {
  formRef.value.working = false
  notificationHub.clearErrors()
  form.value = {}
  emit('close')
}

async function submit() {
  notificationHub.clearErrors()

  const data = { ...form.value }
  data.name_sentence_case = form.value.name
  data.dictionary_id = form.value.name
  try {
    if (!props.editedTerm) {
      data.library_name = constants.LIBRARY_UCUM
      await dictionaries.create(form.value)
      notificationHub.add({
        msg: t('DictionaryTermForm.create_success'),
      })
    } else {
      await dictionaries.update(props.editedTerm.term_uid, form.value)
      notificationHub.add({
        msg: t('DictionaryTermForm.update_success'),
      })
    }
    emit('save')
    close()
  } finally {
    formRef.value.working = false
  }
}
</script>
