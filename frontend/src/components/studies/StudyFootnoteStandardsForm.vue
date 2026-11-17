<template>
  <div>
    <div class="d-flex align-center flex-wrap pa-2">
      <v-btn
        icon="mdi-arrow-left"
        color="secondary"
        data-cy="footnote-standards-back"
        size="small"
        variant="text"
        :disabled="adding"
        @click="emit('cancel')"
      />
      <span class="font-weight-medium ml-1">
        {{ $t('ProtocolFlowchart.select_from_standards') }}
      </span>
      <v-spacer />
      <v-switch
        v-model="preInstanceMode"
        class="px-4 py-2"
        data-cy="footnote-standards-pre-instance-switch"
        :label="$t('StudyFootnoteForm.show_pre_instances')"
        :disabled="adding"
        hide-details
      />
    </div>
    <v-divider />
    <SelectMenuSearch
      v-model="search"
      :placeholder="$t('_global.search')"
      autofocus
      data-cy="footnote-standards-search"
      class="px-4"
    />
    <div class="standards-list px-4">
      <v-progress-linear v-if="loading" indeterminate color="nnBaseBlue" />
      <v-list
        v-else-if="rows.length"
        data-cy="footnote-standards-list"
        density="compact"
      >
        <v-list-item
          v-for="{ template, added } in rows"
          :key="template.uid"
          :disabled="added || adding"
          @click="toggle(template)"
        >
          <template #prepend>
            <v-list-item-action start>
              <v-checkbox-btn
                :model-value="added || selectedUids.has(template.uid)"
                readonly
                tabindex="-1"
              />
            </v-list-item-action>
          </template>
          <NNParameterHighlighter
            :name="template.name"
            :show-prefix-and-postfix="false"
            :tooltip="false"
          />
          <template v-if="added" #append>
            <span class="text-body-small ml-2">
              {{ $t('ProtocolFlowchart.standard_footnote_added') }}
            </span>
          </template>
        </v-list-item>
      </v-list>
      <div v-else class="standards-empty text-center text-medium-emphasis pa-4">
        {{
          templates.length
            ? $t('ProtocolFlowchart.no_matching_standard_footnotes')
            : $t('ProtocolFlowchart.no_standard_footnotes')
        }}
      </div>
    </div>
    <v-divider />
    <div class="d-flex justify-end ga-2 pa-3">
      <v-btn
        variant="outlined"
        :disabled="adding"
        data-cy="cancel-footnote-standards"
        @click="emit('cancel')"
      >
        {{ $t('_global.cancel') }}
      </v-btn>
      <v-btn
        color="secondary"
        variant="flat"
        data-cy="submit-footnote-standards"
        :disabled="!chosenTemplates.length"
        :loading="adding"
        @click="submit"
      >
        {{
          chosenTemplates.length
            ? $t('ProtocolFlowchart.add_selected_footnotes', {
                count: chosenTemplates.length,
              })
            : $t('_global.add')
        }}
      </v-btn>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import study from '@/api/study'
import footnoteTemplates from '@/api/footnoteTemplates'
import templatePreInstances from '@/api/templatePreInstances'
import libraryConstants from '@/constants/libraries'
import statuses from '@/constants/statuses'
import { getSoaFootnoteType, normalizeFootnoteText } from '@/utils/soaFootnotes'
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import SelectMenuSearch from '@/components/tools/SelectMenuSearch.vue'

const props = defineProps({
  existingNames: {
    type: Set,
    required: true,
  },
  // Items the new footnotes are assigned to, in the layout given by `layout`.
  referencedItems: {
    type: Array,
    default: () => [],
  },
  layout: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['cancel', 'created'])

const studiesGeneralStore = useStudiesGeneralStore()
const notificationHub = inject('notificationHub')
const footnotePreInstances = templatePreInstances('footnote')

const search = ref('')
const preInstanceMode = ref(true)
const templates = ref([])
const selectedUids = ref(new Set())
const loading = ref(false)
const adding = ref(false)
let latestRequest = 0

function plainText(template) {
  if (template.name_plain != null) {
    return template.name_plain
  }

  if (template.name == null) {
    return ''
  }

  const parser = document.createElement('div')
  parser.innerHTML = template.name
  return parser.textContent ?? ''
}

function isAdded(template) {
  return props.existingNames.has(normalizeFootnoteText(plainText(template)))
}

// Footnotes already in the study stay listed (so a search explains their absence)
// but sink below the ones that can still be picked.
const rows = computed(() => {
  const words = (search.value ?? '').toLowerCase().split(/\s+/).filter(Boolean)
  return templates.value
    .filter((template) => {
      const text = plainText(template).replace(/[[\]]/g, '').toLowerCase()
      return words.every((word) => text.includes(word))
    })
    .map((template) => ({ template, added: isAdded(template) }))
    .sort((a, b) => a.added - b.added)
})

const chosenTemplates = computed(() =>
  templates.value.filter(
    (template) => selectedUids.value.has(template.uid) && !isAdded(template)
  )
)

async function fetchTemplates() {
  const request = ++latestRequest
  const asPreInstances = preInstanceMode.value
  loading.value = true
  templates.value = []
  selectedUids.value = new Set()
  try {
    const typeTerm = await getSoaFootnoteType()
    if (!typeTerm) {
      return
    }
    const filters = {
      'library.name': { v: [libraryConstants.LIBRARY_SPONSOR] },
    }
    if (asPreInstances) {
      filters.template_type_uid = { v: [typeTerm.term_uid] }
    } else {
      filters['type.name.sponsor_preferred_name'] = {
        v: [typeTerm.sponsor_preferred_name],
      }
    }
    const endpoint = asPreInstances ? footnotePreInstances : footnoteTemplates
    const resp = await endpoint.get({
      status: statuses.FINAL,
      page_size: 0,
      filters,
    })
    if (request === latestRequest) {
      templates.value = resp.data.items
    }
  } finally {
    if (request === latestRequest) {
      loading.value = false
    }
  }
}

fetchTemplates()
watch(preInstanceMode, fetchTemplates)

function toggle(template) {
  const selected = new Set(selectedUids.value)
  if (selected.has(template.uid)) {
    selected.delete(template.uid)
  } else {
    selected.add(template.uid)
  }
  selectedUids.value = selected
}

async function submit() {
  if (adding.value || !chosenTemplates.value.length) {
    return
  }
  const asPreInstances = preInstanceMode.value
  const footnotes = chosenTemplates.value.map((template) => ({
    footnote_data: {
      footnote_template_uid: asPreInstances
        ? template.template_uid
        : template.uid,
      parameter_terms: asPreInstances ? template.parameter_terms : [],
      library_name: template.library.name,
    },
    referenced_items: props.referencedItems,
    ...(props.layout ? { layout: props.layout } : {}),
  }))
  notificationHub.clearErrors()
  adding.value = true
  try {
    await study.batchCreateStudyFootnotes(
      studiesGeneralStore.selectedStudy.uid,
      footnotes
    )
    emit('created')
  } finally {
    adding.value = false
  }
}
</script>

<style scoped lang="scss">
.standards-list {
  display: flex;
  flex-direction: column;
  min-height: 160px;
  max-height: 360px;
  overflow-y: auto;
}

.standards-empty {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: center;
}
</style>
