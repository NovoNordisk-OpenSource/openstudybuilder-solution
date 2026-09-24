<template>
  <div id="translated-text-container">
    <v-row>
      <v-col>
        <div class="text-headline-medium mb-4">
          {{ $t('CRFTranslatedTexts.add') }}
        </div>
      </v-col>
    </v-row>

    <v-row>
      <v-col>
        <v-select
          v-model="inputTranslatedText.text_type"
          data-cy="text-type"
          :label="t('CRFTranslatedTexts.text_type')"
          :items="translatedTextTypes"
          :readonly="props.readOnly"
        />
      </v-col>
      <v-col>
        <v-autocomplete
          v-model="inputTranslatedText.language"
          data-cy="language"
          :label="t('CRFTranslatedTexts.language')"
          :items="languages"
          item-title="name"
          :item-value="
            (lang) =>
              [lang._2T, lang._1].includes(inputTranslatedText.language)
                ? inputTranslatedText.language == lang._1
                  ? lang._1
                  : lang._2T
                : lang._1
          "
          :readonly="props.readOnly"
        />
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <div>
          <QuillEditor
            v-if="!showSource"
            ref="quillEditor"
            v-model:content="inputTranslatedText.text"
            data-cy="translated-texts"
            content-type="html"
            :options="editorOptions"
            :read-only="props.readOnly"
            :placeholder="
              inputTranslatedText.text ? '' : t('CRFTranslatedTexts.text')
            "
          />
          <v-textarea
            v-else
            v-model="sourceText"
            data-cy="source-text"
            :readonly="props.readOnly"
            auto-grow
            hide-details
          />
          <v-btn
            size="small"
            data-cy="toggle-source"
            variant="text"
            class="mt-1"
            :prepend-icon="showSource ? 'mdi-eye' : 'mdi-code-tags'"
            @click="toggleSource"
          >
            {{ showSource ? t('_global.rich_text') : t('_global.view_source') }}
          </v-btn>
        </div>
      </v-col>
    </v-row>
    <v-row>
      <v-col>
        <v-btn
          color="secondary"
          data-cy="add-translation"
          class="mr-2"
          block
          :readonly="props.readOnly"
          @click="add"
        >
          {{ t('_global.add') }}
        </v-btn>
      </v-col>
    </v-row>

    <v-row>
      <v-col>
        <div class="text-headline-medium mb-4">
          {{ $t('CRFTranslatedTexts.select') }}
        </div>
      </v-col>
    </v-row>

    <v-row>
      <v-col>
        <NNTable
          ref="table"
          v-model="modelValue"
          table-id="crf-translated-text-selection"
          :headers="headers"
          :items="translatedTexts"
          hide-default-switches
          hide-export-button
          :show-select="!readOnly"
          :hide-default-footer="props.readOnly"
          :hide-search-field="props.readOnly"
          :items-length="total"
          disable-filtering
          column-data-resource="concepts/odm-metadata/translated-texts"
          @filter="getTranslatedTexts"
        >
          <template #[`afterSearch`]>
            <v-checkbox
              v-model="operator"
              data-cy="exact-match-checkbox"
              :label="t('CRFTranslatedTexts.exact_match')"
              class="ms-5 mt-5"
            />
          </template>
          <template #[`item.actions`]="{ item }">
            <v-btn
              icon="mdi-pencil"
              data-cy="edit-translation-item"
              variant="flat"
              :disabled="props.readOnly"
              @click.stop="edit(item)"
            />
          </template>
          <template #[`item.text_type`]="{ value }">
            {{
              translatedTextTypes.find((type) => type.value === value)?.title ||
              value
            }}
          </template>
          <template #[`item.language`]="{ value }">
            {{
              languages.find((lang) => [lang._1, lang._2T].includes(value))
                ?.name || value
            }}
          </template>
          <template #[`item.text`]="{ value }">
            <span v-html="sanitizeHTML(value)"></span>
          </template>
        </NNTable>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { ref, computed, inject, onMounted, watch } from 'vue'
import { QuillEditor } from '@vueup/vue-quill'
import QuillTableBetter from 'quill-table-better'
import filteringParameters from '@/utils/filteringParameters'
import NNTable from '@/components/tools/NNTable.vue'
import translatedTextTypes from '@/constants/crfTranslatedTextTypes.js'
import crfs from '@/api/crfs'
import iso from '@/api/iso'
import regex from '@/utils/regex'
import { sanitizeHTML } from '@/utils/sanitize'
import parameters from '@/constants/parameters'

const { t } = useI18n()
const notificationHub = inject('notificationHub')

const props = defineProps({
  readOnly: {
    type: Boolean,
    default: false,
  },
})

const modelValue = defineModel({
  type: Array,
  default: () => [],
})

const headers = computed(() => [
  props.readOnly
    ? ''
    : { title: '', key: 'actions', width: '1%', condition: false },
  { title: t('CRFTranslatedTexts.text_type'), key: 'text_type' },
  { title: t('CRFTranslatedTexts.language'), key: 'language' },
  { title: t('CRFTranslatedTexts.text'), key: 'text' },
])

