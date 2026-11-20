<template>
  <v-card color="dfltBackground" rounded="xl">
    <v-card-title class="pt-4">
      <div class="page-title">
        {{ $t(`StandardsImport.history_title_${conceptType}`, { conceptId }) }}
      </div>
      <div class="text-body-2 text-medium-emphasis">
        {{
          $t('StandardsImport.history_subtitle', {
            catalogue,
            effectiveDate,
          })
        }}
      </div>
    </v-card-title>
    <v-divider />
    <v-card-text>
      <v-alert
        v-if="error"
        type="error"
        variant="tonal"
        class="alert-bordered"
        :text="error"
      />
      <v-progress-linear v-if="loading" indeterminate />
      <v-table
        v-else-if="history"
        class="history-table overflow-x-hidden"
        density="compact"
      >
        <thead>
          <tr>
            <th class="attribute-column" />
            <th
              v-for="release in history.releases"
              :key="release.package_name"
              :class="columnClass(release)"
            >
              <div class="font-weight-bold">{{ release.effective_date }}</div>
              <div class="text-caption text-medium-emphasis">
                <template v-if="release.is_current">
                  {{ $t('StandardsImport.history_this_package') }}
                </template>
                <template v-else-if="release.is_earliest_staged">
                  {{ $t('StandardsImport.history_first_release') }}
                </template>
              </div>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in attributeRows" :key="row.field">
            <th class="attribute-column">
              {{ fieldLabel(row.field) }}
            </th>
            <td
              v-for="(cell, index) in row.cells"
              :key="index"
              :class="{
                'changed-cell': cell.changed,
                [currentStatusClass]: history.releases[index].is_current,
              }"
              :data-cy="`standards-import-history-${row.field}-${index}`"
            >
              <span
                v-if="!cell.present"
                class="text-caption text-medium-emphasis font-italic"
              >
                {{ $t('StandardsImport.history_not_in_release') }}
              </span>
              <AttributeDiff
                v-else
                :old-value="cell.previous"
                :new-value="cell.value"
              />
            </td>
          </tr>
          <tr v-if="history.membership_changes" class="membership-row">
            <th class="attribute-column">
              {{ $t('StandardsImport.history_codelists') }}
            </th>
            <td
              v-for="(change, index) in history.membership_changes"
              :key="index"
              :class="{
                'changed-cell': change.entered.length || change.left.length,
                [currentStatusClass]: history.releases[index].is_current,
              }"
              data-cy="standards-import-history-membership"
            >
              <div
                v-for="codelist in change.left"
                :key="`l${codelist.concept_id}`"
              >
                <span class="text-error font-weight-bold mr-1">&minus;</span>
                {{ codelistLabel(codelist) }}
              </div>
              <div
                v-for="codelist in change.entered"
                :key="`e${codelist.concept_id}`"
              >
                <span class="text-success font-weight-bold mr-1">+</span>
                {{ codelistLabel(codelist) }}
              </div>
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card-text>
    <v-divider />
    <v-card-actions class="bg-white border-t-thin py-4 px-6">
      <div class="text-caption text-medium-emphasis">
        {{ $t('StandardsImport.history_footnote') }}
      </div>
      <v-spacer />
      <v-btn
        color="primary"
        variant="flat"
        rounded="xl"
        min-width="120px"
        data-cy="standards-import-history-close"
        @click="emit('close')"
      >
        {{ $t('_global.close') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import AttributeDiff from './AttributeDiff.vue'
import packageDiffApi from '@/api/standardsImport/packageDiff'

const { t, te } = useI18n()

const props = defineProps({
  catalogue: {
    type: String,
    default: '',
  },
  effectiveDate: {
    type: String,
    default: '',
  },
  conceptType: {
    type: String,
    default: 'term',
    validator: (value) => ['term', 'codelist'].includes(value),
  },
  conceptId: {
    type: String,
    default: '',
  },
})
const emit = defineEmits(['close'])

const history = ref(null)
const loading = ref(false)
const error = ref('')

// Per attribute, one cell per release. A cell is "changed" when the release holds the
// concept and the last release that did held something else; the diff is drawn against
// that one, so a gap in the middle does not hide an edit.
const attributeRows = computed(() =>
  (history.value?.attributes || []).map((attribute) => {
    let lastPresent
    let seen = false
    const cells = attribute.values.map((value, index) => {
      const present = history.value.releases[index].present
      if (!present) {
        return { present: false }
      }
      const previous = seen ? lastPresent : value
      const changed = seen && JSON.stringify(previous) !== JSON.stringify(value)
      lastPresent = value
      seen = true
      return { present: true, value, previous, changed }
    })
    return { field: attribute.field, cells }
  })
)

// What this release does to the concept, against the one before it: it is removed when
// the release before held it and this one does not, added when it is the other way
// round, and otherwise unchanged as far as being there goes (edited or not).
const currentStatusClass = computed(() => {
  const releases = history.value?.releases || []
  const current = releases[releases.length - 1]
  const previous = releases[releases.length - 2]
  if (!current || !previous) {
    return 'current-release-unchanged'
  }
  if (previous.present && !current.present) {
    return 'current-release-removed'
  }
  if (!previous.present && current.present) {
    return 'current-release-added'
  }
  return 'current-release-unchanged'
})

function columnClass(release) {
  return release.is_current ? currentStatusClass.value : ''
}

function fieldLabel(field) {
  const key = `StandardsImport.diff_field_${field}`
  return te(key) ? t(key) : field
}

function codelistLabel(codelist) {
  return codelist.submission_value
    ? `${codelist.concept_id} (${codelist.submission_value})`
    : codelist.concept_id
}

function load() {
  if (!props.catalogue || !props.effectiveDate || !props.conceptId) {
    return
  }
  loading.value = true
  error.value = ''
  history.value = null
  packageDiffApi
    .getConceptHistory(
      props.catalogue,
      props.conceptType,
      props.conceptId,
      props.effectiveDate
    )
    .then((response) => {
      history.value = response.data
    })
    .catch((err) => {
      error.value =
        err.response?.data?.message ||
        err.message ||
        t('StandardsImport.history_error')
    })
    .finally(() => {
      loading.value = false
    })
}

watch(() => [props.catalogue, props.effectiveDate, props.conceptId], load)
onMounted(load)
</script>

<style scoped lang="scss">
// Fixed layout so the columns share the dialog's width instead of each demanding a
// minimum of its own: the number of releases and the length of what they hold then
// cannot push the table past the dialog. Long values wrap instead.
.history-table {
  :deep(table) {
    table-layout: fixed;
    width: 100%;
  }

  th,
  td {
    vertical-align: top;
    padding-top: 8px;
    padding-bottom: 8px;
    overflow-wrap: anywhere;
  }

  .attribute-column {
    width: 160px;
  }

  .changed-cell {
    background-color: rgba(var(--v-theme-warning), 0.12);
  }

  .current-release-added {
    border-left: 2px solid rgb(var(--v-theme-success));
  }

  .current-release-removed {
    border-left: 2px solid rgb(var(--v-theme-error));
  }

  .current-release-unchanged {
    border-left: 2px solid rgb(var(--v-theme-info));
  }
}
</style>
