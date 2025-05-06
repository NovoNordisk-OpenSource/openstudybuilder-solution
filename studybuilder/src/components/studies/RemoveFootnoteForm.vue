<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('StudyRemoveFootnoteForm.title')"
    max-width="500px"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      {{ $t('StudyRemoveFootnoteForm.remove_info') }}
      <v-form ref="observer" class="mt-4">
        <v-checkbox
          v-for="item of footnotes"
          :key="item.uid"
          v-model="selectedFootnotes"
          :label="
            item.footnote ? item.footnote.name_plain : item.template.name_plain
          "
          :value="item.uid"
          density="compact"
        ></v-checkbox>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import { ref, watch } from 'vue'
import filteringParameters from '@/utils/filteringParameters'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import study from '@/api/study'

const studiesGeneralStore = useStudiesGeneralStore()
const emit = defineEmits(['close'])

const props = defineProps({
  itemUid: {
    type: String,
    default: null,
  },
  open: Boolean,
})

const footnotes = ref([])
const selectedFootnotes = ref([])

watch(
  () => props.itemUid,
  () => {
    fetchFootnotes()
  }
)

function fetchFootnotes(filters, options, filtersUpdated) {
  const params = filteringParameters.prepareParameters(
    options,
    filters,
    filtersUpdated
  )
  params.filters = {
    'referenced_items.item_uid': { v: [props.itemUid], op: 'co' },
  }
  study
    .getStudyFootnotes(studiesGeneralStore.selectedStudy.uid, params)
    .then((resp) => {
      footnotes.value = resp.data.items
    })
}

function submit() {
  let footnotesToSave = []
  selectedFootnotes.value.forEach(async (footnote) => {
    let elementsForFootnote = footnotes.value.find(
      (a) => a.uid === footnote
    ).referenced_items
    elementsForFootnote = elementsForFootnote.filter((item) => {
      if (item.item_uid !== props.itemUid) {
        return true
      }
    })
    footnotesToSave.push({
      referenced_items: elementsForFootnote,
      study_soa_footnote_uid: footnote,
    })
  })
  study
    .batchUpdateStudyFootnotes(
      studiesGeneralStore.selectedStudy.uid,
      footnotesToSave
    )
    .then(() => {
      emit('close')
    })
}

function close() {
  emit('close')
}
</script>
