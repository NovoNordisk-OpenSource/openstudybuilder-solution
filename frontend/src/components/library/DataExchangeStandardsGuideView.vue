<template>
  <v-row>
    <v-col cols="1">
      <v-timeline density="compact" class="ml-2 timeline-height">
        <v-timeline-item
          v-for="model of models"
          :key="model.start_date"
          :dot-color="activeGuide === model ? 'primary' : 'grey'"
          size="small"
          right
        >
          <v-btn
            variant="text"
            :color="activeGuide === model ? 'primary' : 'default'"
            @click="chooseGuideVersion(model)"
          >
            {{ model.version_number }}
          </v-btn>
        </v-timeline-item>
      </v-timeline>
    </v-col>
    <v-col cols="11">
      <v-card class="mt-2 mb-2" elevation="1" max-width="99%">
        <v-card-text>
          <v-row>
            <v-col cols="1">
              <div class="font-weight-bold">
                {{ $t('DataModels.status') }}
              </div>
              <p class="font-weight-regular">
                {{ activeGuide.status }}
              </p>
            </v-col>
            <v-col cols="3">
              <div class="font-weight-bold">
                {{ $t('DataModels.effective_date') }}
              </div>
              <p class="font-weight-regular">
                {{
                  activeGuide.start_date
                    ? activeGuide.start_date.substring(0, 10)
                    : ''
                }}
              </p>
            </v-col>
            <v-col cols="3">
              <div class="font-weight-bold">
                {{ $t('DataModels.implements') }}
              </div>
              <a
                href="#"
                class="font-weight-regular"
                @click="redirectToModel(activeGuide.implemented_data_model)"
                >{{
                  activeGuide.implemented_data_model
                    ? activeGuide.implemented_data_model.name
                    : ''
                }}</a
              >
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>
      <div class="title font-weight-bold mt-6">
        {{ $t('DataModels.classes') }}
      </div>
      <v-tabs v-model="activeTab" show-arrows>
        <v-tab v-for="tab of datasets" :key="tab[0].uid" :href="tab[0].tab">
          {{
            tab[0].implemented_dataset_class.dataset_class_name
              ? tab[0].implemented_dataset_class.dataset_class_name.replaceAll(
                  '_',
                  ' '
                )
              : '0'
          }}
        </v-tab>
      </v-tabs>
      <v-window v-model="activeTab">
        <v-window-item v-for="tab of datasets" :key="tab[0].uid">
          <div v-if="tab.length === 1">
            <v-card class="mt-2 mb-2 ml-1" elevation="1" max-width="1440px">
              <v-card-text>
                <v-row>
                  <v-col cols="2">
                    <div class="font-weight-bold">
                      {{ $t('_global.name') }}
                    </div>
                    <p class="font-weight-regular">
                      {{ tab[0].label }}
                    </p>
                  </v-col>
                  <v-col cols="10">
                    <div class="font-weight-bold">
                      {{ $t('_global.description') }}
                    </div>
                    <p class="font-weight-regular">
                      {{ tab[0].description }}
                    </p>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
            <v-data-table
              :loading="loading"
              density="compact"
              :headers="headers"
              :items="variables"
            >
              <template #[`item.referenced_codelists.uid`]="{ item }">
                <a
                  v-for="codelist in item.referenced_codelists"
                  :key="codelist.uid"
                  href="#"
                  class="mr-2"
                  @click="showCodelistTerms(codelist.uid)"
                  >{{ codelist.uid }}</a
                >
              </template>
              <template #[`item.implements_variable.uid`]="{ item }">
                <a
                  href="#"
                  @click="openImplementedModel(item.implements_variable.uid)"
                  >{{
                    item.implements_variable ? item.implements_variable.uid : ''
                  }}</a
                >
              </template>
              <template #[`item.value_list`]="{ item }">
                {{ item.value_list.join(',') }}
              </template>
            </v-data-table>
          </div>
          <div v-else>
            <v-tabs v-model="domainTab" show-arrows>
              <v-tab v-for="dTab of tab" :key="dTab.uid" :href="dTab.tab">
                {{ dTab.uid }}
              </v-tab>
            </v-tabs>
            <v-window v-model="domainTab">
              <v-window-item v-for="dTab of tab" :key="dTab.uid">
                <v-card class="mt-2 mb-2 ml-1" elevation="1" max-width="1440px">
                  <v-card-text>
                    <v-row>
                      <v-col cols="2">
                        <div class="font-weight-bold">
                          {{ $t('_global.name') }}
                        </div>
                        <p class="font-weight-regular">
                          {{ dTab.label }}
                        </p>
                      </v-col>
                      <v-col cols="1">
                        <div class="font-weight-bold">
                          {{ $t('DataModels.ordinal') }}
                        </div>
                        <p class="font-weight-regular">
                          {{ dTab.data_model_ig.ordinal }}
                        </p>
                      </v-col>
                      <v-col cols="9">
                        <div class="font-weight-bold">
                          {{ $t('_global.description') }}
                        </div>
                        <p class="font-weight-regular">
                          {{ dTab.description }}
                        </p>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
                <v-data-table
                  :loading="loading"
                  density="compact"
                  :headers="headers"
                  :items="variables"
                >
                  <template #[`item.referenced_codelists.uid`]="{ item }">
                    <a
                      v-for="codelist in item.referenced_codelists"
                      :key="codelist"
                      href="#"
                      class="mr-2"
                      @click="showCodelistTerms(codelist.uid)"
                      >{{ codelist.uid }}</a
                    >
                  </template>
                  <template #[`item.implements_variable.uid`]="{ item }">
                    <a
                      href="#"
                      @click="
                        openImplementedModel(item.implements_variable.uid)
                      "
                      >{{
                        item.implements_variable
                          ? item.implements_variable.uid
                          : ''
                      }}</a
                    >
                  </template>
                  <template #[`item.value_list`]="{ item }">
                    {{ item.value_list.join(',') }}
                  </template>
                </v-data-table>
              </v-window-item>
            </v-window>
          </div>
        </v-window-item>
      </v-window>
    </v-col>
  </v-row>
  <v-dialog v-model="showCodelist" persistent>
    <StandardsCodelistTermsDialog
      :codelist-uid="codelistUid"
      @close="closeCodelistTerms"
    />
  </v-dialog>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import standards from '@/api/standards'
