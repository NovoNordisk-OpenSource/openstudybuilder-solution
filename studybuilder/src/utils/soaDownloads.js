import study from '@/api/study'
import exportLoader from '@/utils/exportLoader'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const studiesGeneralStore = useStudiesGeneralStore()

async function docxDownload(layout) {
  const response = await study.getStudyProtocolFlowchartDocx(
    studiesGeneralStore.selectedStudy.uid,
    { layout }
  )

  download(response, ` ${layout} SoA.docx`)
}

async function csvDownload(layout) {
  const uid = studiesGeneralStore.selectedStudy.uid
  let response

  switch (layout) {
    case 'detailed':
      response = await study.exportStudyDetailedSoa(uid)
      break
    case 'protocol':
      response = await study.exportStudyProtocolSoa(uid)
      break
    case 'operational':
      response = await study.exportStudyOperationalSoa(uid)
      break
  }

  if (response) {
    download(response, ` ${layout} SoA.csv`)
  }
}

async function excelDownload(layout) {
  const uid = studiesGeneralStore.selectedStudy.uid
  let response

  switch (layout) {
    case 'detailed':
      response = await study.exportStudyDetailedSoaExcel(uid)
      break
    case 'protocol':
      response = await study.exportStudyProtocolSoaExcel(uid)
      break
    case 'operational':
      response = await study.exportStudyOperationalSoaExcel(uid)
      break
  }

  if (response) {
    download(response, ` ${layout} SoA.xlsx`)
  }
}

function download(response, type) {
  const filename =
    studiesGeneralStore.selectedStudy.current_metadata.identification_metadata
      .study_id + type
  exportLoader.downloadFile(
    response.data,
    response.headers['content-type'],
    filename
  )
}

export default {
  docxDownload,
  csvDownload,
  excelDownload,
}
