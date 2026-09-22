<template>
  <SimpleFormDialog
    ref="formRef"
    :title="$t('ActivityInstanceClassForm.edit_title')"
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
              data-cy="activity-instance-class-name"
              :rules="[formRules.required]"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="form.parent_uid"
              :label="$t('ActivityInstanceClassForm.parent')"
              data-cy="activity-instance-class-parent"
              :items="parentOptions"
              item-title="name"
              item-value="uid"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              v-model="form.definition"
              :label="$t('_global.definition')"
              data-cy="activity-instance-class-definition"
              clearable
              auto-grow
              rows="1"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-checkbox
              v-model="form.is_domain_specific"
              :label="$t('ActivityInstanceClassForm.is_domain_specific')"
              data-cy="activity-instance-class-domain-specific"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              v-model="form.change_description"
              :label="$t('_global.change_description')"
              data-cy="activity-instance-class-change-description"
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
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/api/activityInstanceClasses'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import { useFormStore } from '@/stores/form'

const { t } = useI18n()
const formStore = useFormStore()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')

const props = defineProps({
  editedInstanceClass: {
    type: Object,
    default: null,
  },
  open: Boolean,
})
const emit = defineEmits(['close', 'save'])

const formRef = ref()
const observer = ref()
const form = ref({})
const allInstanceClasses = ref([])

const parentOptions = computed(() =>
  allInstanceClasses.value.filter(
    (ic) => ic.uid !== props.editedInstanceClass?.uid
  )
)

const helpItems = [
  'ActivityInstanceClassForm.name',
  'ActivityInstanceClassForm.parent',
  'ActivityInstanceClassForm.definition',
  'ActivityInstanceClassForm.is_domain_specific',
]

onMounted(() => {
  api.getAll({ page_size: 0, sort_by: { name: true } }).then((resp) => {
    allInstanceClasses.value = resp.data.items
  })
})

watch(
  () => props.editedInstanceClass,
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
    parent_uid: value.parent_class?.uid ?? value.parent_uid ?? null,
    definition: value.definition,
    is_domain_specific: value.is_domain_specific ?? false,
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
  api.update(props.editedInstanceClass.uid, data).then(
    (resp) => {
      notificationHub.add({
        msg: t('ActivityInstanceClassForm.update_success'),
        type: 'success',
      })
      emit('save', resp.data)
      close()
    },
    () => {
      formRef.value.working = false
    }
  )
}
</script>
