<template>
  <v-card>
    <v-card-title>
      {{ $t('OdmViewer.export') + item.name }}
    </v-card-title>
    <v-card-text>
      <v-form ref="observer">
        <v-row>
          <v-col cols="4">
            <v-select
              v-model="format"
              class="mt-5"
              :label="$t('OdmViewer.format')"
              :items="formats"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
          <v-col cols="2">
            <v-switch
              v-model="draft"
              class="mt-6"
              :label="$t('_global.draft')"
            />
          </v-col>
          <v-col cols="4">
            <label>{{ $t('OdmViewer.stylesheet') }}</label>
            <v-radio-group v-model="exportParams.selectedStylesheet">
              <v-radio
                :label="$t('OdmViewer.crf_with_annotations')"
                value="with-annotations"
              />
              <v-radio :label="$t('OdmViewer.falcon')" value="falcon" />
            </v-radio-group>
          </v-col>
        </v-row>
      </v-form>
    </v-card-text>
    <v-card-actions>
      <v-spacer />
      <v-btn class="primary" :loading="loading" @click="exportElement()">
        {{ $t('_global.export') }}
      </v-btn>
      <v-btn class="secondary-btn" color="white" @click="close()">
        {{ $t('_global.close') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup>
import { inject, reactive, ref } from 'vue'

import crfs from '@/api/crfs'
import statuses from '@/constants/statuses'
import exportLoader from '@/utils/exportLoader'
import { DateTime } from 'luxon'

const props = defineProps({
  open: Boolean,
  item: {
    type: Object,
    default: null,
  },
  type: {
    type: String,
    default: null,
  },
})

const emit = defineEmits(['close'])

const formRules = inject('formRules')

const observer = ref(null)

const formats = ['PDF', 'HTML', 'XML']
const draft = ref(false)
const format = ref(null)

const exportParams = reactive({
  target_type: '',
  selectedStylesheet: 'with-annotations',
  status: '',
  allowed_namespaces: '&allowed_namespaces=*',
})

const loading = ref(false)

const close = () => {
  emit('close')
}

const setExportParams = (item, type) => {
  exportParams.targets = `targets=${item.uid}&`
  exportParams.target_type = type
  exportParams.status = draft.value
    ? `${statuses.FINAL}&status=${statuses.DRAFT}`.toLowerCase()
    : statuses.FINAL.toLowerCase()
}

const getDownloadFileName = (item) => {
  let stylesheet = '_with_annotations_crf_'
  if (exportParams.selectedStylesheet === 'falcon') {
    stylesheet = '_falcon_crf_'
  }
  const templateName = item.name
  return `${templateName + stylesheet + DateTime.local().toFormat('yyyy-MM-dd HH:mm')}`
}

const exportPdf = (item) => {
  console.log('exportPdf called', exportParams)
  crfs
    .getPdf(exportParams)
    .then((resp) => {
      exportLoader.downloadFile(
        resp.data,
        'application/pdf',
        getDownloadFileName(item)
      )
      close()
    })
    .finally(() => {
      loading.value = false
    })
}

const exportHtml = (item) => {
  crfs
    .getXml(exportParams)
    .then(async (resp) => {
      const parser = new globalThis.DOMParser()
      const xml = parser.parseFromString(resp.data, 'application/xml')
      const xsltProcessor = new globalThis.XSLTProcessor()
      crfs.getXsl(exportParams.selectedStylesheet).then((xslResp) => {
        const xmlDoc = parser.parseFromString(xslResp.data, 'text/xml')
        xsltProcessor.importStylesheet(xmlDoc)
        exportLoader.downloadFile(
          new globalThis.XMLSerializer().serializeToString(
            xsltProcessor.transformToDocument(xml)
          ),
          'text/html',
          getDownloadFileName(item)
        )
        close()
      })
    })
    .finally(() => {
      loading.value = false
    })
}

const exportXml = (item) => {
  crfs
    .getXml(exportParams)
    .then((resp) => {
      exportLoader.downloadFile(
        resp.data,
        'text/xml',
        getDownloadFileName(item)
      )
      close()
    })
    .finally(() => {
      loading.value = false
    })
}

const exportElement = async () => {
  const { valid } = await observer.value.validate()
  if (!valid) return

  loading.value = true
  setExportParams(props.item, props.type)

  switch (format.value) {
    case 'PDF':
      exportPdf(props.item)
      break
    case 'HTML':
      exportHtml(props.item)
      break
    case 'XML':
      exportXml(props.item)
  }
}
</script>
