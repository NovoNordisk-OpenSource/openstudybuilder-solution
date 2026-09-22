<template>
  <ConfirmDialog
    ref="confirm"
    :text-cols="6"
    :action-cols="5"
    :agree-disabled="loading"
  >
    <template #body>
      <v-skeleton-loader v-if="loading" type="paragraph"></v-skeleton-loader>
      <div v-else-if="hasSummary">
        <v-row>
          <v-col v-if="affectedCrfs.forms.length !== 0"
            ><strong>{{ t('CRFTree.forms') }}</strong></v-col
          >
          <v-col v-if="affectedCrfs.itemGroups.length !== 0"
            ><strong>{{ t('CRFTree.item_groups') }}</strong></v-col
          >
          <v-col v-if="affectedCrfs.items.length !== 0"
            ><strong>{{ t('CRFTree.items') }}</strong></v-col
          >
        </v-row>
        <v-row>
          <v-col v-if="affectedCrfs.forms.length !== 0">
            <div
              v-for="form in affectedCrfs.forms"
              :key="form.uid"
              class="mb-4"
            >
              <v-tooltip
                location="top"
                max-width="300"
                :text="`${form.oid}: ${form.name}`"
                :attach="true"
                interactive
              >
                <template #activator="{ props }">
                  <span v-bind="props">
                    {{ form.name.substring(0, 25)
                    }}<span v-if="form.name.length > 25">...</span>
                    {{ getNextFinalVersion(form.version) }}
                  </span>
                </template>
              </v-tooltip>
            </div>
          </v-col>
          <v-col v-if="affectedCrfs.itemGroups.length !== 0">
            <div
              v-for="itemGroup in affectedCrfs.itemGroups"
              :key="itemGroup.uid"
              class="mb-4"
            >
              <v-tooltip
                location="top"
                max-width="300"
                :text="`${itemGroup.oid}: ${itemGroup.name}`"
                :attach="true"
                interactive
              >
                <template #activator="{ props }">
                  <span v-bind="props">
                    {{ itemGroup.name.substring(0, 25)
                    }}<span v-if="itemGroup.name.length > 25">...</span>
                    {{ getNextFinalVersion(itemGroup.version) }}
                  </span>
                </template>
              </v-tooltip>
            </div>
          </v-col>
          <v-col v-if="affectedCrfs.items.length !== 0">
            <div
              v-for="item in affectedCrfs.items"
              :key="item.uid"
              class="mb-4"
            >
              <v-tooltip
                location="top"
                max-width="300"
                :text="`${item.oid}: ${item.name}`"
                :attach="true"
                interactive
              >
                <template #activator="{ props }">
                  <span v-bind="props">
                    {{ item.name.substring(0, 25)
                    }}<span v-if="item.name.length > 25">...</span>
                    {{ getNextFinalVersion(item.version) }}
                  </span>
                </template>
              </v-tooltip>
            </div>
          </v-col>
        </v-row>
      </div>
      <div v-else>
        {{ $t('_global.children_unaffected') }}
      </div>
    </template>
  </ConfirmDialog>
</template>

<script setup>
import { useI18n } from 'vue-i18n'
import { computed, ref } from 'vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import crfs from '@/api/crfs'
import statuses from '@/constants/statuses'

const { t } = useI18n()

const collection = ref(null)
const form = ref(null)
const itemGroup = ref(null)

const affectedCrfs = ref({
  forms: [],
  itemGroups: [],
  items: [],
})
const loading = ref(false)
const confirm = ref()

const getNextFinalVersion = (version) => {
  if (!version || typeof version !== 'string') return ''

  const major = parseInt(version.split('.')[0], 10)
  const nextVersion = [major + 1, 0].join('.')

  return ` (${version} → ${nextVersion})`
}

const hasSummary = computed(() => {
  return (
    affectedCrfs.value.forms.length > 0 ||
    affectedCrfs.value.itemGroups.length > 0 ||
    affectedCrfs.value.items.length > 0
  )
})

const open = async (extraOptions) => {
  collection.value = extraOptions.collection
  delete extraOptions.collection

  form.value = extraOptions.form
  delete extraOptions.form

  itemGroup.value = extraOptions.itemGroup
  delete extraOptions.itemGroup

  loading.value = true

  extraOptions = {
    ...{
      type: 'warning',
      title: t('_global.approval_affecting_children_warning'),
      cancelLabel: t('_global.cancel'),
      width: 750,
    },
    ...extraOptions,
  }

  return await confirm.value.open('N/A', extraOptions, () => {
    retrieveData().then(() => {
      loading.value = false
    })
  })
}

const retrieveData = async () => {
  const fetchEntities = async (endpoint, parents, childKey) => {
    const uids = parents
      .map((parent) => (parent[childKey] || []).map((child) => child.uid))
      .flat()

    if (!uids.length) return []

    const resp = await crfs.get(endpoint, {
      params: {
        filters: JSON.stringify({ uid: { v: uids } }),
        page_size: 0,
      },
    })

    return resp.data.items || []
  }

  let forms = []
  let itemGroups = []
  let items = []
  if (collection.value) {
    forms = await fetchEntities('forms', [collection.value], 'forms')
    itemGroups = await fetchEntities('item-groups', forms, 'item_groups')
    items = await fetchEntities('items', itemGroups, 'items')
  } else if (form.value) {
    itemGroups = await fetchEntities('item-groups', [form.value], 'item_groups')
    items = await fetchEntities('items', itemGroups, 'items')
  } else if (itemGroup.value) {
    items = await fetchEntities('items', [itemGroup.value], 'items')
  }

  affectedCrfs.value.forms = (forms || []).filter(
    (f) => f.status === statuses.DRAFT
  )
  affectedCrfs.value.itemGroups = (itemGroups || []).filter(
    (ig) => ig.status === statuses.DRAFT
  )
  affectedCrfs.value.items = (items || []).filter(
    (i) => i.status === statuses.DRAFT
  )
}

defineExpose({
  open,
})
</script>
