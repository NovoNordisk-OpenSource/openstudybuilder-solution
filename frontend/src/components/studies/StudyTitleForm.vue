<template>
  <v-card elevation="0" class="nn-grey">
    <v-card-title class="d-flex align-center">
      <div class="page-title">
        {{ $t('StudyTitleForm.title') }} ({{ studiesGeneralStore.studyId }})
      </div>
    </v-card-title>
    <v-card-text ref="container" class="mb-12 pb-12">
      <div class="bg-white pa-6 mb-6 form-panel">
        <v-form ref="observer">
          <div class="input-block mb-5">
            <div class="d-flex align-center mb-1">
              <label class="field-label">{{
                $t('StudyTitleForm.title_label')
              }}</label>
              <v-spacer />
              <span class="counter"
                >{{ currentTitleLength }} / {{ maxTitleLength }}</span
              >
            </div>
            <v-textarea
              v-model="form.study_title"
              data-cy="study-title"
              :maxlength="maxTitleLength"
              :hint="$t('StudyTitleForm.title_hint')"
              persistent-hint
              rows="2"
              class="mb-1"
              auto-grow
              :rules="[formRules.required]"
            />
          </div>
          <div class="input-block">
            <div class="d-flex align-center mb-1">
              <label class="field-label">{{
                $t('StudyTitleForm.short_title')
              }}</label>
              <v-spacer />
              <span class="counter"
                >{{ currentShortTitleLength }} / {{ shortTitleMaxLength }}</span
              >
            </div>
            <v-textarea
              v-model="form.study_short_title"
              data-cy="short-study-title"
              :maxlength="shortTitleMaxLength"
              :hint="$t('StudyTitleForm.short_title_hint')"
              persistent-hint
              rows="2"
              class="mb-1"
              auto-grow
              :rules="[formRules.required]"
            />
          </div>
        </v-form>
      </div>
      <div class="d-flex align-center text-grey font-italic">
        <v-icon size="18" class="mr-1">mdi-information-outline</v-icon>
        <span>{{ $t('StudyTitleForm.global_help') }}</span>
      </div>
      <div class="table-panel mt-4">
        <div class="table-header px-4 py-3">
          <div class="text-label-large font-weight-bold">
            {{ $t('StudyTitleForm.copy_title') }}
          </div>
        </div>
        <v-data-table
          :headers="headers"
          :items="studies"
          :loading="loading"
          height="35vh"
        >
          <template #[`item.actions`]="{ item }">
            <v-btn
              data-cy="copy-title"
              icon="mdi-content-copy"
              color="primary"
              :title="$t('StudyTitleForm.copy_title')"
              variant="text"
              @click="copyTitle(item)"
            />
          </template>
        </v-data-table>
      </div>
    </v-card-text>
    <v-card-actions class="bg-white fixed-actions border-t-thin">
      <v-col>
        <v-btn
          class="secondary-btn"
          variant="outlined"
          width="120px"
          rounded="xl"
          @click="close"
        >
          {{ $t('_global.cancel') }}
        </v-btn>
      </v-col>
      <v-spacer />
      <div class="mx-2">
        <v-row>
          <v-col>
            <v-btn
              data-cy="save-button"
              color="secondary"
              variant="flat"
              width="120px"
              rounded="xl"
              :loading="working"
              @click.stop="submit"
            >
              {{ $t('_global.save') }}
            </v-btn>
          </v-col>
        </v-row>
      </div>
    </v-card-actions>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  </v-card>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import study from '@/api/study'
import _isEqual from 'lodash/isEqual'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  description: {
    type: Object,
    default: undefined,
  },
})

const emit = defineEmits(['close', 'updated'])

const studiesGeneralStore = useStudiesGeneralStore()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')
const { t } = useI18n()

const observer = ref()
const confirm = ref()

const form = ref({})
const maxTitleLength = 600
const shortTitleMaxLength = maxTitleLength / 2
const studies = ref([])
const working = ref(false)

function cloneDescription(description) {
  return description ? JSON.parse(JSON.stringify(description)) : {}
}

const headers = computed(() => [
  { title: '', key: 'actions', width: '1%' },
  {
    title: t('StudyTitleForm.project_id'),
    key: 'current_metadata.identification_metadata.project_number',
  },
  {
    title: t('StudyTitleForm.project_name'),
    key: 'current_metadata.identification_metadata.project_name',
  },
  {
    title: t('StudyTitleForm.study_id'),
    key: 'current_metadata.identification_metadata.study_id',
  },
  {
    title: t('StudyTitleForm.study_title'),
    key: 'current_metadata.study_description.study_title',
  },
  {
    title: t('StudyTitleForm.short_title'),
    key: 'current_metadata.study_description.study_short_title',
  },
])

const loading = ref(false)

const currentTitleLength = computed(() => {
  if (form.value.study_title) {
    return form.value.study_title.length
  }
  return 0
})

const currentShortTitleLength = computed(() => {
  if (form.value.study_short_title) {
    return form.value.study_short_title.length
  }
  return 0
})

watch(
  () => props.description,
  (value) => {
    if (value) {
      form.value = cloneDescription(value)
    }
  },
  { immediate: true }
)

onMounted(() => {
  loading.value = true
  study
    .getAll()
    .then((resp) => {
      studies.value = resp.data.items
    })
    .finally(() => {
      loading.value = false
    })
})

async function close() {
  notificationHub.clearErrors()
  if (_isEqual(form.value, props.description)) {
    emit('close')
    return
  }
  const options = {
    type: 'warning',
    cancelLabel: t('_global.cancel'),
    agreeLabel: t('_global.continue'),
  }
  if (await confirm.value.open(t('_global.cancel_changes'), options)) {
    form.value = cloneDescription(props.description)
    emit('close')
  }
}

function copyTitle(studyItem) {
  form.value.study_title =
    studyItem.current_metadata.study_description.study_title
  form.value.study_short_title =
    studyItem.current_metadata.study_description.study_short_title
}

async function submit() {
  const { valid } = await observer.value.validate()
  if (!valid) return

  notificationHub.clearErrors()

  if (_isEqual(form.value, props.description)) {
    notificationHub.add({
      msg: t('_global.no_changes'),
      type: 'info',
    })
    close()
    return
  }
  working.value = true
  try {
    await study.updateStudyDescription(
      studiesGeneralStore.selectedStudy.uid,
      form.value
    )
    emit('updated')
    notificationHub.add({
      msg: t('StudyTitleForm.update_success'),
    })
    emit('close')
  } finally {
    working.value = false
  }
}
</script>

<style scoped>
.form-panel {
  border: 1px solid rgb(var(--v-theme-greyBackground));
  border-radius: 12px;
}

.input-block {
  border: 1px solid rgb(var(--v-theme-greyBackground));
  border-radius: 10px;
  padding: 12px 12px 4px;
}

.field-label {
  font-weight: 600;
  font-size: 14px;
  color: rgb(var(--v-theme-darkGrey)) !important;
}

.counter {
  color: rgb(var(--v-theme-greyText));
  font-size: 12px;
}

.table-panel {
  border: 1px solid rgb(var(--v-theme-greyBackground));
  border-radius: 12px;
  overflow: hidden;
}

.table-header {
  background: rgb(var(--v-theme-nnLightBlue100));
}
</style>
