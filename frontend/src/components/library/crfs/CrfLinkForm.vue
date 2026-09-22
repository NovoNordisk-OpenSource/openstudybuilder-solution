<template>
  <SimpleFormDialog
    ref="formRef"
    :title="$t('CRFTree.link') + ' ' + itemsTypeName"
    :help-items="helpItems"
    :open="open"
    max-width="1200px"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-col class="pt-0 mt-0">
        <NNTable
          table-id="crf-link-form"
          :headers="availableItemsHeaders"
          item-value="uid"
          :items="items"
          hide-export-button
          hide-default-switches
          only-text-search
          column-data-resource="ct/codelists"
          :items-length="total"
          table-height="auto"
          @filter="getItems"
        >
          <template #[`item.oid`]="{ item }">
            {{ item.oid }}
          </template>
          <template #[`item.displayText`]="{ item }">
            <div v-html="sanitizeHTMLHandler(getDisplayText(item))" />
          </template>
          <template #[`item.question`]="{ item }">
            <div v-html="sanitizeHTMLHandler(getQuestion(item))" />
          </template>
          <template #[`item.desc`]="{ item }">
            <div v-html="sanitizeHTMLHandler(getDescription(item))" />
          </template>
          <template #[`item.notes`]="{ item }">
            <div v-html="sanitizeHTMLHandler(getNotes(item))" />
          </template>
          <template #[`item.add`]="{ item }">
            <v-btn
              v-if="!checkIfLinked(item)"
              icon="mdi-content-copy"
              class="mt-1 rightButtons"
              data-cy="add-item-link"
              variant="text"
              @click="addItem(item)"
            />
            <v-btn
              v-else
              icon="mdi-delete-outline"
              class="mt-1 rightButtons"
              color="error"
              data-cy="remove-item-link"
              variant="text"
              @click="removeItem(item)"
            />
          </template>
        </NNTable>
      </v-col>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import crfs from '@/api/crfs'
import constants from '@/constants/parameters'
import NNTable from '@/components/tools/NNTable.vue'
import filteringParameters from '@/utils/filteringParameters'
import { sanitizeHTML } from '@/utils/sanitize'

const props = defineProps({
  itemToLink: {
    type: Object,
    default: null,
  },
  itemsType: {
    type: String,
    default: null,
  },
  open: Boolean,
})

const notificationHub = inject('notificationHub')

const emit = defineEmits(['close'])

const { t } = useI18n()
const formRef = ref()

const helpItems = ref([])
const items = ref([])
const chosenItems = ref([])
const total = ref(0)

const availableItemsHeaders = computed(() => {
  const headers = [
    { title: '', key: 'add', width: '5%' },
    { title: t('_global.name'), key: 'name', width: '15%' },
    { title: t('_global.oid'), key: 'oid', width: '10%' },
    { title: t('CRFTree.display_text'), key: 'displayText', width: '15%' },
  ]

  if (props.itemsType === 'items') {
    headers.push({
      title: t('CRFTree.question'),
      key: 'question',
      width: '15%',
    })
  }

  headers.push(
    { title: t('_global.description'), key: 'desc', width: '20%' },
    {
      title: t('CRFTree.sponsor_instruction'),
      key: 'notes',
      width: '20%',
    }
  )

  return headers
})

const itemsTypeName = computed(() => {
  if (props.itemsType === 'forms') {
    return t('CRFTree.forms')
  }
  if (props.itemsType === 'item-groups') {
    return t('CRFTree.item_groups')
  }
  return t('CRFTree.items')
})

watch(
  () => props.itemToLink,
  () => {
    initForm()
  }
)

const sanitizeHTMLHandler = (html) => {
  return sanitizeHTML(html)
}

const getDescription = (item) => {
  const engDesc = item.translated_texts.find(
    (el) =>
      [constants.EN, constants.ENG].includes(el.language) &&
      el.text_type == 'Description'
  )
  return engDesc ? engDesc.text : ''
}

const getNotes = (item) => {
  const engDesc = item.translated_texts.find(
    (el) =>
      [constants.EN, constants.ENG].includes(el.language) &&
      el.text_type == 'osb:DesignNotes'
  )
  return engDesc ? engDesc.text : ''
}

