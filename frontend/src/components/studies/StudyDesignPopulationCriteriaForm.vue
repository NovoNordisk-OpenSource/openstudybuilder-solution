<template>
  <SimpleFormDialog
    ref="form"
    :title="title"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <p class="text-body-2 text-medium-emphasis mb-4">
        {{ $t('StudyDesignPopulationCriteriaForm.hint') }}
      </p>
      <v-row>
        <v-col cols="12">
          <v-autocomplete
            v-model="selectedInclusionUids"
            :items="inclusionCriteria"
            :label="$t('StudyDesignPopulationForm.inclusion_criteria')"
            item-title="label"
            item-value="uid"
            multiple
            chips
            closable-chips
            density="compact"
            :loading="loadingCriteria"
          />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <v-autocomplete
            v-model="selectedExclusionUids"
            :items="exclusionCriteria"
            :label="$t('StudyDesignPopulationForm.exclusion_criteria')"
            item-title="label"
            item-value="uid"
            multiple
            chips
            closable-chips
            density="compact"
            :loading="loadingCriteria"
          />
        </v-col>
      </v-row>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import study from '@/api/study'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const props = defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  // The population the criteria are assigned to; always required since
  // this dialog only opens once the population itself has been saved.
  population: {
    type: Object,
    default: null,
  },
})
const emit = defineEmits(['close', 'saved'])

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const studiesGeneralStore = useStudiesGeneralStore()
const form = ref()
const allCriteria = ref([])
const selectedInclusionUids = ref([])
const selectedExclusionUids = ref([])
const originalInclusionUids = ref([])
const originalExclusionUids = ref([])
const loadingCriteria = ref(false)

const title = computed(() =>
  t('StudyDesignPopulationCriteriaForm.title', {
    name: props.population?.name || props.population?.group_id || '',
  })
)

const inclusionCriteria = computed(() =>
  allCriteria.value
    .filter((c) =>
      c.criteria_type?.term_name?.toLowerCase().includes('inclusion')
    )
    .map((c) => ({
      uid: c.study_criteria_uid,
      label: `${c.order}. ${c.criteria ? c.criteria.name_plain : (c.template?.name_plain ?? '')}`,
    }))
)

const exclusionCriteria = computed(() =>
  allCriteria.value
    .filter((c) =>
      c.criteria_type?.term_name?.toLowerCase().includes('exclusion')
    )
    .map((c) => ({
      uid: c.study_criteria_uid,
      label: `${c.order}. ${c.criteria ? c.criteria.name_plain : (c.template?.name_plain ?? '')}`,
    }))
)

watch(
  () => props.open,
  async (isOpen) => {
    if (!isOpen) return
    await loadCriteria()
  },
  { immediate: true }
)

function resetCriteria() {
  allCriteria.value = []
  selectedInclusionUids.value = []
  selectedExclusionUids.value = []
  originalInclusionUids.value = []
  originalExclusionUids.value = []
}

async function loadCriteria() {
  const populationUid = props.population?.uid
  loadingCriteria.value = true
  try {
    const resp = await study.getStudyCriteria(
      studiesGeneralStore.selectedStudy.uid
    )
    const seen = new Set()
    allCriteria.value = (resp.data.items ?? []).filter((c) => {
      if (seen.has(c.study_criteria_uid)) return false
      seen.add(c.study_criteria_uid)
      return true
    })
    const assignedUids = populationUid
      ? allCriteria.value
          .filter((c) =>
            (c.study_design_population_uids ?? []).includes(populationUid)
          )
          .map((c) => c.study_criteria_uid)
      : []
    selectedInclusionUids.value = inclusionCriteria.value
      .map((c) => c.uid)
      .filter((uid) => assignedUids.includes(uid))
    selectedExclusionUids.value = exclusionCriteria.value
      .map((c) => c.uid)
      .filter((uid) => assignedUids.includes(uid))
    originalInclusionUids.value = [...selectedInclusionUids.value]
    originalExclusionUids.value = [...selectedExclusionUids.value]
  } finally {
    loadingCriteria.value = false
  }
}

// Applies the add/remove operations one by one (each is an independent API
// call) and reports which ones actually succeeded, so a retry only attempts
// the operations that failed and the selection stays in sync with reality.
async function applyCriteriaChanges(studyUid, populationUid) {
  const toAdd = [
    ...selectedInclusionUids.value.filter(
      (uid) => !originalInclusionUids.value.includes(uid)
    ),
    ...selectedExclusionUids.value.filter(
      (uid) => !originalExclusionUids.value.includes(uid)
    ),
  ]
  const toRemove = [
    ...originalInclusionUids.value.filter(
      (uid) => !selectedInclusionUids.value.includes(uid)
    ),
    ...originalExclusionUids.value.filter(
      (uid) => !selectedExclusionUids.value.includes(uid)
    ),
  ]

  const operations = [
    ...toAdd.map((criteriaUid) => ({ criteriaUid, op: 'add' })),
    ...toRemove.map((criteriaUid) => ({ criteriaUid, op: 'remove' })),
  ]

  const results = await Promise.allSettled(
    operations.map(({ criteriaUid, op }) => {
      const criterion = allCriteria.value.find(
        (c) => c.study_criteria_uid === criteriaUid
      )
      const currentUids = criterion?.study_design_population_uids ?? []
      const newUids =
        op === 'add'
          ? currentUids.includes(populationUid)
            ? currentUids
            : [...currentUids, populationUid]
          : currentUids.filter((uid) => uid !== populationUid)
      return study.updateStudyCriteriaStudyDesignPopulation(
        studyUid,
        criteriaUid,
        newUids
      )
    })
  )

  const failedCount = results.filter((r) => r.status === 'rejected').length

  // Only mark the successfully applied changes as the new baseline, so a
  // retry only attempts the operations that actually failed.
  results.forEach((result, index) => {
    if (result.status !== 'fulfilled') return
    const { criteriaUid, op } = operations[index]
    if (op === 'add') {
      if (selectedInclusionUids.value.includes(criteriaUid)) {
        originalInclusionUids.value = [
          ...new Set([...originalInclusionUids.value, criteriaUid]),
        ]
      }
      if (selectedExclusionUids.value.includes(criteriaUid)) {
        originalExclusionUids.value = [
          ...new Set([...originalExclusionUids.value, criteriaUid]),
        ]
      }
    } else {
      originalInclusionUids.value = originalInclusionUids.value.filter(
        (uid) => uid !== criteriaUid
      )
      originalExclusionUids.value = originalExclusionUids.value.filter(
        (uid) => uid !== criteriaUid
      )
    }
  })

  return failedCount
}

function close() {
  emit('close')
  notificationHub.clearErrors()
  resetCriteria()
}

async function submit() {
  notificationHub.clearErrors()
  const studyUid = studiesGeneralStore.selectedStudy.uid
  const populationUid = props.population?.uid

  try {
    const failedCount = await applyCriteriaChanges(studyUid, populationUid)
    if (failedCount > 0) {
      notificationHub.add({
        msg: t('StudyDesignPopulationCriteriaForm.partial_failure', {
          count: failedCount,
        }),
        type: 'warning',
        timeout: 0,
      })
      form.value.working = false
      return
    }
    notificationHub.add({
      msg: t('StudyDesignPopulationCriteriaForm.save_success'),
    })
    form.value.working = false
    emit('saved')
    close()
  } catch {
    form.value.working = false
  }
}
</script>
