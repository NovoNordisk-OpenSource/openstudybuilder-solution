<template>
  <SimpleFormDialog
    ref="formRef"
    :title="$t('ActivityInstancePicker.title')"
    :open="open"
    max-width="1440px"
    :action-label="$t('ActivityInstancePicker.add_selected')"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-alert type="info" variant="tonal" class="mb-4">
        {{ $t('ActivityInstancePicker.description') }}
      </v-alert>

      <v-text-field
        v-model="search"
        :label="$t('_global.search')"
        prepend-inner-icon="mdi-magnify"
        clearable
        variant="outlined"
        density="compact"
        class="mb-2"
        @update:model-value="debouncedFetch"
      />

      <v-data-table
        v-model="selected"
        :headers="headers"
        :items="instances"
        :loading="loading"
        item-value="uid"
        show-select
        density="compact"
        :items-per-page="25"
        :items-per-page-options="[10, 25, 50]"
      >
        <template #[`item.name`]="{ item }">
          <span class="font-weight-medium">{{ item.name }}</span>
        </template>
        <template #[`item.status`]="{ item }">
          <v-chip
            size="small"
            :color="item.status === 'Final' ? 'success' : 'grey'"
            variant="flat"
            class="text-white"
          >
            {{ item.status }}
          </v-chip>
        </template>
        <template #[`item.activity_name`]="{ item }">
          <span class="text-medium-emphasis">{{
            item.activity_name || '—'
          }}</span>
        </template>
      </v-data-table>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import activitiesApi from '@/api/activities'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'

const { t } = useI18n()

const props = defineProps({
  open: Boolean,
  excludeUids: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['close', 'select'])

const formRef = ref()
const loading = ref(false)
const search = ref('')
const selected = ref([])
const allInstances = ref([])
let debounceTimer = null

const headers = computed(() => [
  {
    title: t('ActivityInstancePicker.instance_name'),
    key: 'name',
    sortable: true,
  },
  {
    title: t('ActivityInstancePicker.activity'),
    key: 'activity_name',
    sortable: true,
  },
  {
    title: t('ActivityInstancePicker.topic_code'),
    key: 'topic_code',
    sortable: false,
  },
  { title: t('ActivityInstancePicker.status'), key: 'status', sortable: false },
])

const instances = computed(() => {
  const excludeSet = new Set(props.excludeUids)
  return allInstances.value.filter((inst) => !excludeSet.has(inst.uid))
})

watch(
  () => props.open,
  (newVal) => {
    if (newVal) {
      selected.value = []
      search.value = ''
      fetchInstances()
    }
  }
)

function debouncedFetch() {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    fetchInstances()
  }, 300)
}

async function fetchInstances() {
  loading.value = true
  try {
    const params = {
      page_size: 0,
      filters: {
        status: { v: ['Final'] },
      },
    }
    if (search.value) {
      params.filters.name = { v: [search.value], op: 'co' }
    }
    const resp = await activitiesApi.get(params, 'activity-instances')
    allInstances.value = (resp.data.items || []).map((item) => ({
      uid: item.uid,
      name: item.name,
      topic_code: item.topic_code || '',
      status: item.status,
      activity_name: item.activity_groupings?.[0]?.activity?.name || '',
      activity_groupings: item.activity_groupings || [],
    }))
  } catch {
    allInstances.value = []
  } finally {
    loading.value = false
  }
}

function cancel() {
  selected.value = []
  emit('close')
}

function submit() {
  const selectedInstances = instances.value.filter((inst) =>
    selected.value.includes(inst.uid)
  )
  emit('select', selectedInstances)
  selected.value = []
  emit('close')
}
</script>
