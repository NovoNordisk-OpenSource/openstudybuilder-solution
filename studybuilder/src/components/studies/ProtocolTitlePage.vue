<template>
  <div class="mt-6 d-flex align-center">
    <v-card-title class="text-h6">
      {{ $t('StudyProtocolElementsView.title_page') }}
    </v-card-title>
  </div>
  <v-data-table
    class="mt-2"
    :headers="headers"
    :items="items"
    hide-default-footer
  />
</template>

<script>
import { computed } from 'vue'
import study from '@/api/study'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
    }
  },
  data() {
    return {
      headers: [
        {
          title: this.$t('ProtocolTitlePage.title_page_elements'),
          key: 'label',
          width: '30%',
        },
        { title: this.$t('ProtocolTitlePage.values'), key: 'value' },
      ],
      items: [],
    }
  },
  mounted() {
    study.getStudyProtocolTitle(this.selectedStudy.uid).then((resp) => {
      this.items = [
        {
          label: this.$t('ProtocolTitlePage.protocol_title'),
          value: resp.data.study_title,
        },
        {
          label: this.$t('ProtocolTitlePage.protocol_short_title'),
          value: resp.data.study_short_title,
        },
        {
          label: this.$t('ProtocolTitlePage.substance_name'),
          value: resp.data.substance_name,
        },
        {
          label: this.$t('ProtocolTitlePage.utn'),
          value: resp.data.universal_trial_number_utn,
        },
        {
          label: this.$t('ProtocolTitlePage.eudract_number'),
          value: resp.data.eudract_id,
        },
        {
          label: this.$t('ProtocolTitlePage.ind_number'),
          value: resp.data.ind_number,
        },
        {
          label: this.$t('ProtocolTitlePage.study_phase'),
          value: resp.data.trial_phase_code
            ? resp.data.trial_phase_code.name
            : '',
        },
      ]
    })
  },
}
</script>