import _isEmpty from 'lodash/isEmpty'
import StandardsCodelistTermsDialog from '@/components/library/StandardsCodelistTermsDialog.vue'

const props = defineProps({
  uid: {
    type: String,
    default: null,
  },
  headers: {
    type: Array,
    default: null,
  },
  redirectGuide: {
    type: Object,
    default: null,
  },
})
const emit = defineEmits(['redirectToModelWithVariable', 'redirectToModel'])

const models = ref([])
const activeGuide = ref({})
const datasets = ref([])
const activeTab = ref(null)
const variables = ref([])
const loading = ref(false)
const domainTab = ref(null)
const showCodelist = ref(false)
const codelistUid = ref('')

watch(activeTab, (value) => {
  domainTab.value = 0
  if (datasets.value[value]) {
    getVariables(datasets.value[value][0].uid)
  }
})
watch(
  () => props.redirectGuide,
  (value) => {
    chooseGuideVersion(models.value.find((model) => model.name === value.name))
  }
)
watch(domainTab, (value) => {
  getVariables(datasets.value[activeTab.value][value].uid)
})

onMounted(() => {
  const params = {
    filters: { uid: { v: [props.uid], op: 'eq' } },
    page_size: 0,
  }
  standards.getAllGuides(params).then((resp) => {
    models.value = resp.data.items
    chooseGuideVersion(
      !_isEmpty(props.redirectGuide)
        ? models.value.find((model) => model.name === props.redirectGuide.name)
        : models.value[0]
    )
  })
})

function openImplementedModel(variable) {
  const params = {
    data_model_name: activeGuide.value.implemented_data_model.uid,
    data_model_version:
      activeGuide.value.implemented_data_model.name.substring(6),
    dataset_class_name:
      datasets.value[activeTab.value][0].implemented_dataset_class
        .dataset_class_name,
    filters: { uid: { v: [variable], op: 'eq' } },
  }
  standards.getClassVariables(params).then((resp) => {
    emit('redirectToModelWithVariable', {
      data: resp.data.items,
      implementation: activeGuide.value.implemented_data_model,
    })
  })
}
function showCodelistTerms(uid) {
  codelistUid.value = uid
  showCodelist.value = true
}
function closeCodelistTerms() {
  codelistUid.value = ''
  showCodelist.value = false
}
function redirectToModel(item) {
  emit('redirectToModel', item)
}
function chooseGuideVersion(guide) {
  if (guide) {
    datasets.value = []
    activeGuide.value = guide
    const params = {
      data_model_ig_name: activeGuide.value.uid,
      data_model_ig_version: activeGuide.value.version_number,
      page_size: 0,
    }
    standards.getDatasets(params).then((resp) => {
      datasets.value = resp.data.items
      const sortedDatasets = Object.values(
        datasets.value.reduce((acc, curr) => {
          acc[curr.implemented_dataset_class.dataset_class_name] =
            acc[curr.implemented_dataset_class.dataset_class_name] || []
          acc[curr.implemented_dataset_class.dataset_class_name].push(curr)
          return acc
        }, {})
      ).sort((a, b) =>
        a[0].implemented_dataset_class.dataset_class_name.localeCompare(
          b[0].implemented_dataset_class.dataset_class_name
        )
      )
      datasets.value = sortedDatasets
      activeTab.value = 0
      getVariables(datasets.value[0][0].uid)
    })
  }
}
function getVariables(domain) {
  loading.value = true
  variables.value = []
  const params = {
    filters: { 'dataset.uid': { v: [domain], op: 'eq' } },
    data_model_ig_name: activeGuide.value.uid,
    data_model_ig_version: activeGuide.value.version_number,
    page_size: 0,
  }
  standards.getDatasetVariables(params).then((resp) => {
    variables.value = resp.data.items
    loading.value = false
  })
}
</script>
<style>
.timeline-height {
  height: auto;
}
</style>
