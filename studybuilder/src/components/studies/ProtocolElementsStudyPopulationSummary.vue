<template>
  <div>
    <div class="mt-6 d-flex align-center">
      <v-card-title class="text-h6 ml-2">
        {{ $t('StudyPopulationView.title') }}
      </v-card-title>
    </div>
    <div>
      <v-radio-group v-model="expand" row color="primary" class="pt-2 ml-5">
        <v-radio :label="$t('StudyPopulationView.show_all')" :value="true" />
        <v-radio :label="$t('StudyPopulationView.hide_all')" :value="false" />
      </v-radio-group>
    </div>
    <v-expansion-panels v-model="panel" multiple accordion>
      <v-expansion-panel
        v-for="(criterias, name) in studyCriterias"
        :key="name"
      >
        <v-expansion-panel-title
          v-if="criterias.length > 0"
          class="text-h6 text-grey"
        >
          <span v-html="name" />
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <ol>
            <li v-for="(item, index) in criterias" :key="index" v-html="item" />
          </ol>
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </div>
</template>

<script>
import study from '@/api/study'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { computed } from 'vue'

export default {
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
    }
  },
  data() {
    return {
      studyCriteriasTypes: {
        'Inclusion Criteria': [], // Hardcoded to keep correct order
        'Exclusion Criteria': [],
        'Run-in Criteria': [],
        'Randomisation Criteria': [],
        'Dosing Criteria': [],
        'Withdrawal Criteria': [],
      },
      studyCriterias: {},
      test: {},
      panel: [],
      expand: false,
    }
  },
  watch: {
    expand(value) {
      value ? this.openAll() : this.closeAll()
    },
  },
  mounted() {
    study.getStudyCriteria(this.selectedStudy.uid).then((resp) => {
      resp.data.items.forEach((el) => {
        if (
          el.criteria_type.sponsor_preferred_name in this.studyCriteriasTypes
        ) {
          if (!this.studyCriterias[el.criteria_type.sponsor_preferred_name]) {
            this.studyCriterias[el.criteria_type.sponsor_preferred_name] = []
          }
          this.studyCriterias[el.criteria_type.sponsor_preferred_name].push(
            el.criteria
              ? this.removeBrackets(el.criteria.name)
              : this.removeBrackets(el.criteria_template.name)
          )
        }
      })
    })
  },
  methods: {
    openAll() {
      let length = Object.keys(this.studyCriterias).length
      while (length >= 0) {
        this.panel.push(length)
        length--
      }
    },
    closeAll() {
      this.panel = []
    },
    removeBrackets(value) {
      return value.replaceAll('[', '').replaceAll(']', '')
    },
  },
}
</script>
