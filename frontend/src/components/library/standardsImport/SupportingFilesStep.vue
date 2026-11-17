<template>
  <div>
    <v-alert
      v-if="!props.effectiveDate"
      type="info"
      variant="tonal"
      :text="$t('StandardsImport.supporting_files_need_packages')"
    />

    <template v-else>
      <!-- Pairing workbooks: an input to the analysis. -->
      <template v-if="shows('pairings')">
        <div class="text-h6">
          {{ $t('StandardsImport.pairing_workbooks') }}
        </div>
        <div class="text-body-2 text-medium-emphasis mt-1">
          {{ $t('StandardsImport.pairing_workbook_purpose') }}
        </div>

        <DownloadFromCdisc
          class="mt-2"
          :href="pairedViewUrl"
          :label="$t('StandardsImport.download_paired_view')"
          :note="$t('StandardsImport.cdisc_account_required')"
        />

        <v-row align="start" class="mt-1">
          <v-col cols="12" md="6">
            <v-file-input
              v-model="selectedPairingFile"
              density="compact"
              accept=".xlsx"
              chips
              show-size
              prepend-icon=""
              prepend-inner-icon="mdi-paperclip"
              :label="$t('StandardsImport.choose_pairing_workbook')"
              :hint="$t('StandardsImport.pairing_workbook_hint')"
              persistent-hint
              :disabled="disabled"
            />
          </v-col>
          <v-col cols="auto">
            <v-btn
              color="secondary"
              variant="flat"
              rounded="xl"
              :loading="uploadingPairing"
              :disabled="disabled || !selectedPairingFile"
              data-cy="standards-import-upload-pairing-workbook"
              @click="uploadPairing"
            >
              {{ $t('StandardsImport.upload') }}
            </v-btn>
          </v-col>
          <v-col cols="auto">
            <v-btn
              variant="outlined"
              rounded="xl"
              :loading="loadingPairings"
              @click="loadPairings"
            >
              {{ $t('StandardsImport.refresh') }}
            </v-btn>
          </v-col>
        </v-row>

        <v-alert
          v-if="pairingError"
          class="mt-2"
          type="error"
          variant="tonal"
          closable
          :text="pairingError"
        />

        <v-data-table
          class="mt-4"
          :headers="pairingHeaders"
          :items="workbooks"
          :loading="loadingPairings"
          item-value="source_file"
          :items-per-page="-1"
          :no-data-text="$t('StandardsImport.no_pairing_workbooks')"
          hide-default-footer
          data-cy="standards-import-pairings-table"
        >
          <template #[`item.skipped`]="{ item }">
            <span v-if="item.skipped === null" class="text-medium-emphasis">
              {{ $t('StandardsImport.not_recorded') }}
            </span>
            <span v-else-if="item.skipped === 0">0</span>
            <span v-else>
              {{ item.skipped }}
              <v-btn
                variant="text"
                density="compact"
                size="small"
                @click="showSkipped(item)"
              >
                {{ $t('StandardsImport.view_skipped') }}
              </v-btn>
            </span>
          </template>
        </v-data-table>

        <div
          v-if="expectedWorkbookCatalogues.length"
          class="text-body-2 text-medium-emphasis mt-2"
          data-cy="standards-import-expected-workbooks-note"
        >
          {{
            $t('StandardsImport.expected_workbooks_note', {
              catalogues: expectedWorkbookCatalogues.join(', '),
            })
          }}
        </div>
      </template>

      <v-divider v-if="shows('pairings') && shows('changelog')" class="my-8" />

      <!-- Terminology changes: commentary, not an input. -->
      <template v-if="shows('changelog')">
        <div class="text-h6">
          {{ $t('StandardsImport.terminology_changes') }}
        </div>
        <div class="text-body-2 text-medium-emphasis mt-1">
          {{ $t('StandardsImport.terminology_changes_purpose') }}
        </div>

        <div class="d-flex align-center flex-wrap mt-2">
          <v-icon
            icon="mdi-tray-arrow-down"
            size="small"
            color="primary"
            class="mr-2"
          />
          <span class="text-body-2 text-primary">
            {{ $t('StandardsImport.download_terminology_changes') }}
          </span>
          <v-btn
            v-for="link in terminologyChangesLinks"
            :key="link.label"
            variant="text"
            density="comfortable"
            rounded="xl"
            size="small"
            color="primary"
            class="px-2 ml-1"
            append-icon="mdi-open-in-new"
            :href="link.href"
            target="_blank"
            rel="noopener"
          >
            {{ link.label }}
          </v-btn>
        </div>

        <v-row align="start" class="mt-1">
          <v-col cols="12" md="6">
            <v-file-input
              v-model="selectedChangelogFile"
              density="compact"
              accept=".xls"
              chips
              show-size
              prepend-icon=""
              prepend-inner-icon="mdi-paperclip"
              :label="$t('StandardsImport.choose_changelog_workbook')"
              :hint="$t('StandardsImport.changelog_workbook_hint')"
              persistent-hint
              :disabled="disabled"
            />
          </v-col>
          <v-col cols="auto">
            <v-btn
              color="secondary"
              variant="flat"
              rounded="xl"
              :loading="uploadingChangelog"
              :disabled="disabled || !selectedChangelogFile"
              data-cy="standards-import-upload-changelog"
              @click="uploadChangelog"
            >
              {{ $t('StandardsImport.upload') }}
            </v-btn>
          </v-col>
          <v-col cols="auto">
            <v-btn
              variant="outlined"
              rounded="xl"
              :loading="loadingChangelog"
              @click="loadChangelog"
            >
              {{ $t('StandardsImport.refresh') }}
            </v-btn>
          </v-col>
        </v-row>

        <v-alert
          v-if="changelogError"
          class="mt-2"
          type="error"
          variant="tonal"
          closable
          :text="changelogError"
        />

        <v-data-table
          class="mt-4"
          :headers="changelogHeaders"
          :items="changelogSheets"
          :loading="loadingChangelog"
          item-value="catalogue"
          :items-per-page="-1"
          :no-data-text="$t('StandardsImport.no_changelog_files')"
          hide-default-footer
          data-cy="standards-import-changelog-table"
        >
          <template #[`item.source_file`]="{ item }">
            <span v-if="item.source_file">{{ item.source_file }}</span>
            <span v-else class="text-medium-emphasis">
              {{ $t('StandardsImport.not_recorded') }}
            </span>
          </template>
          <template #[`item.collapsed`]="{ item }">
            <span v-if="item.collapsed === null" class="text-medium-emphasis">
              {{ $t('StandardsImport.not_recorded') }}
            </span>
            <span v-else>{{ item.collapsed }}</span>
          </template>
        </v-data-table>
      </template>
    </template>

    <v-dialog v-model="skippedDialogOpen" max-width="600px">
      <v-card rounded="xl">
        <v-card-title>{{
          $t('StandardsImport.skipped_rows_title')
        }}</v-card-title>
        <v-divider />
        <v-card-text>
          <v-list>
            <v-list-item
              v-for="(row, index) in skippedRows"
              :key="index"
              :title="row"
            />
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="outlined" rounded @click="skippedDialogOpen = false">
            {{ $t('_global.close') }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import pairingsApi from '@/api/standardsImport/pairings'
import changelogApi from '@/api/standardsImport/changelog'
import configApi from '@/api/standardsImport/config'
import DownloadFromCdisc from '@/components/library/standardsImport/DownloadFromCdisc.vue'

const { t } = useI18n()
const notificationHub = inject('notificationHub')

const props = defineProps({
  effectiveDate: {
    type: String,
    default: '',
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  // Which halves to render. The release dashboard opens this component for the
  // pairing workbooks alone, since that is the task it offers; both halves show
  // when nothing is asked for in particular.
  sections: {
    type: Array,
    default: () => ['pairings', 'changelog'],
  },
})
const emit = defineEmits(['uploaded'])

const shows = (section) => props.sections.includes(section)

// Where CDISC publishes each file for this release. The paired view is SDTM only
// for now: SEND and ADaM sit at different paths, and a guessed URL 404s in a way
// that reads as "there is no such file for this release" rather than "the link
// is wrong". The terminology changes follow one path pattern for SDTM and ADaM.
//
// The two use different date formats in the filename, which is precisely the
// sort of thing not worth making anyone get right by hand.
const pairedViewUrl = computed(() =>
  props.effectiveDate
    ? 'https://www.cdisc.org/system/files/members/standard/terminology/' +
      `SDTM_paired_view_${props.effectiveDate.replaceAll('-', '_')}.xlsx`
    : ''
)
const terminologyChangesLinks = computed(() =>
  ['SDTM', 'ADaM'].map((standard) => ({
    label: standard,
    href:
      `https://evs.nci.nih.gov/ftp1/CDISC/${standard}/Archive/` +
      `${standard}%20Terminology%20Changes%20${props.effectiveDate}.xls`,
  }))
)

const pairingHeaders = [
  { title: t('StandardsImport.source_file'), key: 'source_file' },
  { title: t('StandardsImport.pairings'), key: 'pairings' },
  { title: t('StandardsImport.skipped'), key: 'skipped', sortable: false },
]

const changelogHeaders = [
  { title: t('StandardsImport.catalogue'), key: 'catalogue' },
  { title: t('StandardsImport.source_file'), key: 'source_file' },
  { title: t('StandardsImport.changelog_entries'), key: 'entries' },
  { title: t('StandardsImport.changelog_collapsed'), key: 'collapsed' },
]

const workbooks = ref([])
const selectedPairingFile = ref(null)
const loadingPairings = ref(false)
const uploadingPairing = ref(false)
const pairingError = ref(null)
const skippedDialogOpen = ref(false)
const skippedRows = ref([])
const expectedWorkbookCatalogues = ref([])

const changelogSheets = ref([])
const selectedChangelogFile = ref(null)
const loadingChangelog = ref(false)
const uploadingChangelog = ref(false)
const changelogError = ref(null)

// Skipped rows are reported back on upload but never stored, so they are only
// known for workbooks uploaded in this session. Keyed by source file.
const skippedBySourceFile = ref({})

// Same for the changes sheets: the API reports the filename it was given and
// how many rows it folded, and keeps neither. Keyed by catalogue, since that is
// what an upload replaces — re-uploading the same sheet under a different name
// overwrites rather than adds.
const uploadedByCatalogue = ref({})

function showSkipped(row) {
  skippedRows.value = skippedBySourceFile.value[row.source_file] || []
  skippedDialogOpen.value = true
}

// The API has no "list staged workbooks" endpoint — it returns the individual
// pairings, each stamped with the workbook it came from. Group them back up so
// an already-uploaded workbook still shows on a revisit.
function loadPairings() {
  if (!props.effectiveDate) {
    workbooks.value = []
    return
  }
  loadingPairings.value = true
  pairingsApi
    .getAll(props.effectiveDate)
    .then((response) => {
      const counts = new Map()
      for (const pairing of response.data || []) {
        counts.set(
          pairing.source_file,
          (counts.get(pairing.source_file) || 0) + 1
        )
      }
      workbooks.value = [...counts.entries()].map(([sourceFile, pairings]) => ({
        source_file: sourceFile,
        pairings,
        skipped: skippedBySourceFile.value[sourceFile]?.length ?? null,
      }))
    })
    .finally(() => {
      loadingPairings.value = false
    })
}

// Purely informational — the admin-configured list of catalogues that usually ship a
// workbook, not tied to what has actually been uploaded for this release.
function loadExpectedWorkbooks() {
  configApi
    .getCataloguePriority()
    .then((response) => {
      expectedWorkbookCatalogues.value = (response.data || [])
        .filter((entry) => entry.expects_workbook)
        .map((entry) => entry.catalogue_name)
    })
    .catch(() => {
      expectedWorkbookCatalogues.value = []
    })
}

// Likewise for the changes sheets, with one wrinkle: catalogues overlap, so a
// change both SDTM and SEND reported comes back as one entry carrying both.
// Counting it under each is right — each sheet really did say it — which is why
// this counts catalogues rather than entries.
function loadChangelog() {
  if (!props.effectiveDate) {
    changelogSheets.value = []
    return
  }
  loadingChangelog.value = true
  changelogApi
    .getAll(props.effectiveDate)
    .then((response) => {
      const counts = new Map()
      for (const entry of response.data || []) {
        for (const catalogue of entry.catalogues || []) {
          counts.set(catalogue, (counts.get(catalogue) || 0) + 1)
        }
      }
      changelogSheets.value = [...counts.entries()]
        .map(([catalogue, entries]) => ({
          catalogue,
          entries,
          source_file: uploadedByCatalogue.value[catalogue]?.source_file || '',
          collapsed: uploadedByCatalogue.value[catalogue]?.collapsed ?? null,
        }))
        .sort((a, b) => a.catalogue.localeCompare(b.catalogue))
    })
    .finally(() => {
      loadingChangelog.value = false
    })
}

const readAsArrayBuffer = (file) =>
  new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = () => reject(reader.error)
    reader.readAsArrayBuffer(file)
  })

