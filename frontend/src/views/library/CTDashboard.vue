<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('CTDashboardView.title') }}
      <HelpButton :help-text="$t('_help.CTDashboard.general')" />
    </div>
    <div v-if="stats.catalogues === undefined" class="text-center mt-10">
      <v-progress-circular indeterminate color="primary" size="128" />
    </div>
    <template v-else>
      <v-row>
        <v-col sm="12" lg="4">
          <v-card flat>
            <v-card-text>
              <div>
                {{ $t('CTDashboardView.catalogue_count') }}
                <span class="font-weight-bold">{{ stats.catalogues }}</span
                ><br />
                {{ $t('CTDashboardView.package_count') }}
                <span class="font-weight-bold">{{ stats.packages }}</span>
              </div>
              <div class="mt-4">
                {{ $t('CTDashboardView.cdisc_codelist_count') }}
                <span class="font-weight-bold">{{
                  getCodelistCount('CDISC')
                }}</span
                ><br />
                {{ $t('CTDashboardView.sponsor_codelist_count') }}
                <span class="font-weight-bold">{{
                  getCodelistCount('Sponsor')
                }}</span>
              </div>
              <div class="mt-4">
                {{ $t('CTDashboardView.cdisc_term_count') }}
                <span class="font-weight-bold">{{ getTermCount('CDISC') }}</span
                ><br />
                {{ $t('CTDashboardView.sponsor_term_count') }}
                <span class="font-weight-bold">{{
                  getTermCount('Sponsor')
                }}</span>
              </div>
              <div class="mt-4">
                {{ $t('CTDashboardView.codelist_mean_count') }}
                <span class="font-weight-bold"
                  >{{ stats.codelist_change_percentage }}%</span
                ><br />
                {{ $t('CTDashboardView.term_mean_count') }}
                <span class="font-weight-bold"
                  >{{ stats.term_change_percentage }}%</span
                >
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col sm="12" lg="4">
          <v-card flat>
            <v-card-title>{{
              $t('CTDashboardView.codelist_chart_title')
            }}</v-card-title>
            <v-card-text>
              <BarChart
                :chart-data="codelistEvolutionData"
                :options="chartOptions"
                :style="chartStyles"
              />
            </v-card-text>
          </v-card>
        </v-col>
        <v-col sm="12" lg="4">
          <v-card class="fixed-height" flat>
            <v-card-title>{{
              $t('CTDashboardView.term_chart_title')
            }}</v-card-title>
            <v-card-text>
              <BarChart
                :chart-data="termEvolutionData"
                :options="chartOptions"
                :style="chartStyles"
              />
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <v-card flat>
            <v-card-title>{{ $t('CTDashboardView.table_title') }}</v-card-title>
            <v-card-text>
              <v-data-table
                :headers="headers"
                :items="stats.latest_added_codelists"
              >
                <template #[`item.name.template_parameter`]="{ item }">
                  {{ $filters.yesno(item.name.template_parameter) }}
                </template>
                <template #[`item.name.status`]="{ item }">
                  <StatusChip :status="item.name.status" />
                </template>
                <template #[`item.name.start_date`]="{ item }">
                  {{ $filters.date(item.name.start_date) }}
                </template>
                <template #[`item.attributes.extensible`]="{ item }">
                  {{ $filters.yesno(item.attributes.extensible) }}
                </template>
                <template #[`item.attributes.status`]="{ item }">
                  <StatusChip :status="item.attributes.status" />
                </template>
                <template #[`item.attributes.start_date`]="{ item }">
                  {{ $filters.date(item.attributes.start_date) }}
                </template>
                <template #bottom />
              </v-data-table>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import controlledTerminology from '@/api/controlledTerminology'
import BarChart from '@/components/tools/BarChart.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import HelpButton from '@/components/tools/HelpButton.vue'

const { t } = useI18n()

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  scales: {
    y: {
      ticks: {
        beginAtZero: true,
      },
    },
  },
}
const headers = [
  { title: t('_global.library'), value: 'library_name' },
  { title: t('CTDashboardView.concept_id'), value: 'codelist_uid' },
  {
    title: t('CTDashboardView.sponsor_pref_name'),
    value: 'name.name',
  },
  {
    title: t('CTDashboardView.template_parameter'),
    value: 'name.template_parameter',
  },
  { title: t('CTDashboardView.name_status'), value: 'name.status' },
  { title: t('_global.modified'), value: 'name.start_date' },
  {
    title: t('CTDashboardView.codelist_name'),
    value: 'attributes.name',
  },
  {
    title: t('CTDashboardView.subm_value'),
    value: 'attributes.submission_value',
  },
  {
    title: t('CTDashboardView.extensible'),
    value: 'attributes.extensible',
  },
  {
    title: t('CTDashboardView.codelist_status'),
    value: 'attributes.status',
  },
  { title: t('_global.modified'), value: 'attributes.start_date' },
]

const stats = ref({})

const codelistEvolutionData = computed(() => {
  return computeEvolutionData('codelist')
})
const termEvolutionData = computed(() => {
  return computeEvolutionData('term')
})
const chartStyles = computed(() => {
  return {
    height: '500px',
    position: 'relative',
  }
})

onMounted(() => {
  controlledTerminology.getStats().then((resp) => {
    stats.value = resp.data
  })
})

function getCodelistCount(name) {
  if (stats.value.codelist_counts) {
    const result = stats.value.codelist_counts.find(
      (item) => item.library_name === name
    )
    if (result) {
      return result.count
    }
  }
  return '?'
}
function getTermCount(name) {
  if (stats.value.term_counts) {
    const result = stats.value.term_counts.find(
      (item) => item.library_name === name
    )
    if (result) {
      return result.count
    }
  }
  return '?'
}
function computeEvolutionData(property) {
  const years = []
  const datasets = {
    added: {
      label: t('CTDashboardView.added'),
      data: [],
      backgroundColor: '#193074',
    },
    updated: {
      label: t('CTDashboardView.updated'),
      data: [],
      backgroundColor: '#3f9c35',
    },
    deleted: {
      label: t('CTDashboardView.deleted'),
      data: [],
      backgroundColor: '#e6553f',
    },
  }

  stats.value[`${property}_change_details`].sort((a, b) => {
    return b.year - a.year
  })
  stats.value[`${property}_change_details`].forEach((item) => {
    years.unshift(item.year)
    item.counts.forEach((count) => {
      datasets[count.type].data.unshift(count.count)
    })
  })
  return {
    labels: years,
    datasets: [datasets.added, datasets.updated, datasets.deleted],
  }
}
</script>
