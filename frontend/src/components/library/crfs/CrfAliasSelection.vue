<template>
  <div id="alias-container">
    <v-row>
      <v-col>
        <div class="text-headline-medium mb-4">
          {{ $t('CRFAliases.add') }}
        </div>
      </v-col>
    </v-row>

    <v-row>
      <v-col>
        <v-text-field
          v-model="inputAlias.context"
          :label="$t('CRFAliases.context')"
          data-cy="alias-context"
          :readonly="props.readOnly"
        />
      </v-col>
      <v-col>
        <v-text-field
          v-model="inputAlias.name"
          :label="$t('CRFAliases.name')"
          data-cy="alias-name"
          :readonly="props.readOnly"
        />
      </v-col>
      <v-col>
        <v-btn
          color="secondary"
          class="mr-2"
          data-cy="alias-add-button"
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
          {{ $t('CRFAliases.select') }}
        </div>
      </v-col>
    </v-row>

    <v-row>
      <v-col>
        <NNTable
          ref="table"
          v-model="modelValue"
          table-id="crf-alias-selection"
          :headers="headers"
          :items="aliases"
          hide-default-switches
          hide-export-button
          :show-select="!readOnly"
          :hide-default-footer="props.readOnly"
          :hide-search-field="props.readOnly"
          :items-length="total"
          disable-filtering
          column-data-resource="concepts/odm-metadata/aliases"
          @filter="getAliases"
        >
          <template #[`afterSearch`]>
            <v-checkbox
              v-model="operator"
              data-cy="exact-match"
              :label="t('CRFTranslatedTexts.exact_match')"
              class="ms-5 mt-5"
            />
          </template>
          <template #[`item.actions`]="{ item }">
            <v-btn
              icon="mdi-pencil"
              data-cy="edit-item"
              variant="flat"
              :disabled="props.readOnly"
              @click.stop="edit(item)"
            />
          </template>
        </NNTable>
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { ref, computed, inject, onMounted, watch } from 'vue'
import filteringParameters from '@/utils/filteringParameters'
import NNTable from '@/components/tools/NNTable.vue'
import crfs from '@/api/crfs'

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
  { title: t('CRFAliases.context'), key: 'context' },
  { title: t('CRFAliases.name'), key: 'name' },
])

const inputAlias = ref({
  context: '',
  name: '',
})

const table = ref(false)
const operator = ref(false)

watch(operator, () => {
  table.value.filterTable()
})

const aliases = ref([])
const total = ref(0)

onMounted(() => {
  getAliases()
})

const getAliases = (filters, options, filtersUpdated) => {
  if (props.readOnly) {
    aliases.value = [...modelValue.value]
  } else {
    const params = filteringParameters.prepareParameters(
      options,
      null,
      filtersUpdated
    )
    params.search = options.search
    params.op = operator.value ? 'eq' : 'co'
    params.fields = 'context,name'
    crfs.getAliases(params).then((resp) => {
      aliases.value = [
        ...modelValue.value,
        ...resp.data.items.filter((alias) => {
          return !modelValue.value.some(
            (a) => a.context === alias.context && a.name === alias.name
          )
        }),
      ]
      total.value = resp.data.total
    })
  }
}

const add = () => {
  if (inputAlias.value.name && inputAlias.value.context) {
    const alias = {
      context: inputAlias.value.context,
      name: inputAlias.value.name,
    }

    const isDuplicate = aliases.value.some(
      (a) => a.context === alias.context && a.name === alias.name
    )

    if (!isDuplicate) {
      aliases.value.push({ ...alias })
    }

    modelValue.value.push({ ...alias })
    inputAlias.value = {}
  }
}

const edit = (item) => {
  inputAlias.value = { ...item }
  modelValue.value = modelValue.value.filter(
    (tt) => !(tt.context === item.context && tt.name === item.name)
  )

  notificationHub.add({
    msg: t('CRFAliases.editing_alias'),
    type: 'info',
  })

  document
    .getElementById('alias-container')
    .scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>
