<template>
  <div v-if="selectedStudyVersion === null" class="pa-4">
    <div class="mt-6 d-flex align-center">
      <span class="text-headline-small">{{
        $t('ProtocolInterventionsTable.title')
      }}</span>
      <v-spacer />
      <span class="text-center font-italic">{{ loadingMessage }}</span>
      <v-spacer />
      <div class="d-flex ml-4">
        <v-btn
          color="secondary"
          rounded
          :disabled="Boolean(loadingMessage)"
          @click="downloadDocx($event)"
        >
          {{ $t('_global.download_docx') }}
        </v-btn>
      </div>
    </div>
    <div
      id="ProtocolInterventions"
      class="mt-4"
      v-html="sanitizeHTMLHandler(protocolInterventionsTable)"
    />
  </div>
  <div v-else>
    <UnderConstruction :message="$t('UnderConstruction.not_supported')" />
  </div>
</template>

<script>
import study from '@/api/study'
import exportLoader from '@/utils/exportLoader'
import UnderConstruction from '@/components/layout/UnderConstruction.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { computed } from 'vue'
import { sanitizeHTML } from '@/utils/sanitize'

export default {
  components: {
    UnderConstruction,
  },
  props: {
    studyUid: {
      type: String,
      default: '',
    },
    update: {
      type: Number,
      default: 0,
    },
  },
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudyVersion: computed(
        () => studiesGeneralStore.selectedStudyVersion
      ),
    }
  },
  data() {
    return {
      protocolInterventionsTable: '',
      loadingMessage: '',
    }
  },
  watch: {
    update(newVal, oldVal) {
      if (newVal !== oldVal) this.updateTable()
    },
  },
  mounted() {
    this.updateTable()
  },
  methods: {
    sanitizeHTMLHandler(html) {
      return sanitizeHTML(html)
    },
    updateTable() {
      this.loadingMessage = this.$t('ProtocolInterventionsTable.loading')
      study
        .getStudyProtocolInterventionsTableHtml(this.studyUid)
        .then((resp) => {
          this.protocolInterventionsTable = resp.data
        })
        .then(this.finally)
        .catch(this.finally)
    },
    downloadDocx() {
      this.loadingMessage = this.$t('ProtocolInterventionsTable.downloading')
      study
        .getStudyProtocolInterventionsTableDocx(this.studyUid)
        .then((response) => {
          exportLoader.downloadFile(
            response.data,
            response.headers['content-type'] ||
              'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            `${this.studyUid} interventions.docx`
          )
        })
        .then(this.finally)
        .catch(this.finally)
    },
    finally(error) {
      this.loadingMessage = ''
      if (error) throw error
    },
  },
}
</script>

<style lang="scss">
#StudyInterventionsTable {
  width: 100%;
  table-layout: auto;
  resize: both;
  border-collapse: collapse;

  &,
  & TH,
  & TD {
    border: 1px solid #ebe8e5;
    padding: 1px 3px;
  }

  & THEAD {
    & TH {
      text-align: center;
      font-weight: bold;
    }

    & TH:first-child {
      text-align: left;
    }
  }

  & TBODY {
    & TH {
      text-align: left;
      font-weight: bold;
    }

    & TR TD {
      text-align: left;
    }
  }
}
</style>
