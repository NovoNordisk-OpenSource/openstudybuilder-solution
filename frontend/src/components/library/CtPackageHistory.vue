<template>
  <v-card elevation="0" outlined>
    <v-card>
      <v-row no-gutters>
        <v-col cols="10">
          <div>
            <v-sheet class="mx-auto">
              <v-slide-group multiple show-arrows class="slideHeight mt-2">
                <v-slide-group-item v-for="(date, index) in dates" :key="index">
                  <div class="d-block mx-2">
                    <div class="text-body-small mt-3">
                      {{ shortDate(date) }}
                    </div>
                    <div class="text-center">
                      <v-btn
                        icon
                        :color="getDateColor(date)"
                        size="x-small"
                        @click="selectDate(date)"
                      />
                    </div>
                  </div>
                </v-slide-group-item>
              </v-slide-group>
            </v-sheet>
          </div>
        </v-col>
        <v-col cols="2" class="d-flex align-start">
          <label class="v-label mr-4 mt-3">{{
            $t('CtPackageHistory.show')
          }}</label>
          <v-radio-group v-model="display">
            <v-radio
              :label="$t('CtPackageHistory.submission_value_choice')"
              value="submission_value"
            />
            <v-radio
              :label="$t('CtPackageHistory.codelist_code_choice')"
              value="uid"
            />
            <v-radio
              :label="$t('CtPackageHistory.sponsor_name_choice')"
              value="name"
            />
          </v-radio-group>
        </v-col>
      </v-row>
    </v-card>
    <div
      v-if="fromDate && toDate"
      class="d-flex align-center bg-greyBackground py-4 px-16"
    >
      <v-btn icon color="secondary" size="x-small" class="mr-2" />
      <span>From {{ shortDate(fromDate) }}</span>
      <v-divider class="mx-10" />
      <v-btn icon color="secondary" size="x-small" class="mr-2" />
      <span>To {{ shortDate(toDate) }}</span>
    </div>
    <div v-if="fromDate && toDate" class="pa-4">
      <v-progress-linear v-if="loading" indeterminate class="mx-4" />
      <template v-else>
        <HistoryCodelistSet
          :title="
            $t('CtPackageHistory.new_codelist', changes.new_codelists.length)
          "
          color="primary"
          :codelists="changes.new_codelists"
          :chips-label="display"
          :from-date="fromDate"
          :to-date="toDate"
        />
        <v-divider class="my-4" color="greyBackground" />
        <HistoryCodelistSet
          :title="
            $t(
              'CtPackageHistory.updated_codelist',
              changes.updated_codelists.length
            )
          "
          color="green"
          :codelists="changes.updated_codelists"
          :chips-label="display"
          :from-date="fromDate"
          :to-date="toDate"
        />
        <v-divider class="my-4" color="greyBackground" />
        <HistoryCodelistSet
          :title="
            $t(
              'CtPackageHistory.deleted_codelist',
              changes.deleted_codelists.length
            )
          "
          color="red"
          :codelists="changes.deleted_codelists"
          :chips-label="display"
          :from-date="fromDate"
          :to-date="toDate"
        />
      </template>
    </div>
  </v-card>
</template>

<script>
import { DateTime } from 'luxon'
import controlledTerminology from '@/api/controlledTerminology'
import HistoryCodelistSet from './HistoryCodelistSet.vue'

export default {
  components: {
    HistoryCodelistSet,
  },
  props: {
    catalogue: {
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      changes: {},
      dates: [],
      display: 'submission_value',
      fromDate: null,
      loading: false,
      toDate: null,
    }
  },
  mounted() {
    this.resetChanges()
    controlledTerminology.getPackagesDates(this.catalogue.name).then((resp) => {
      this.dates = resp.data.effective_dates.reverse()
    })
  },
  methods: {
    resetChanges() {
      this.changes = {
        new_codelists: {},
        deleted_codelists: {},
        updated_codelists: {},
      }
    },
    getDateColor(date) {
      return this.fromDate === date || this.toDate === date ? 'secondary' : ''
    },
    async selectDate(date) {
      if (!this.fromDate) {
        this.fromDate = date
      } else if (!this.toDate) {
        const fromDate = DateTime.fromISO(this.fromDate).toJSDate()
        const toDate = DateTime.fromISO(date).toJSDate()
        if (fromDate < toDate) {
          this.toDate = date
        } else {
          this.toDate = this.fromDate
          this.fromDate = date
        }
        this.loading = true
        try {
          const resp = await controlledTerminology.getPackagesChanges(
            this.catalogue.name,
            this.fromDate,
            this.toDate
          )
          this.changes = resp.data
        } finally {
          this.loading = false
        }
      } else {
        this.resetChanges()
        this.fromDate = date
        this.toDate = null
      }
    },
    shortDate(value) {
      return value.split('T')[0]
    },
  },
}
</script>
<style>
.slideHeight {
  height: 100px;
}
</style>
