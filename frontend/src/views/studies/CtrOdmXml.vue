<template>
  <div class="pa-4">
    <div class="mt-6 d-flex align-center">
      <span class="text-headline-small">{{ $t('CtrOdmXmlVue.title') }}</span>
      <v-spacer />
      <span class="text-center font-italic">{{ loadingMessage }}</span>
      <v-spacer />
      <div class="d-flex ml-4">
        <v-btn
          color="secondary"
          class="ml-3"
          :disabled="Boolean(loadingMessage)"
          @click="downloadXml($event)"
        >
          {{ $t('CtrOdmXmlVue.download') }}
        </v-btn>
      </div>
    </div>
    <div
      id="CtrOdmHtml"
      class="mt-4"
      v-html="sanitizeHTMLHandler(htmlDocument)"
    />
  </div>
</template>

<script>
import { studySelectedNavigationGuard } from '@/mixins/studies'
import study from '@/api/study'
import exportLoader from '@/utils/exportLoader'
import axios from 'axios'
import { sanitizeHTML } from '@/utils/sanitize'

export default {
  components: {},
  mixins: [studySelectedNavigationGuard],
  props: {
    update: {
      type: Number,
      default: null,
    },
  },
  data() {
    return {
      loadingMessage: '',
      htmlDocument: '',
      stylesheetPath: 'odm_template_sdtmcrf.xsl',
    }
  },
  computed: {
    stylesheetUrl() {
      if (process.env.NODE_ENV === 'development') {
        return `/${this.stylesheetPath}`
      } else {
        return `https://${location.host}/${this.stylesheetPath}`
      }
    },
  },
  watch: {
    update(newVal, oldVal) {
      if (newVal !== oldVal) this.renderXml()
    },
  },
  mounted() {
    this.renderXml()
  },
  methods: {
    sanitizeHTMLHandler(html) {
      return sanitizeHTML(html)
    },
    renderXml() {
      this.loadingMessage = this.$t('CtrOdmXmlVue.loading')
      study
        .getCtrOdmXml(this.selectedStudy.uid)
        .then((resp) => {
          const parser = new DOMParser()
          const xml = parser.parseFromString(resp.data, 'text/xml')
          axios.get(this.stylesheetUrl).then((resp) => {
            const xsltProcessor = new XSLTProcessor()
            xsltProcessor.importStylesheet(
              parser.parseFromString(resp.data, 'text/xml')
            )
            const doc = xsltProcessor.transformToDocument(xml)
            const bodies = doc.getElementsByTagName('body')
            if (bodies.length) {
              this.htmlDocument = new XMLSerializer().serializeToString(
                bodies[0]
              )
            }
          })
        })
        .then(this.finally)
        .catch(this.finally)
    },
    downloadXml() {
      this.loadingMessage = this.$t('CtrOdmXmlVue.downloading')
      study
        .downloadCtrOdmXml(this.selectedStudy.uid)
        .then((response) => {
          exportLoader.downloadFile(
            response.data,
            response.headers['content-type'] || 'text/xml',
            `${this.selectedStudy.uid} CTR-ODM.xml`
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
