<template>
  <SimpleFormDialog
    ref="formRef"
    :title="$t('StudyBranchArms.branch')"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.name"
              :label="$t('StudyBranchArms.name')"
              :rules="[formRules.required, formRules.max(form.name, 200)]"
              clearable
              class="required"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12">
            <v-text-field
              v-model="form.short_name"
              :label="$t('StudyBranchArms.branch_short_name')"
              :rules="[formRules.required]"
              clearable
              class="required"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { inject, onMounted, ref, watch } from 'vue'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'

const formRules = inject('formRules')
const emit = defineEmits(['close', 'save'])

const props = defineProps({
  branch: {
    type: Object,
    default: null,
  },
  open: Boolean,
})

const form = ref({})

watch(
  () => props.branch,
  (value) => {
    if (value) {
      form.value = JSON.parse(JSON.stringify(value))
    }
  },
  { immediate: true }
)

onMounted(() => {
  form.value = JSON.parse(JSON.stringify(props.branch))
})

function submit() {
  emit('save', form.value)
}

function cancel() {
  emit('close')
}
</script>
