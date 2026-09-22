<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('CollapsibleVisitGroupForm.title')"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-alert type="warning" :text="$t('CollapsibleVisitGroupForm.warning')" />
      <v-form ref="observer">
        <v-row>
          <v-col>
            <v-select
              v-model="visitTemplate"
              :items="visits"
              :label="$t('CollapsibleVisitGroupForm.visit_template')"
              item-title="text"
              item-value="refs[0].uid"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import studyEpochs from '@/api/studyEpochs'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { inject, ref } from 'vue'

const formRules = inject('formRules')
const studiesGeneralStore = useStudiesGeneralStore()
const emit = defineEmits(['close', 'created'])

const props = defineProps({
  visits: {
    type: Array,
    default: () => [],
  },
  format: {
    type: String,
    default: '',
  },
  open: Boolean,
})
const observer = ref()
const form = ref()

const visitTemplate = ref(null)

function close() {
  emit('close')
  visitTemplate.value = null
  observer.value.reset()
  form.value.working = false
}

async function submit() {
  const visitUids = props.visits.map((item) => item.refs[0].uid)
  const data = {
    visits_to_assign: visitUids,
    format: props.format,
    overwrite_visit_from_template: visitTemplate.value,
    validate_only: false,
  }
  await studyEpochs.createCollapsibleVisitGroup(
    studiesGeneralStore.selectedStudy.uid,
    data
  )
  emit('created')
  close()
}
</script>
