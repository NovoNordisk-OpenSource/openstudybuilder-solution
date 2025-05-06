<template>
  <div>
    <BaseActivityOverview
      ref="overview"
      :transform-func="transformItem"
      :navigate-to-version="changeVersion"
      :history-headers="historyHeaders"
      v-bind="$attrs"
    >
      <template #htmlContent="{ itemOverview, item }">
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.name') }}
          </v-col>
          <v-col cols="10">
            {{ itemOverview.activity.name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.sentence_case_name') }}
          </v-col>
          <v-col cols="10">
            {{ itemOverview.activity.name_sentence_case }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.version') }}
          </v-col>
          <v-col cols="2">
            <v-select
              :items="allVersions(itemOverview)"
              :value="itemOverview.activity.version"
              @update:model-value="
                (value) => changeVersion(itemOverview.activity, value)
              "
            ></v-select>
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.status') }}
          </v-col>
          <v-col cols="2">
            <StatusChip v-if="item" :status="itemOverview.activity.status" />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.start_date') }}
          </v-col>
          <v-col cols="2">
            {{
              itemOverview.activity.start_date
                ? $filters.date(itemOverview.activity.start_date)
                : $t('_global.date_null')
            }}
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.end_date') }}
          </v-col>
          <v-col cols="2">
            {{
              itemOverview.activity.end_date
                ? $filters.date(itemOverview.activity.end_date)
                : $t('_global.date_null')
            }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.definition') }}
          </v-col>
          <v-col cols="10">
            {{ itemOverview.activity.definition }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.abbreviation') }}
          </v-col>
          <v-col cols="10">
            {{ itemOverview.activity.abbreviation }}
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.library') }}
          </v-col>
          <v-col cols="10">
            {{ itemOverview.activity.library_name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityForms.nci_concept_id') }}
          </v-col>
          <v-col cols="10">
            <NCIConceptLink
              :concept-id="itemOverview.activity.nci_concept_id"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityForms.nci_concept_name') }}
          </v-col>
          <v-col cols="10">
            {{ itemOverview.activity.nci_concept_name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityForms.synonyms') }}
          </v-col>
          <v-col cols="10">
            <v-chip
              v-for="synonym in itemOverview.activity.synonyms"
              :key="synonym"
            >
              {{ synonym }}
            </v-chip>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityOverview.is_data_collected') }}
          </v-col>
          <v-col cols="10">
            {{ $filters.yesno(itemOverview.activity.is_data_collected) }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityOverview.activity_groupings') }}
          </v-col>
          <v-col cols="10">
            <v-table>
              <thead>
                <tr class="text-left">
                  <th scope="col">
                    {{ $t('ActivityOverview.activity_group') }}
                  </th>
                  <th scope="col">
                    {{ $t('ActivityOverview.activity_subgroup') }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(grouping, index) in itemOverview.activity_groupings"
                  :key="`grouping-${index}`"
                >
                  <td>
                    <router-link
                      :to="{
                        name: 'GroupOverview',
                        params: {
                          id: grouping.activity_group.uid,
                        },
                      }"
                    >
                      {{ grouping.activity_group.name }}
                    </router-link>
                  </td>
                  <td>
                    <router-link
                      :to="{
                        name: 'SubgroupOverview',
                        params: {
                          id: grouping.activity_subgroup.uid,
                        },
                      }"
                    >
                      {{ grouping.activity_subgroup.name }}
                    </router-link>
                  </td>
                </tr>
              </tbody>
            </v-table>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityOverview.instances') }}
          </v-col>
          <v-col cols="10">
            <v-table>
              <thead>
                <tr class="text-left">
                  <th scope="col">
                    {{ $t('_global.name') }}
                  </th>
                  <th scope="col">
                    {{ $t('_global.definition') }}
                  </th>
                  <th scope="col">
                    {{ $t('_global.version') }}
                  </th>
                  <th scope="col">
                    {{ $t('_global.status') }}
                  </th>
                  <th scope="col">
                    {{ $t('ActivityOverview.class') }}
                  </th>
                  <th scope="col">
                    {{ $t('ActivityOverview.topic_code') }}
                  </th>
                  <th scope="col">
                    {{ $t('ActivityOverview.adam_code') }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(
                    activityItem, index
                  ) in itemOverview.activity_instances"
                  :key="`item-${index}`"
                >
                  <td>
                    <router-link
                      :to="{
                        name: 'ActivityInstanceOverview',
                        params: {
                          id: activityItem.uid,
                          version: activityItem.version,
                        },
                      }"
                    >
                      {{ activityItem.name }}
                    </router-link>
                  </td>
                  <td>{{ activityItem.definition }}</td>
                  <td>{{ activityItem.version }}</td>
                  <td>{{ activityItem.status }}</td>
                  <td>{{ activityItem.activity_instance_class.name }}</td>
                  <td>{{ activityItem.topic_code }}</td>
                  <td>{{ activityItem.adam_param_code }}</td>
                </tr>
              </tbody>
            </v-table>
          </v-col>
        </v-row>
      </template>
      <template #itemForm="{ show, item, close }">
        <ActivitiesForm :open="show" :edited-activity="item" @close="close" />
      </template>
    </BaseActivityOverview>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'
import BaseActivityOverview from './BaseActivityOverview.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import NCIConceptLink from '@/components/tools/NCIConceptLink.vue'
import { defineAsyncComponent } from 'vue'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const overview = ref()

const emit = defineEmits(['refresh'])
const ActivitiesForm = defineAsyncComponent(
  () => import('@/components/library/ActivitiesForm.vue')
)

const historyHeaders = [
  { title: t('_global.library'), key: 'library_name' },
  {
    title: t('ActivityTable.activity_group'),
    key: 'activity_group.name',
    externalFilterSource: 'concepts/activities/activity-groups$name',
    width: '15%',
    exludeFromHeader: ['is_data_collected'],
  },
  {
    title: t('ActivityTable.activity_subgroup'),
    key: 'activity_subgroup.name',
    externalFilterSource: 'concepts/activities/activity-sub-groups$name',
    width: '15%',
    exludeFromHeader: ['is_data_collected'],
  },
  {
    title: t('ActivityTable.activity_name'),
    key: 'name',
    externalFilterSource: 'concepts/activities/activities$name',
  },
  {
    title: t('ActivityTable.sentence_case_name'),
    key: 'name_sentence_case',
  },
  {
    title: t('ActivityTable.synonyms'),
    key: 'synonyms',
  },
  { title: t('ActivityTable.abbreviation'), key: 'abbreviation' },
  {
    title: t('ActivityTable.is_data_collected'),
    key: 'is_data_collected',
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.status'), key: 'status' },
  { title: t('_global.version'), key: 'version' },
]

function allVersions(item) {
  return [...item.all_versions].sort().reverse()
}

async function changeVersion(activity, version) {
  await router.push({
    name: 'ActivityOverview',
    params: { id: activity.uid, version },
  })
  emit('refresh')
}

function transformItem(item) {
  if (item.activity_groupings.length > 0) {
    const groups = []
    const subgroups = []
    for (const grouping of item.activity_groupings) {
      groups.push(grouping.activity_group_name)
      subgroups.push(grouping.activity_subgroup_name)
    }
    item.activity_group = { name: groups }
    item.activity_subgroup = { name: subgroups }
    item.item_key = item.uid
  } else {
    item.activity_group = { name: [] }
    item.activity_subgroup = { name: [] }
    item.item_key = item.uid
  }
}

onMounted(() => {
  appStore.addBreadcrumbsLevel(
    t('Sidebar.library.concepts'),
    { name: 'Activities' },
    1,
    false
  )

  appStore.addBreadcrumbsLevel(
    t('Sidebar.library.activities'),
    { name: 'Activities' },
    2,
    true
  )

  appStore.addBreadcrumbsLevel(
    t('Sidebar.library.activities'),
    { name: 'Activities' },
    3,
    true
  )

  const activityName =
    overview.value?.itemOverview?.activity?.name || t('_global.loading')

  appStore.addBreadcrumbsLevel(
    activityName,
    {
      name: 'ActivityOverview',
      params: { id: route.params.id },
    },
    4,
    true
  )
})
</script>
