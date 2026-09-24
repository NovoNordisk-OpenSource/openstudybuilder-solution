<template>
  <div class="mt-6 d-flex align-center">
    <span class="text-headline-small">{{
      $t('StudyProtocolElementsView.study_design')
    }}</span>
    <v-spacer />
    <span class="text-center font-italic">{{ loadingMessage }}</span>
    <v-spacer />
    <div class="d-flex ml-4">
      <v-btn
        color="secondary"
        class="mr-3"
        rounded
        :disabled="Boolean(loadingMessage)"
        @click="downloadSvg($event)"
      >
        {{ $t('_global.download_svg') }}
      </v-btn>
    </div>
  </div>
  <div
    id="studyDesign"
    class="mt-4"
    v-html="sanitizeHTMLHandler(studyDesignSVG)"
  />
</template>

<script>
import study from '@/api/study'
import exportLoader from '@/utils/exportLoader'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { computed } from 'vue'
import { sanitizeHTML } from '@/utils/sanitize'

export default {
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
      studyDesignSVG: '',
      loadingMessage: '',
    }
  },
  watch: {
    update(newVal, oldVal) {
      if (newVal !== oldVal) this.updateSvg()
    },
  },
  mounted() {
    this.updateSvg()
  },
  methods: {
    sanitizeHTMLHandler(html) {
      return sanitizeHTML(html)
    },
    updateSvg() {
      this.loadingMessage = this.$t('StudyProtocolElementsView.loading')
      study
        .getStudyDesignFigureSvg(this.studyUid)
        .then((resp) => {
          this.studyDesignSVG = resp.data
        })
        .then(this.finally)
        .catch(this.finally)
    },
    downloadSvg() {
      this.loadingMessage = this.$t('StudyProtocolElementsView.downloading')
      study
        .getStudyDesignFigureSvgArray(this.studyUid)
        .then((response) => {
          exportLoader.downloadFile(
            response.data,
            response.headers['content-type'] || 'image/svg+xml',
            `${this.studyUid} design.svg`
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
