<template>
  <SimpleFormDialog
    ref="formRef"
    :title="$t('ActivityItemClassForm.edit_title')"
    :help-items="helpItems"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.name"
              :label="$t('_global.name')"
              data-cy="activity-item-class-name"
              :rules="[formRules.required]"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.display_name"
              :label="$t('ActivityItemClassForm.display_name')"
              data-cy="activity-item-class-display-name"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model.number="form.order"
              :label="$t('_global.order')"
              data-cy="activity-item-class-order"
              type="number"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-select
              v-model="form.role_uid"
              :label="$t('ActivityItemClassForm.role')"
              data-cy="activity-item-class-role"
              :items="roles"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              :rules="[formRules.required]"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-select
              v-model="form.data_type_uid"
              :label="$t('ActivityItemClassForm.data_type')"
              data-cy="activity-item-class-data-type"
              :items="dataTypes"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              :rules="[formRules.required]"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.nci_concept_id"
              :label="$t('ActivityItemClassForm.nci_concept_id')"
              data-cy="activity-item-class-nci-concept-id"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              v-model="form.definition"
              :label="$t('_global.definition')"
              data-cy="activity-item-class-definition"
              clearable
              auto-grow
              rows="1"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              v-model="form.change_description"
              :label="$t('_global.change_description')"
              data-cy="activity-item-class-change-description"
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
import _isEmpty from 'lodash/isEmpty'
import { inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/api/activityItemClasses'
import terms from '@/api/controlledTerminology/terms'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import { useFormStore } from '@/stores/form'

const { t } = useI18n()
const formStore = useFormStore()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')

const props = defineProps({
  editedItemClass: {
    type: Object,
    default: null,
  },
  open: Boolean,
})
const emit = defineEmits(['close', 'save'])

const formRef = ref()
const observer = ref()
const form = ref({})
const dataTypes = ref([])
const roles = ref([])

const helpItems = [
  'ActivityItemClassForm.name',
  'ActivityItemClassForm.display_name',
  'ActivityItemClassForm.order',
  'ActivityItemClassForm.role',
  'ActivityItemClassForm.data_type',
  'ActivityItemClassForm.nci_concept_id',
  'ActivityItemClassForm.definition',
]

onMounted(() => {
  terms.getTermsByCodelist('dataType', { all: true }).then((resp) => {
    dataTypes.value = resp.data.items
  })
  terms.getTermsByCodelist('role', { all: true }).then((resp) => {
    roles.value = resp.data.items
  })
})

watch(
  () => props.editedItemClass,
  (value) => {
    if (!_isEmpty(value)) {
      api.get(value.uid).then((resp) => {
        initForm(resp.data)
      })
    }
  },
  { immediate: true }
)

function initForm(value) {
  form.value = {
    name: value.name,
    display_name: value.display_name,
    order: value.order,
    role_uid: value.role?.uid ?? value.role?.term_uid ?? null,
    data_type_uid: value.data_type?.uid ?? value.data_type?.term_uid ?? null,
    nci_concept_id: value.nci_concept_id,
    definition: value.definition,
    change_description: t('_global.work_in_progress'),
  }
  formStore.save(form.value)
}

async function cancel() {
  if (!formStore.isEqual(form.value)) {
    const options = {
      type: 'warning',
      cancelLabel: t('_global.cancel'),
      agreeLabel: t('_global.continue'),
    }
    if (!(await formRef.value.confirm(t('_global.cancel_changes'), options))) {
      return
    }
  }
  close()
}

function close() {
  notificationHub.clearErrors()
  form.value = {}
  formStore.reset()
  emit('close')
}

function submit() {
  notificationHub.clearErrors()
  const data = JSON.parse(JSON.stringify(form.value))
  api.update(props.editedItemClass.uid, data).then(
    () => {
      notificationHub.add({
        msg: t('ActivityItemClassForm.update_success'),
      })
      emit('save')
      close()
    },
    () => {
      formRef.value.working = false
    }
  )
}
</script>