const getDisplayText = (item) => {
  const engText = item.translated_texts.find(
    (el) =>
      [constants.EN, constants.ENG].includes(el.language) &&
      el.text_type == 'osb:DisplayText'
  )
  return engText ? engText.text : ''
}

const getQuestion = (item) => {
  const engQuestion = item.translated_texts.find(
    (el) =>
      [constants.EN, constants.ENG].includes(el.language) &&
      el.text_type == 'Question'
  )
  return engQuestion ? engQuestion.text : ''
}

const submit = () => {
  const payload = []
  chosenItems.value.forEach((el, index) => {
    payload.push({
      uid: el.uid ? el.uid : el,
      order_number: index + 1,
      mandatory: el.mandatory ? el.mandatory : 'No',
      data_entry_required: el.data_entry_required
        ? el.data_entry_required
        : 'No',
      sdv: el.sdv ? el.sdv : 'No',
      collection_exception_condition_oid: el.collection_exception_condition_oid
        ? el.collection_exception_condition_oid
        : null,
      vendor: el?.vendor || { attributes: [] },
    })
  })
  switch (props.itemsType) {
    case 'forms':
      crfs.addFormsToCollection(payload, props.itemToLink.uid, true).then(
        () => {
          notificationHub.add({
            type: 'success',
            msg: t('CRFTree.success_forms', {
              count: payload.length,
              name: props.itemToLink.name,
            }),
          })
          emit('close')
        },
        () => {
          formRef.value.working = false
        }
      )
      return
    case 'item-groups':
      crfs.addItemGroupsToForm(payload, props.itemToLink.uid, true).then(
        () => {
          notificationHub.add({
            type: 'success',
            msg: t('CRFTree.success_item_groups', {
              count: payload.length,
              name: props.itemToLink.name,
            }),
          })
          emit('close')
        },
        () => {
          formRef.value.working = false
        }
      )
      return
    case 'items':
      payload.forEach((el) => {
        el.key_sequence = el.key_sequence ? el.key_sequence : constants.NULL
        el.method_oid = el.method_oid ? el.method_oid : constants.NULL
        el.imputation_method_oid = el.imputation_method_oid
          ? el.imputation_method_oid
          : constants.NULL
        el.role = el.role ? el.role : constants.NULL
        el.role_codelist_oid = el.role_codelist_oid
          ? el.role_codelist_oid
          : constants.NULL
      })
      crfs.addItemsToItemGroup(payload, props.itemToLink.uid, true).then(
        () => {
          notificationHub.add({
            type: 'success',
            msg: t('CRFTree.success_items', {
              count: payload.length,
              name: props.itemToLink.name,
            }),
          })
          emit('close')
        },
        () => {
          formRef.value.working = false
        }
      )
  }
}

const addItem = (item) => {
  if (!chosenItems.value.some((el) => el.uid === item.uid)) {
    chosenItems.value.push(item)
  }
}

const checkIfLinked = (item) => {
  return chosenItems.value.some((el) => el.uid === item.uid)
}

const removeItem = (item) => {
  chosenItems.value = chosenItems.value.filter((el) => el.uid !== item.uid)
}

const close = () => {
  chosenItems.value = []
  items.value = []
  emit('close')
}

const initForm = () => {
  if (!props.itemToLink) {
    return
  }
  chosenItems.value = Array.from(
    new Set(
      props.itemToLink.forms ||
        props.itemToLink.item_groups ||
        props.itemToLink.items
    )
  )
  getItems()
}

const getItems = (filters, options, filtersUpdated) => {
  if (props.itemsType) {
    const localFilters = filters ? JSON.parse(filters) : {}

    if (props.itemsType === 'items') {
      localFilters['odm_item_group'] = { v: [], op: 'eq' }
      if (props.itemToLink?.uid) {
        localFilters['odm_item_group.uid'] = {
          v: [props.itemToLink.uid],
          op: 'eq',
        }
      }
    }

    const parameters = filteringParameters.prepareParameters(
      options,
      localFilters,
      filtersUpdated
    )

    parameters['operator'] = 'or'

    if (props.itemToLink?.library_name) {
      parameters['library_name'] = props.itemToLink.library_name
    }

    crfs.get(props.itemsType, { params: parameters }).then((resp) => {
      items.value = resp.data.items
      total.value = resp.data.total
    })
  }
}
</script>
<style scoped>
.rightButtons {
  float: right;
}
</style>
