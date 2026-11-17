<template>
  <div class="d-flex flex-column flex-grow-1 ga-2 pa-3 selector-box">
    <div class="d-flex align-center justify-space-between">
      <v-switch
        :model-value="isFile"
        :label="$t('CRFCompare.use_file')"
        color="primary"
        density="compact"
        hide-details
        :data-cy="`${dataCy}-use-file`"
        @update:model-value="onSwitch"
      />
      <v-tooltip
        v-if="isFile"
        :text="$t('CRFCompare.file_hint')"
        location="top"
        max-width="320"
      >
        <template #activator="{ props: tooltipProps }">
          <v-icon
            v-bind="tooltipProps"
            icon="mdi-information-outline"
            size="small"
            :data-cy="`${dataCy}-file-hint`"
          />
        </template>
      </v-tooltip>
    </div>
    <div class="d-flex ga-3">
      <template v-if="isFile">
        <v-file-input
          v-model="xmlFile"
          accept=".xml,text/xml,application/xml"
          :label="$t('CRFCompare.xml_file')"
          :data-cy="`${dataCy}-xml-file`"
          :loading="fileLoading"
          prepend-icon=""
          prepend-inner-icon="mdi-paperclip"
          hide-details
          clearable
          style="min-width: 160px"
          @update:model-value="parseFile"
        />
        <v-select
          v-if="!isCollection && fileForms.length > 1"
          v-model="selection.uid"
          :items="fileForms"
          item-title="name"
          item-value="uid"
          :label="$t('CRFCompare.form_in_file')"
          :data-cy="`${dataCy}-file-form`"
          hide-details
          style="min-width: 140px"
          @update:model-value="onFileFormChange"
        />
        <v-tooltip :text="$t('CRFCompare.mapper_file')" location="top">
          <template #activator="{ props: tooltipProps }">
            <v-btn
              v-bind="tooltipProps"
              icon="mdi-file-cog-outline"
              variant="text"
              size="small"
              class="align-self-center"
              :color="showMapper || mapperFile ? 'primary' : undefined"
              :data-cy="`${dataCy}-mapper-toggle`"
              @click="showMapper = !showMapper"
            />
          </template>
        </v-tooltip>
      </template>
      <template v-else>
        <v-select
          v-model="selection.library"
          :items="libraries"
          :label="$t('CRFCompare.library')"
          :data-cy="`${dataCy}-library`"
          hide-details
          style="min-width: 80px"
          @update:model-value="onLibraryChange"
        />
        <v-autocomplete
          v-model="selection.uid"
          :items="elements"
          item-title="name"
          item-value="uid"
          :label="
            isCollection
              ? $t('CRFCompare.collection')
              : $t('CRFCompare.crf_form')
          "
          :data-cy="`${dataCy}-${isCollection ? 'collection' : 'form'}`"
          :loading="formsLoading"
          :disabled="!selection.library"
          hide-details
          style="min-width: 100px"
          @update:model-value="onFormChange"
        />
        <v-select
          v-model="selection.version"
          :items="versions"
          item-title="title"
          item-value="version"
          :label="$t('CRFCompare.version')"
          :data-cy="`${dataCy}-version`"
          :loading="versionsLoading"
          :disabled="!selection.uid"
          hide-details
          style="min-width: 80px"
          @update:model-value="emitSelection"
        />
      </template>
    </div>
    <template v-if="isFile">
      <v-file-input
        v-if="showMapper || mapperFile"
        v-model="mapperFile"
        accept=".csv,text/csv"
        :label="$t('CRFCompare.mapper_file')"
        :data-cy="`${dataCy}-mapper-file`"
        prepend-icon=""
        prepend-inner-icon="mdi-paperclip"
        density="compact"
        hide-details
        clearable
        @update:model-value="parseFile"
      />
    </template>
  </div>
</template>

<script setup>
import { computed, inject, reactive, ref, watch } from 'vue'
import crfs from '@/api/crfs'
import { useI18n } from 'vue-i18n'
import { useCrfCompare } from '@/composables/crfCompare'

const props = defineProps({
  modelValue: {
    type: Object,
    required: true,
  },
  libraries: {
    type: Array,
    default: () => [],
  },
  mode: {
    type: String,
    default: 'form',
  },
  dataCy: {
    type: String,
    default: 'crf-compare-selector',
  },
})
const emit = defineEmits(['update:modelValue'])

const { t } = useI18n()
const notificationHub = inject('notificationHub')
const { loadFormVersions, loadCollectionVersions, loadFile } = useCrfCompare()

const isCollection = computed(() => props.mode === 'collection')

