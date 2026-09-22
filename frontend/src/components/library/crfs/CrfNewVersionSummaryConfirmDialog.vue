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
          <v-col v-if="affectedCrfs.itemGroups.length !== 0"
            ><strong>{{ t('CRFTree.item_groups') }}</strong></v-col
          >
          <v-col v-if="affectedCrfs.forms.length !== 0"
            ><strong>{{ t('CRFTree.forms') }}</strong></v-col
          >
          <v-col v-if="affectedCrfs.collections.length !== 0"
            ><strong>{{ t('CRFTree.collections') }}</strong></v-col
          >
        </v-row>
        <v-row>
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
                  </span>
                </template>
              </v-tooltip>
            </div>
          </v-col>
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
                  </span>
                </template>
              </v-tooltip>
            </div>
          </v-col>
          <v-col v-if="affectedCrfs.collections.length !== 0">
            <div
              v-for="collection in affectedCrfs.collections"
              :key="collection.uid"
              class="mb-4"
            >
              <v-tooltip
                location="top"
                max-width="300"
                :text="`${collection.oid}: ${collection.name}`"
                :attach="true"
                interactive
              >
                <template #activator="{ props }">
                  <span v-bind="props">
                    {{ collection.name.substring(0, 25)
                    }}<span v-if="collection.name.length > 25">...</span>
                  </span>
                </template>
              </v-tooltip>
            </div>
          </v-col>
        </v-row>
      </div>
      <div v-else>
        {{ $t('_global.parents_unaffected') }}
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

const form = ref(null)
const itemGroup = ref(null)
const item = ref(null)

const affectedCrfs = ref({
  collections: [],
  forms: [],
  itemGroups: [],
})
const loading = ref(false)
const confirm = ref()

const hasSummary = computed(() => {
  return (
    affectedCrfs.value.collections.length > 0 ||
    affectedCrfs.value.forms.length > 0 ||
    affectedCrfs.value.itemGroups.length > 0
  )
})

const open = async (extraOptions) => {
  form.value = extraOptions.form
  delete extraOptions.form

  itemGroup.value = extraOptions.itemGroup
  delete extraOptions.itemGroup

  item.value = extraOptions.item
  delete extraOptions.item

  loading.value = true

  extraOptions = {
    ...{
      type: 'warning',
      title: t('_global.new_version_affecting_parents_warning'),
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
  const fetchEntities = async (endpoint, targetUids, childKey) => {
    if (targetUids.length === 0) {
      return []
    }

    const resp = await crfs.get(endpoint, {
      params: {
        filters: JSON.stringify({
          [childKey]: { v: targetUids },
          status: { v: [statuses.DRAFT] },
        }),
        page_size: 0,
      },
    })

    return resp.data.items || []
  }

  let collections = []
  let forms = []
  let itemGroups = []
  if (item.value) {
    itemGroups = await fetchEntities(
      'item-groups',
      [item.value.uid],
      'items.uid'
    )
    forms = await fetchEntities(
      'forms',
      itemGroups.map((ig) => ig.uid),
      'item_groups.uid'
    )
    collections = await fetchEntities(
      'study-events',
      forms.map((f) => f.uid),
      'forms.uid'
    )
  } else if (itemGroup.value) {
    forms = await fetchEntities(
      'forms',
      [itemGroup.value.uid],
      'item_groups.uid'
    )
    collections = await fetchEntities(
      'study-events',
      forms.map((f) => f.uid),
      'forms.uid'
    )
  } else if (form.value) {
    collections = await fetchEntities(
      'study-events',
      [form.value.uid],
      'forms.uid'
    )
  }

  affectedCrfs.value.collections = collections || []
  affectedCrfs.value.forms = forms || []
  affectedCrfs.value.itemGroups = itemGroups || []
}

defineExpose({
  open,
})
</script>
