<template>
  <div>
    <v-row>
      <v-col cols="1">
        <v-timeline density="compact" class="timeline-height">
          <v-timeline-item
            v-for="model of models"
            :key="model.start_date"
            :dot-color="activeModel === model ? 'primary' : 'grey'"
            size="small"
            right
          >
            <v-btn
              variant="text"
              :color="activeModel === model ? 'primary' : 'default'"
              @click="chooseModelVersion(model)"
            >
              v{{ model.version_number }}
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
                  {{ activeModel.status }}
                </p>
              </v-col>
              <v-col cols="3">
                <div class="font-weight-bold">
                  {{ $t('DataModels.effective_date') }}
                </div>
                <p class="font-weight-regular">
                  {{
                    activeModel.start_date
                      ? activeModel.start_date.substring(0, 10)
                      : ''
                  }}
                </p>
              </v-col>
              <v-col cols="3">
                <div class="font-weight-bold">
                  {{ $t('DataModels.implemented_by') }}
                </div>
                <div
                  v-for="guide of activeModel.implementation_guides"
                  :key="guide.name"
                >
                  <a
                    href="#"
                    class="font-weight-regular"
                    @click="redirectToGuide(guide)"
                    >{{ guide.name }}</a
                  >
                </div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
        <div class="title font-weight-bold mt-6">
          {{ $t('DataModels.classes') }}
        </div>
        <v-row class="mt-2">
          <v-tabs v-model="activeTab" light>
            <v-tab v-for="tab of datasetClasses" :key="tab.uid" :href="tab.tab">
              {{ tab.uid.replaceAll('_', ' ') }}
            </v-tab>
          </v-tabs>
          <v-window v-model="activeTab">
            <v-window-item v-for="tab of datasetClasses" :key="tab.uid">
              <div>
                <v-card class="mt-2 mb-2 ml-1" elevation="1" max-width="1440px">
                  <v-card-text>
                    <v-row>
                      <v-col cols="2">
                        <div class="font-weight-bold">
                          {{ $t('_global.name') }}
                        </div>
                        <p class="font-weight-regular">
                          {{ tab.label }}
                        </p>
                      </v-col>
                      <v-col cols="10">
                        <div class="font-weight-bold">
                          {{ $t('_global.description') }}
                        </div>
                        <p class="font-weight-regular">
                          {{ tab.description }}
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
                      @click="openCodelistTerms(codelist.uid)"
                      >{{ codelist.uid }}</a
                    >
                  </template>
                </v-data-table>
              </div>
            </v-window-item>
          </v-window>
        </v-row>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import standards from '@/api/standards'

const props = defineProps({
  uid: {
    type: String,
    default: null,
  },
  redirectModel: {
    type: Object,
    default: null,
  },
  redirectClass: {
    type: Object,
    default: null,
  },
  headers: {
    type: Array,
    default: null,
  },
})
const emit = defineEmits(['redirectToGuide'])

const models = ref([])
const activeModel = ref({})
const datasetClasses = ref([])
const activeTab = ref(0)
const variables = ref([])
const loading = ref(false)
const variableFilter = ref(false)

watch(activeTab, (value) => {
  if (!variableFilter.value) {
    getVariables(datasetClasses.value[value].label)
  }
  variableFilter.value = false
})
watch(
  () => props.redirectModel,
  (value) => {
    if (value && value.implementation) {
      variableFilter.value = true
      activeModel.value = models.value.find(
        (model) => model.name === value.implementation.name
      )
      activeTab.value = datasetClasses.value.findIndex(
        (el) => el.label === value.data[0].dataset_class.dataset_class_name
      )
      variables.value = value.data
    } else if (value) {
      chooseModelVersion(
        models.value.find((model) => model.name === value.name)
      )
    }
  }
)

onMounted(() => {
  const params = {
    filters: { uid: { v: [props.uid], op: 'eq' } },
  }
  standards.getAllModels(params).then((resp) => {
    models.value = resp.data.items
    if (models.value.length) {
      chooseModelVersion(models.value[0])
    }
  })
})

function openCodelistTerms(codelistUid) {
  this.$router.push({
    name: 'CodelistTerms',
    params: { codelist_id: codelistUid, catalogue_name: 'All' },
  })
}
function redirectToGuide(item) {
  emit('redirectToGuide', item)
}
function chooseModelVersion(model) {
  activeModel.value = model
  const params = {
    data_model_name: activeModel.value.name,
    page_size: 0,
  }
  standards.getDatasetClasses(params).then((resp) => {
    datasetClasses.value = resp.data.items
    activeTab.value = 0
    getVariables(datasetClasses.value[0].label)
  })
}
function getVariables(className) {
  loading.value = true
  variables.value = []
  const params = {
    dataset_class_name: className,
    data_model_name: activeModel.value.uid,
    data_model_version: activeModel.value.version_number,
    page_size: 0,
  }
  standards.getClassVariables(params).then((resp) => {
    variables.value = resp.data.items
    loading.value = false
  })
}
</script>
<style>
.timeline-height {
  height: auto !important;
}
</style>
