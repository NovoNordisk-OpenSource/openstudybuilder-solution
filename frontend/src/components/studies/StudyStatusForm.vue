<template>
  <SimpleFormDialog
    ref="formRef"
    :title="dialogLabels.title"
    :help-items="helpItems"
    :open="open"
    max-width="1200px"
    :action-label="dialogLabels.title"
    :scrollable="false"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <table
        class="mt-4"
        :aria-label="$t('StudyStructureOverview.table_caption')"
      >
        <thead>
          <tr>
            <th
              v-for="header in headers"
              :key="header.key"
              scope="col"
              style="color: white"
            >
              {{ header.title }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td v-for="(header, index) in headers" :key="header.key">
              <StatusChip
                v-if="index === 0"
                :status="
                  getValueByColumn(
                    studiesGeneralStore.selectedStudy,
                    header.key
                  )
                "
                :outlined="false"
              />
              <div v-else>
                {{
                  getValueByColumn(
                    studiesGeneralStore.selectedStudy,
                    header.key
                  )
                }}
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <v-form ref="observer" class="mt-5">
        <v-row>
          <v-col cols="5"
            ><div class="label-font">{{ dialogLabels.reason }}</div>
            <v-select
              v-model="form.reason_for_change_uid"
              :items="reasons"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              data-cy="change-reason"
              :rules="[formRules.required]"
              @update:model-value="updateVersions"
            />
          </v-col>
          <v-col v-if="action !== 'unlock'">
            <div class="label-font">
              {{
                $t('Study.protocol_header_version') +
                (form.reason_for_change_uid &&
                form.reason_for_change_uid === finalProtocolReasonUid
                  ? $t('_global.required')
                  : $t('_global.optional'))
              }}
            </div>
            <div>
              <input
                v-model="form.protocol_header_major_version"
                :class="{
                  'tiny-native-input': true,
                  'tiny-native-input--error': majorVersionWarning,
                }"
                data-cy="major-version"
                @input="onVersionInput"
              />
              .
              <input
                v-model="form.protocol_header_minor_version"
                class="tiny-native-input"
                data-cy="minor-version"
                :disabled="
                  form.reason_for_change_uid &&
                  form.reason_for_change_uid === finalProtocolReasonUid
                "
                @input="onVersionInput"
              />
              <div v-if="majorVersionWarning" class="error-font">
                {{ $t('Study.major_version_warning') }}
              </div>
            </div>
          </v-col>
        </v-row>
        <v-row>
          <v-col v-if="props.action === 'unlock'">
            <v-textarea
              v-model="form.other_reason_for_unlocking"
              :label="dialogLabels.desc"
              data-cy="unlock-reason"
              auto-grow
              persistent-hint
              :placeholder="dialogLabels.descPlaceholder"
              width="60%"
            />
          </v-col>
          <v-col
            v-if="
              ['lock', 'release'].includes(props.action) &&
              form.reason_for_change_uid === otherReasonUid
            "
          >
            <v-textarea
              v-model="form.other_reason_for_locking_releasing"
              :label="$t('Study.other_reason_for_locking_releasing')"
              class="mb-n4"
              data-cy="lock-release-other-reason"
              auto-grow
              persistent-hint
              :rules="[formRules.required]"
              :placeholder="$t('StudyStatusForm.other_reason_lock_desc')"
              width="60%"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col v-if="['lock', 'release'].includes(props.action)">
            <v-textarea
              v-model="form.change_description"
              :label="dialogLabels.desc"
              data-cy="lock-release-description"
              auto-grow
              persistent-hint
              :placeholder="dialogLabels.descPlaceholder"
              width="60%"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import api from '@/api/study'
