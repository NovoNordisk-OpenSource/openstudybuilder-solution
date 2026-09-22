<template>
  <v-card color="dfltBackground">
    <v-card-title>
      <div class="page-title">
        {{ codelistAttributes.name }} ({{ codelistAttributes.codelist_uid }}) -
        {{ codelistAttributes.submission_value }} /
        {{ $t('CodeListDetail.terms_listing') }}
      </div>
    </v-card-title>
    <v-card-text>
      <v-expansion-panels v-model="panel" flat tile accordion>
        <v-expansion-panel>
          <v-expansion-panel-title class="text-headline-small grey--text">
            {{ $t('CodelistSummary.title') }}
          </v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-row class="mt-2">
              <v-col cols="2" class="font-weight-bold pb-0">
                {{ codelistAttributes.codelist_uid }}
              </v-col>
              <v-col cols="1" class="pb-0">
                <v-btn color="secondary" @click="openCodelistTerms">
                  {{ $t('CodeListDetail.open_ct') }}
                </v-btn>
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="2" class="font-weight-bold pb-0">
                {{ $t('CodeListDetail.extensible') }}:
              </v-col>
              <v-col cols="1" class="pb-0">
                {{ $filters.yesno(codelistAttributes.extensible) }}
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="2" class="font-weight-bold pb-0">
                {{ $t('CodeListDetail.submission_value') }}:
              </v-col>
              <v-col cols="1" class="pb-0">
                {{ codelistAttributes.submission_value }}
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="2" class="font-weight-bold pb-0">
                {{ $t('CodeListDetail.definition') }}:
              </v-col>
              <v-col cols="8" class="pb-0">
                {{ codelistAttributes.definition }}
              </v-col>
            </v-row>
            <v-row>
              <v-col cols="2" class="font-weight-bold">
                {{ $t('CodeListDetail.nci_pref_name') }}:
              </v-col>
              <v-col cols="8">
                {{ codelistAttributes.nci_preferred_name }}
              </v-col>
            </v-row>
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>
      <NNTable
        table-id="standards-codelist-terms-dialog"
        :headers="headers"
        :items="terms"
        :items-length="total"
        item-value="term_uid"
        height="40vh"
        class="mt-4"
        column-data-resource="ct/terms"
        :codelist-uid="codelistUid"
        @filter="fetchTerms"
      >
        <template #[`item.attributes.status`]="{ item }">
          <StatusChip :status="item.attributes.status" />
        </template>
      </NNTable>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn color="secondary" @click="close">
        {{ $t('_global.close') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import controlledTerminology from '@/api/controlledTerminology'
import codelistsApi from '@/api/controlledTerminology/codelists'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import filteringParameters from '@/utils/filteringParameters'

const props = defineProps({
  codelistUid: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['close'])

const router = useRouter()
const { t } = useI18n()

const codelistAttributes = ref({})
const headers = [
  { title: t('CtCatalogueTable.concept_id'), key: 'concept_id' },
  {
    title: t('CodelistTermsView.sponsor_name'),
    key: 'sponsor_preferred_name',
  },
  {
    title: t('CodelistTermsView.submission_value'),
    key: 'submission_value',
  },
  {
    title: t('CodelistTermsView.attr_status'),
    key: 'attributes_status',
  },
]
const terms = ref([])
const total = ref(0)
const panel = ref(0)

watch(
  () => props.codelistUid,
  (value) => {
    if (value) {
      controlledTerminology.getCodelistAttributes(value).then((resp) => {
        codelistAttributes.value = resp.data
      })
      fetchTerms()
    }
  }
)

onMounted(() => {
  controlledTerminology
    .getCodelistAttributes(props.codelistUid)
    .then((resp) => {
      codelistAttributes.value = resp.data
    })
})

function close() {
  emit('close')
}
function openCodelistTerms() {
  router.push({
    name: 'CodelistTerms',
    params: { codelist_id: props.codelistUid, catalogue_name: 'All' },
  })
}
function fetchTerms(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  codelistsApi.getCodelistTerms(props.codelistUid, params).then((resp) => {
    terms.value = resp.data.items
    total.value = resp.data.total
  })
}
</script>
