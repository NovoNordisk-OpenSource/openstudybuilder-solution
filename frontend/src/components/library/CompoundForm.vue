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
              :label="$t('CompoundForm.name')"
              :rules="[formRules.required]"
              class="required"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-textarea
              v-model="form.definition"
              :label="$t('_global.definition')"
              clearable
              auto-grow
              rows="1"
            />
          </v-col>
        </v-row>
        <v-row v-if="compoundUid">
          <v-col cols="12">
            <v-textarea
              v-model="form.change_description"
              :label="$t('HistoryTable.change_description')"
              clearable
              auto-grow
              rows="1"
              :rules="[formRules.required]"
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
import compounds from '@/api/concepts/compounds'
import compoundAliases from '@/api/concepts/compoundAliases'
import libConstants from '@/constants/libraries'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import { useFormStore } from '@/stores/form'

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const props = defineProps({
  compoundUid: {
    type: String,
    default: null,
  },
  open: Boolean,
})
const emit = defineEmits(['close', 'created', 'updated'])

const formStore = useFormStore()

const compound = ref(null)
const form = ref(getInitialForm())
const formRef = ref()

const helpItems = ['CompoundForm.name', 'CompoundForm.definition']

const title = computed(() => {
  return props.compoundUid
    ? t('CompoundForm.edit_title')
    : t('CompoundForm.add_title')
})

watch(
  () => props.compoundUid,
  (value) => {
    if (value) {
      compounds.getObject(props.compoundUid).then((resp) => {
        form.value = resp.data
        form.value.change_description = null
        formStore.save(form.value)
      })
    }
  },
  { immediate: true }
)
watch(
  () => form.value.name,
  (value) => {
    if (value && !compound.value) {
      form.value.alias_name = value
    }
  }
)

function close() {
  emit('close')
  notificationHub.clearErrors()
  form.value = getInitialForm()
  formStore.reset()
}
function getInitialForm() {
  return {}
}

async function addCompound(data) {
  notificationHub.clearErrors()

  data.library_name = libConstants.LIBRARY_SPONSOR
  const createdCompound = await compounds.create(data)
  try {
    // Add alias
    const alias = {}
    alias.compound_uid = createdCompound.data.uid
    alias.name = data.alias_name
    alias.name_sentence_case = data.alias_name_sentence_case
    alias.is_preferred_synonym = true
    alias.library_name = data.library_name
    alias.abbreviation = null
    await compoundAliases.create(alias)
  } catch (error) {
    // If creation of alias fails, delete the newly created compound
    await compounds.deleteObject(createdCompound.data.uid)
    throw error
  }
  emit('created')
  notificationHub.add({
    msg: t('CompoundForm.add_success'),
    type: 'success',
  })
}
async function updateCompound(data) {
  notificationHub.clearErrors()

  if (formStore.isEmpty || formStore.isEqual(data)) {
    close()
    notificationHub.add({
      type: 'info',
      msg: t('_global.no_changes'),
    })
    return
  }
  await compounds.update(props.compoundUid, data)
  emit('updated')
  notificationHub.add({
    msg: t('CompoundForm.update_success'),
    type: 'success',
  })
}

async function submit() {
  notificationHub.clearErrors()

  const data = { ...form.value }
  data.name_sentence_case = data.name.toLowerCase()
  try {
    if (!props.compoundUid) {
      await addCompound(data)
    } else {
      await updateCompound(data)
    }
    close()
  } finally {
    formRef.value.working = false
  }
}
</script>

<style lang="scss" scoped>
.v-btn {
  &--right {
    right: -16px;
  }
}

.sub-v-card {
  margin-bottom: 25px;
}
</style>
