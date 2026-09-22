<template>
  <div v-if="selectedStudyVersion === null" class="pa-4">
    <div class="mt-6 d-flex align-center">
      <span class="text-headline-small">{{
        $t('ProtocolElementsObjectiveTable.title')
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
      id="ProtocolElementsObjective"
      class="mt-4"
      v-html="sanitizeHTMLHandler(document)"
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
      document: '',
      loadingMessage: '',
    }
  },
  watch: {
    update(newVal, oldVal) {
      if (newVal !== oldVal) this.updateDocument()
    },
  },
  mounted() {
    this.updateDocument()
  },
  methods: {
    sanitizeHTMLHandler(html) {
      return sanitizeHTML(html)
    },
    updateDocument() {
      this.loadingMessage = this.$t('ProtocolElementsObjectiveTable.loading')
      study
        .getStudyObjectivesHtml(this.studyUid)
        .then((resp) => {
          this.document = resp.data
        })
        .then(this.finally)
        .catch(this.finally)
    },
    downloadDocx() {
      this.loadingMessage = this.$t(
        'ProtocolElementsObjectiveTable.downloading'
      )
      study
        .getStudyObjectivesDocx(this.studyUid)
        .then((response) => {
          exportLoader.downloadFile(
            response.data,
            response.headers['content-type'] ||
              'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            `${this.studyUid} study-objectives.docx`
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
#ObjectivesEndpointsTable {
  width: 100%;
  text-align: left;
  border: 1px solid black;
  border-spacing: 0px;
  border-collapse: collapse;
  table-layout: auto;
  resize: both;

  & TH {
    text-align: center;
    font-weight: bold;
  }

  &,
  & TH,
  & TD {
    border: 1px solid black;
    padding: 4px;
  }

  & THEAD {
    background-color: var(--v-greyBackground-base);
    text-align: center;
  }

  & TBODY {
    & TH.objective-level,
    & TH.endpoint-level {
      text-align: left;
      font-style: italic;
    }

    & TR TD {
      vertical-align: middle;
    }

    & TR TD:first-child {
      vertical-align: top;
    }
  }
}
</style>
