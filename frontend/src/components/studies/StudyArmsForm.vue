<template>
  <SimpleFormDialog
    ref="formRef"
    :title="title"
    :help-items="helpItems"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col cols="12">
            <v-autocomplete
              v-model="form.arm_type_uid"
              :label="$t('StudyArmsForm.arm_type')"
              :items="armTypes"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              data-cy="arm-type"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.name"
              :label="$t('StudyArmsForm.arm_name')"
              data-cy="arm-name"
              :rules="[formRules.required, formRules.max(form.name, 200)]"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.label"
              :label="$t('StudyArmsForm.arm_label')"
              data-cy="arm-label"
              :rules="[formRules.max(form.label, 40)]"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.short_name"
              :label="$t('StudyArmsForm.arm_short_name')"
              data-cy="arm-short-name"
              :rules="[formRules.required, formRules.max(form.short_name, 20)]"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.randomization_group"
              :label="$t('StudyArmsForm.randomisation_group')"
              data-cy="arm-randomisation-group"
              clearable
              @blur="enableArmCode"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.code"
              :label="$t('StudyArmsForm.arm_code')"
              data-cy="arm-code"
              :rules="[formRules.max(form.code, 20)]"
              clearable
              :disabled="!armCodeEnable && !isEdit()"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.number_of_subjects"
              :label="$t('StudyArmsForm.planned_number')"
              data-cy="arm-planned-number-of-subjects"
              :rules="[formRules.min_value(form.number_of_subjects, 1)]"
              type="number"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.description"
              :label="$t('StudyArmsForm.description')"
              data-cy="arm-description"
              clearable
            />
          </v-col>
        </v-row>
        <v-text-field
          v-if="isEdit()"
          v-model="branches"
          :label="$t('StudyArmsForm.connected_branches')"
          data-cy="arm-connected-branches"
          clearable
          readonly
        />
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import arms from '@/api/arms'
import codelists from '@/api/controlledTerminology/terms'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import _isEqual from 'lodash/isEqual'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useFormStore } from '@/stores/form'
import { useI18n } from 'vue-i18n'

const formRules = inject('formRules')
const notificationHub = inject('notificationHub')

const props = defineProps({
  editedArm: {
    type: Object,
    default: undefined,
  },
  open: Boolean,
})
const emit = defineEmits(['close'])

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()
const formStore = useFormStore()

const selectedStudy = computed(() => studiesGeneralStore.selectedStudy)
const title = computed(() => {
  return Object.keys(props.editedArm).length !== 0
    ? t('StudyArmsForm.edit_arm')
    : t('StudyArmsForm.add_arm')
})

const form = ref({})
const armTypes = ref([])
const armCodeEnable = ref(false)
const branches = ref([])
const formRef = ref()
const observer = ref()
let storedForm = ''

const helpItems = [
  'StudyArmsForm.arm_type',
  'StudyArmsForm.arm_name',
  'StudyArmsForm.arm_short_name',
  'StudyArmsForm.arm_label',
  'StudyArmsForm.randomisation_group',
  'StudyArmsForm.arm_code',
  'StudyArmsForm.planned_number',
  'StudyArmsForm.description',
]

watch(
  () => props.editedArm,
  (value) => {
    if (Object.keys(value).length !== 0) {
      arms.getStudyArm(selectedStudy.value.uid, value.arm_uid).then((resp) => {
        form.value = JSON.parse(JSON.stringify(resp.data))
        if (form.value.arm_connected_branch_arms) {
          branches.value = form.value.arm_connected_branch_arms.map(
            (el) => el.name
          )
          delete form.value.arm_connected_branch_arms
        }
        form.value.arm_type_uid = value.arm_type.term_uid
        formStore.save(form.value)
      })
    }
  }
)

onMounted(() => {
  codelists.getTermsByCodelist('armTypes').then((resp) => {
    armTypes.value = resp.data.items
  })
  if (Object.keys(props.editedArm).length !== 0) {
    form.value = JSON.parse(JSON.stringify(props.editedArm))
    if (form.value.arm_connected_branch_arms) {
      branches.value = form.value.arm_connected_branch_arms.map((el) => el.name)
      delete form.value.arm_connected_branch_arms
    }
    form.value.arm_type_uid = props.editedArm.arm_type.term_uid
    formStore.save(form.value)
  }
})

function enableArmCode() {
  if (!armCodeEnable.value) {
    form.value.code = form.value.randomization_group
    armCodeEnable.value = true
  }
}
function isEdit() {
  return Object.keys(props.editedArm).length !== 0
}
async function submit() {
  notificationHub.clearErrors()

  if (Object.keys(props.editedArm).length !== 0) {
    edit()
  } else {
    create()
  }
}
function create() {
  arms.create(selectedStudy.value.uid, form.value).then(
    () => {
      notificationHub.add({
        msg: t('StudyArmsForm.arm_created'),
      })
      close()
    },
    () => {
      formRef.value.working = false
    }
  )
}
function edit() {
  arms.edit(selectedStudy.value.uid, form.value, props.editedArm.arm_uid).then(
    () => {
      notificationHub.add({
        msg: t('StudyArmsForm.arm_updated'),
      })
      close()
    },
    () => {
      formRef.value.working = false
    }
  )
}
function close() {
  notificationHub.clearErrors()
  form.value = {}
  armCodeEnable.value = false
  observer.value.reset()
  emit('close')
  formStore.reset()
}
async function cancel() {
  if (storedForm === '' || _isEqual(storedForm, JSON.stringify(form.value))) {
    close()
  } else {
    const options = {
      type: 'warning',
      cancelLabel: t('_global.cancel'),
      agreeLabel: t('_global.continue'),
    }
    if (await formRef.value.confirm(t('_global.cancel_changes'), options)) {
      close()
    }
  }
}
</script>