const editorOptions = {
  theme: 'snow',
  modules: {
    toolbar: [
      ['bold', 'italic', 'underline', 'strike'],
      ['blockquote', 'code-block'],
      [{ font: [] }],
      [{ size: ['small', false, 'large', 'huge'] }],
      [{ header: [1, 2, 3, 4, 5, 6, false] }],
      [{ list: 'ordered' }, { list: 'bullet' }, { list: 'check' }],
      [{ script: 'sub' }, { script: 'super' }],
      [{ align: [] }],
      [{ indent: '-1' }, { indent: '+1' }],
      [{ direction: 'rtl' }],
      [{ color: [] }, { background: [] }],
      ['clean'],
      ['table-better'],
    ],
    'table-better': {
      toolbarTable: true,
      menus: [
        'column',
        'row',
        'merge',
        'table',
        'cell',
        'wrap',
        'copy',
        'delete',
      ],
    },
    keyboard: {
      bindings: QuillTableBetter.keyboardBindings,
    },
  },
}

const inputTranslatedText = ref({
  text_type: '',
  language: parameters.EN,
  text: '',
})

const table = ref(false)
const operator = ref(false)
const showSource = ref(false)
const quillEditor = ref(null)
const sourceText = ref('')
const savedSourceText = ref('')

const stripParagraphWrap = (html) =>
  html?.replaceAll(/<\/?p>/g, '').trim() || ''

const toggleSource = () => {
  if (showSource.value) {
    inputTranslatedText.value.text = sourceText.value
    savedSourceText.value = sourceText.value
  } else {
    const quillOutput = inputTranslatedText.value.text || ''
    // Only update sourceText from Quill if the user made real edits (not just Quill's auto <p> wrapping)
    if (
      stripParagraphWrap(quillOutput) ===
      stripParagraphWrap(savedSourceText.value)
    ) {
      sourceText.value = savedSourceText.value
    } else {
      sourceText.value = quillOutput
    }
  }
  showSource.value = !showSource.value
}

watch(operator, () => {
  table.value.filterTable()
})

const languages = ref([])
const translatedTexts = ref([])
const total = ref(0)

onMounted(() => {
  iso.get('639').then((resp) => {
    languages.value = resp.data
  })

  getTranslatedTexts()
})

const getTranslatedTexts = (filters, options, filtersUpdated) => {
  if (props.readOnly) {
    translatedTexts.value = [...modelValue.value]
  } else {
    const params = filteringParameters.prepareParameters(
      options,
      null,
      filtersUpdated
    )
    params.search = options.search
    params.op = operator.value ? 'eq' : 'co'
    params.sort_by = 'language,text_type'
    params.fields = 'text_type,language,text'
    crfs.getTranslatedTexts(params).then((resp) => {
      translatedTexts.value = [
        ...modelValue.value,
        ...resp.data.items.filter((translatedText) => {
          return !modelValue.value.some(
            (tt) =>
              tt.text_type === translatedText.text_type &&
              tt.language === translatedText.language &&
              tt.text === translatedText.text
          )
        }),
      ]
      total.value = resp.data.total
    })
  }
}

const add = () => {
  if (showSource.value) {
    inputTranslatedText.value.text = sourceText.value
  }

  const lowerCaseLanguage = inputTranslatedText.value.language.toLowerCase()
  const parsedText = regex.clearEmptyHtml(inputTranslatedText.value.text)

  if (inputTranslatedText.value.text_type && lowerCaseLanguage && parsedText) {
    const translatedText = {
      text_type: inputTranslatedText.value.text_type,
      language: lowerCaseLanguage,
      text: parsedText,
    }

    const isDuplicate = (items) => {
      return items.some(
        (item) =>
          item.text_type === translatedText.text_type &&
          item.language === translatedText.language.toLocaleLowerCase() &&
          item.text === translatedText.text
      )
    }

    if (!isDuplicate(modelValue.value)) {
      modelValue.value.push({ ...translatedText })
    }

    if (!isDuplicate(translatedTexts.value)) {
      translatedTexts.value = [
        ...modelValue.value,
        ...translatedTexts.value.filter((translatedText) => {
          return !modelValue.value.some(
            (tt) =>
              tt.text_type === translatedText.text_type &&
              tt.language === translatedText.language &&
              tt.text === translatedText.text
          )
        }),
      ]
    }

    inputTranslatedText.value = {
      text_type: '',
      language: parameters.EN,
      text: '<p></p>',
    }
    sourceText.value = ''
  } else {
    notificationHub.add({
      msg: t('CRFTranslatedTexts.missing_fields'),
      type: 'info',
    })
  }
}

const edit = (item) => {
  inputTranslatedText.value = { ...item }
  modelValue.value = modelValue.value.filter(
    (tt) =>
      !(
        tt.text_type === item.text_type &&
        tt.language === item.language &&
        tt.text === item.text
      )
  )

  notificationHub.add({
    msg: t('CRFTranslatedTexts.editing_translated_text'),
    type: 'info',
  })

  document
    .getElementById('translated-text-container')
    .scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>