// source is 'db' or 'file'. For a file, file is { name, xml, mapper, forms }
// (forms already normalized) and version is the placeholder 'file'.
const selection = reactive({ source: 'db', file: null, ...props.modelValue })
const isFile = computed(() => selection.source === 'file')
const showMapper = ref(false)
const fileForms = computed(() => selection.file?.forms ?? [])
const xmlFile = ref(selection.file?.xml ?? null)
const mapperFile = ref(selection.file?.mapper ?? null)
const fileLoading = ref(false)
let parseCounter = 0
const elements = ref([])
const versions = ref([])
const formsLoading = ref(false)
const versionsLoading = ref(false)

// v-file-input yields a File, or an array of them in older versions.
const firstFile = (value) => (Array.isArray(value) ? value[0] : value) ?? null

// Another component (the swap button) can replace the whole selection.
watch(
  () => props.modelValue,
  async (value) => {
    if (
      value.library === selection.library &&
      value.uid === selection.uid &&
      value.version === selection.version &&
      value.source === selection.source &&
      value.file === selection.file
    ) {
      return
    }
    Object.assign(selection, { source: 'db', file: null }, value)
    xmlFile.value = selection.file?.xml ?? null
    mapperFile.value = selection.file?.mapper ?? null
    await Promise.all([
      value.library ? fetchElements(value.library) : (elements.value = []),
      value.uid && selection.source === 'db'
        ? fetchVersions(value.uid)
        : (versions.value = []),
    ])
  }
)

if (selection.source === 'db' && selection.library) {
  fetchElements(selection.library)
}
if (selection.source === 'db' && selection.uid) {
  fetchVersions(selection.uid)
}

async function fetchElements(library) {
  formsLoading.value = true
  try {
    const resp = await crfs.get(isCollection.value ? 'study-events' : 'forms', {
      params: { library_name: library, page_size: 0, fields: 'uid,name' },
    })
    elements.value = resp.data.items
  } finally {
    formsLoading.value = false
  }
}

async function fetchVersions(uid) {
  versionsLoading.value = true
  try {
    const entries = await (isCollection.value
      ? loadCollectionVersions(uid)
      : loadFormVersions(uid))
    versions.value = entries.map((entry) => ({
      ...entry,
      title: `${entry.version} (${entry.status})`,
    }))
  } finally {
    versionsLoading.value = false
  }
}

function emitSelection() {
  emit('update:modelValue', { ...selection })
}

function onSwitch(value) {
  selection.source = value ? 'file' : 'db'
  resetSelection()
}

function resetSelection() {
  parseCounter++
  showMapper.value = false
  Object.assign(selection, {
    library: null,
    uid: null,
    version: null,
    file: null,
  })
  xmlFile.value = null
  mapperFile.value = null
  elements.value = []
  versions.value = []
  emitSelection()
}

function onFileFormChange(uid) {
  selection.version = uid ? 'file' : null
  emitSelection()
}

// Parsing happens as soon as a file is chosen so a file with several forms can
// offer a form to pick. API errors are already toasted by the repository.
async function parseFile() {
  const xml = firstFile(xmlFile.value)
  const mapper = firstFile(mapperFile.value)
  const current = ++parseCounter
  Object.assign(selection, { uid: null, version: null, file: null })
  emitSelection()
  if (!xml) {
    fileLoading.value = false
    return
  }
  try {
    const forms = await loadFile(xml, { mapperFile: mapper })
    if (current !== parseCounter) return
    if (forms.length === 0) {
      notificationHub.add({
        msg: t('CRFCompare.no_forms_in_file'),
        type: 'warning',
      })
      return
    }
    selection.file = { name: xml.name, xml, mapper, forms }
    if (isCollection.value) {
      selection.uid = `file:${xml.name}`
    } else if (forms.length === 1) {
      selection.uid = forms[0].uid
    }
    selection.version = selection.uid ? 'file' : null
    emitSelection()
  } catch {
    // already reported by the repository interceptor
  } finally {
    if (current === parseCounter) fileLoading.value = false
  }
}

async function onLibraryChange(library) {
  selection.uid = null
  selection.version = null
  elements.value = []
  versions.value = []
  emitSelection()
  if (library) {
    await fetchElements(library)
  }
}

async function onFormChange(uid) {
  selection.version = null
  versions.value = []
  emitSelection()
  if (uid) {
    await fetchVersions(uid)
    // The audit trail is newest first, so this preselects the latest version.
    selection.version = versions.value[0]?.version ?? null
    emitSelection()
  }
}
</script>

<style scoped>
.selector-box {
  background-color: rgb(var(--v-theme-dfltBackgroundLight1));
  border-radius: 8px;
}
</style>
