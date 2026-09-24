<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('StudyDataCompleteness.admin_title') }}
    </div>
    <v-card>
      <v-card-text>
        <v-alert
          color="nnLightBlue200"
          icon="mdi-information-outline"
          class="text-nnTrueBlue mx-4 my-2"
        >
          {{ $t('StudyDataCompleteness.admin_info') }}
        </v-alert>

        <v-autocomplete
          v-model="study"
          :items="studies"
          :item-title="(value) => getStudyLabel(value)"
          item-value="uid"
          :label="t('StudyDataCompleteness.admin_select_study')"
          data-cy="select-study-to-tag"
          class="mx-4 mt-12 mb-2"
          return-object
        ></v-autocomplete>

        <div class="mx-4 mb-2 d-flex align-center ga-2 new-tag-row">
          <v-text-field
            v-model="newTagName"
            :label="t('StudyDataCompleteness.admin_new_tag')"
            data-cy="tag-name"
            hide-details
            :loading="addingTag"
            @keydown.enter.prevent="addTag"
          />
          <v-btn
            color="primary"
            :loading="addingTag"
            :disabled="!canAddTag"
            data-cy="save-tag"
            @click="addTag"
          >
            {{ $t('_global.save') }}
          </v-btn>
        </div>

        <v-data-table
          :headers="headers"
          :items="tags"
          :items-per-page="-1"
          class="mx-4 my-6"
        >
          <template #[`item.actions`]="{ item }">
            <v-switch
              v-model="item.enabled"
              hide-details
              @update:model-value="(value) => setTagState(item, value)"
            />
          </template>
          <template #bottom></template>
        </v-data-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/api/study'
import tagsApi from '@/api/completenessTags'

const { t } = useI18n()
const studies = ref([])
const study = ref(null)
const tags = ref([])
const newTagName = ref('')
const addingTag = ref(false)

const canAddTag = computed(() => {
  return !!newTagName.value.trim() && !addingTag.value
})

watch(study, async (newStudy) => {
  setCompletenessTags(newStudy)
})

const headers = [
  {
    key: 'actions',
    title: t('StudyDataCompleteness.admin_col_complete'),
    width: '50px',
  },
  { key: 'name', title: t('StudyDataCompleteness.admin_col_section') },
]

async function setTagState(tag, value) {
  const previous = !value
  try {
    if (value) {
      await api.enableTag(study.value.uid, { uid: tag.uid })
      study.value.data_completeness_tags = [
        ...(study.value.data_completeness_tags || []),
        tag.name,
      ]
    } else {
      await api.disableTag(study.value.uid, tag.uid)
      study.value.data_completeness_tags = (
        study.value.data_completeness_tags || []
      ).filter((name) => name !== tag.name)
    }
  } catch (_error) {
    tag.enabled = previous
  }
}

async function addTag() {
  const name = newTagName.value.trim()
  if (!name || addingTag.value) {
    return
  }

  const exists = tags.value.some(
    (tag) =>
      String(tag.name || '')
        .trim()
        .toLowerCase() === name.toLowerCase()
  )
  if (exists) {
    return
  }

  addingTag.value = true
  try {
    await tagsApi.add({ name })
    newTagName.value = ''
    await fetchTags()
  } finally {
    addingTag.value = false
  }
}

function setCompletenessTags(newStudy) {
  tags.value.forEach((tag) => {
    tag.enabled = newStudy?.data_completeness_tags?.includes(tag.name) ?? false
  })
}

function getStudyLabel(study) {
  const id =
    study?.id || study?.current_metadata?.identification_metadata?.study_id
  const acronym =
    study?.acronym ||
    study?.current_metadata?.identification_metadata?.study_acronym
  if (id && acronym) {
    return `${id} (${acronym})`
  } else if (id) {
    return id
  } else if (acronym) {
    return acronym
  }
}

api.getAllList().then((resp) => {
  studies.value = resp.data
  study.value = studies.value[0] || null
})

async function fetchTags() {
  const resp = await tagsApi.get()
  tags.value = resp.data
  setCompletenessTags(study.value)
}

fetchTags()
</script>

<style scoped>
.v-data-table {
  width: auto !important;
}

.new-tag-row {
  width: 50%;
}
</style>