const firstFile = (selection) =>
  Array.isArray(selection) ? selection[0] : selection

const uploadFailure = (exception) =>
  exception.response?.data?.message ||
  exception.message ||
  t('StandardsImport.upload_error')

async function uploadPairing() {
  const file = firstFile(selectedPairingFile.value)
  if (!file) {
    return
  }
  uploadingPairing.value = true
  pairingError.value = null
  try {
    const content = await readAsArrayBuffer(file)
    const { data } = await pairingsApi.upload(
      props.effectiveDate,
      file.name,
      content
    )
    skippedBySourceFile.value[data.source_file] = data.skipped || []
    notificationHub.add({
      type: 'success',
      msg: t('StandardsImport.upload_success', { count: 1 }),
    })
    selectedPairingFile.value = null
    emit('uploaded')
    loadPairings()
  } catch (exception) {
    pairingError.value = uploadFailure(exception)
  } finally {
    uploadingPairing.value = false
  }
}

async function uploadChangelog() {
  const file = firstFile(selectedChangelogFile.value)
  if (!file) {
    return
  }
  uploadingChangelog.value = true
  changelogError.value = null
  try {
    const content = await readAsArrayBuffer(file)
    const { data } = await changelogApi.upload(
      props.effectiveDate,
      file.name,
      content
    )
    uploadedByCatalogue.value[data.catalogue] = {
      source_file: data.source_file,
      collapsed: data.collapsed,
    }
    notificationHub.add({
      type: 'success',
      msg: t('StandardsImport.changelog_upload_success', {
        count: data.entries,
        catalogue: data.catalogue,
      }),
    })
    selectedChangelogFile.value = null
    // This upload still changes nothing about the release itself — not its status, not
    // what the import would do — but it does move `changelog_catalogues`, which the
    // release page's task box reports, so the parent is told to re-read the summary.
    emit('uploaded')
    loadChangelog()
  } catch (exception) {
    changelogError.value = uploadFailure(exception)
  } finally {
    uploadingChangelog.value = false
  }
}

function load() {
  if (shows('pairings')) {
    loadPairings()
  }
  if (shows('changelog')) {
    loadChangelog()
  }
}

watch(() => props.effectiveDate, load)
onMounted(load)
// Independent of the effective date — an org-wide setting, not scoped per release —
// so it loads once rather than refetching every time `load()` does.
onMounted(loadExpectedWorkbooks)
</script>