import { inject, computed, ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import terms from '@/api/controlledTerminology/terms'

const props = defineProps({
  action: {
    type: String,
    default: '',
  },
  helpItems: {
    type: Array,
    default: () => [],
  },
  lastVersion: {
    type: String,
    default: null,
  },
  open: Boolean,
})

const { t } = useI18n()
const studiesGeneralStore = useStudiesGeneralStore()
const notificationHub = inject('notificationHub')
const formRules = inject('formRules')

const emit = defineEmits(['close', 'statusChanged'])

const observer = ref()
const formRef = ref()
const majorVersionWarning = ref(false)

const form = ref({})
const headers = [
  {
    title: t('Study.status'),
    key: 'current_metadata.version_metadata.study_status',
  },
  {
    title: t('Study.clinical_programme'),
    key: 'current_metadata.identification_metadata.clinical_programme_name',
  },
  {
    title: t('Study.project_number'),
    key: 'current_metadata.identification_metadata.project_number',
  },
  {
    title: t('Study.project_name'),
    key: 'current_metadata.identification_metadata.project_name',
  },
  {
    title: t('Study.study_number'),
    key: 'current_metadata.identification_metadata.study_number',
  },
  {
    title: t('Study.acronym'),
    key: 'current_metadata.identification_metadata.study_acronym',
  },
]
const reasons = ref([])
const finalProtocolReasonUid = ref(null)
const otherReasonUid = ref(null)

const dialogLabels = computed(() => {
  const labels = {}
  switch (props.action) {
    case 'release':
      labels.title = t('StudyStatusForm.release_title')
      labels.reason = t('StudyStatusForm.release_reason')
      labels.desc = t('_global.change_description') + t('_global.optional')
      labels.descPlaceholder = t('StudyStatusForm.description_placeholder')
      break
    case 'lock':
      labels.title = t('StudyStatusForm.lock_title')
      labels.reason = t('StudyStatusForm.lock_reason')
      labels.desc = t('_global.change_description') + t('_global.optional')
      labels.descPlaceholder = t('StudyStatusForm.description_placeholder')
      break
    case 'unlock':
      labels.title = t('StudyStatusForm.unlock_title')
      labels.reason = t('StudyStatusForm.unlock_reason')
      labels.desc = t('StudyStatusForm.other_reason') + t('_global.optional')
      labels.descPlaceholder = t('StudyStatusForm.other_reason_desc')
      break
  }
  return labels
})

onMounted(() => {
  const codelist = ['lock', 'release'].includes(props.action)
    ? 'reasonForLock'
    : 'reasonForUnlock'
  terms.getTermsByCodelist(codelist).then((resp) => {
    reasons.value = resp.data.items
    finalProtocolReasonUid.value = reasons.value.find(
      (reason) => reason.submission_value === 'FINAL_PROTOCOL'
    )?.term_uid
    otherReasonUid.value = reasons.value.find(
      (reason) => reason.submission_value === 'OTHER'
    )?.term_uid
  })
  setLastVersion()
})

function setLastVersion() {
  if (props.lastVersion) {
    const parts = props.lastVersion.split('.')
    form.value.protocol_header_major_version = Number(parts[0])
    form.value.protocol_header_minor_version = Number(parts[1])
  }
}

function updateVersions() {
  checkMajorVersionWarning()
  if (form.value.reason_for_change_uid === finalProtocolReasonUid.value)
    form.value.protocol_header_minor_version = 0
}

function onVersionInput() {
  try {
    updateVersionField('protocol_header_major_version')
    updateVersionField('protocol_header_minor_version')
    checkMajorVersionWarning()
  } catch (error) {
    console.error(error)
  }
}

function updateVersionField(key) {
  const val = form.value[key]
  if (typeof val === 'number') return
  const digits = String(val ?? '').replace(/\D/g, '')
  form.value[key] = parseIntOrNull(digits)
}

function parseIntOrNull(str) {
  if (str == null) return null
  const n = parseInt(String(str).trim())
  return Number.isNaN(n) ? null : n
}

function close() {
  notificationHub.clearErrors()
  form.value = {}
  observer.value.reset()
  emit('close')
}

function getValueByColumn(item, columnName) {
  const keys = columnName.split('.')
  return keys.reduce((acc, key) => (acc ? acc[key] : undefined), item)
}

function checkMajorVersionWarning() {
  if (
    form.value.reason_for_change_uid === finalProtocolReasonUid.value &&
    !form.value.protocol_header_major_version
  ) {
    majorVersionWarning.value = true
    return true
  }
  majorVersionWarning.value = false
  return false
}

async function submit() {
  notificationHub.clearErrors()
  try {
    if (checkMajorVersionWarning()) {
      return
    }
    if (form.value.reason_for_change_uid !== otherReasonUid.value)
      form.value.other_reason_for_locking_releasing = null

    if (props.action === 'release') {
      await api.releaseStudy(studiesGeneralStore.selectedStudy.uid, form.value)
      notificationHub.add({
        msg: t('StudyStatusForm.release_success'),
        type: 'success',
      })
    } else if (props.action === 'lock') {
      const resp = await api.lockStudy(
        studiesGeneralStore.selectedStudy.uid,
        form.value
      )
      await studiesGeneralStore.selectStudy(resp.data)
      notificationHub.add({
        msg: t('StudyStatusForm.lock_success'),
        type: 'success',
      })
    } else {
      const resp = await api.unlockStudy(
        studiesGeneralStore.selectedStudy.uid,
        form.value
      )
      await studiesGeneralStore.selectStudy(resp.data)
      notificationHub.add({
        msg: t('StudyStatusForm.unlock_success'),
        type: 'success',
      })
    }
    emit('statusChanged')
    close()
  } finally {
    formRef.value.working = false
  }
}
</script>

<style scoped lang="scss">
table {
  text-align: left;
  border-spacing: 0px;
  border-collapse: separate;
  overflow: hidden;
}
td,
th {
  border: 1px solid gray;
  padding-inline: 20px;
  padding-block: 6px;
  color: rgb(var(--v-theme-nnTrueBlue));
}
table {
  border: solid gray 1px;
  border-radius: 10px;
  font-size: 14px;
}

thead {
  font-size: 12px;
}

thead > tr:first-of-type {
  background-color: rgb(var(--v-theme-nnTrueBlue));
}

.tiny-native-input {
  width: 2.2rem;
  min-width: 2.2rem;
  height: 2.2rem;
  padding: 0.15rem;
  text-align: center;
  font-size: 1rem;
  border: 1px solid #919191;
  border-radius: 8px;
  box-sizing: content-box;
}

.tiny-native-input--error {
  border-color: red;
}

.label-font {
  font-size: small;
  color: rgb(var(--v-theme-darkGrey));
}
.error-font {
  font-size: 12px;
  color: #f44336;
}
</style>
