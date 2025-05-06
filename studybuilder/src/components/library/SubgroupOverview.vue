<template>
  <div>
    <BaseActivityOverview
      ref="overview"
      :source="'activity-sub-groups'"
      :item-uid="props.itemUid"
      :transform-func="transformItem"
      :navigate-to-version="changeVersion"
      :history-headers="historyHeaders"
      :yaml-version="props.yamlVersion"
      :cosmos-version="props.cosmosVersion"
      v-bind="$attrs"
    >
      <template #htmlContent>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.name') }}
          </v-col>
          <v-col cols="10">
            {{ props.itemOverview.activity_subgroup.name }}
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.sentence_case_name') }}
          </v-col>
          <v-col cols="10">
            <template
              v-if="props.itemOverview.activity_subgroup.name_sentence_case"
            >
              {{ props.itemOverview.activity_subgroup.name_sentence_case }}
            </template>
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.version') }}
          </v-col>
          <v-col cols="2">
            <v-select
              :items="allVersions(props.itemOverview)"
              :model-value="props.itemOverview.activity_subgroup.version"
              @update:model-value="
                (value) =>
                  changeVersion(props.itemOverview.activity_subgroup, value)
              "
            ></v-select>
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.status') }}
          </v-col>
          <v-col cols="2">
            <StatusChip :status="props.itemOverview.activity_subgroup.status" />
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.start_date') }}
          </v-col>
          <v-col cols="2">
            <template v-if="props.itemOverview.activity_subgroup.start_date">
              {{
                $filters.date(props.itemOverview.activity_subgroup.start_date)
              }}
            </template>
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.end_date') }}
          </v-col>
          <v-col cols="2">
            <template v-if="props.itemOverview.activity_subgroup.end_date">
              {{ $filters.date(props.itemOverview.activity_subgroup.end_date) }}
            </template>
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.library') }}
          </v-col>
          <v-col cols="10">
            <template v-if="props.itemOverview.activity_subgroup.library_name">
              {{ props.itemOverview.activity_subgroup.library_name }}
            </template>
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.author') }}
          </v-col>
          <v-col cols="10">
            {{ props.itemOverview.activity_subgroup.author_username }}
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.definition') }}
          </v-col>
          <v-col cols="10">
            <template v-if="props.itemOverview.activity_subgroup.definition">
              {{ props.itemOverview.activity_subgroup.definition }}
            </template>
          </v-col>
        </v-row>

        <!-- Activity Groups List -->
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityOverview.activity_group') }}
          </v-col>
          <v-col cols="10">
            <v-table>
              <thead>
                <tr>
                  <th width="70%">{{ $t('_global.name') }}</th>
                  <th width="15%">{{ $t('_global.version') }}</th>
                  <th width="15%">{{ $t('_global.status') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="group in props.itemOverview.activity_subgroup
                    .activity_groups"
                  :key="group.uid"
                >
                  <td>
                    <router-link
                      :to="{
                        name: 'GroupOverview',
                        params: { id: group.uid, version: group.version },
                      }"
                    >
                      {{ group.name }}
                    </router-link>
                  </td>
                  <td>{{ group.version }}</td>
                  <td>
                    <StatusChip :status="group.status" />
                  </td>
                </tr>
              </tbody>
            </v-table>
          </v-col>
        </v-row>

        <!-- Activities List -->
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityOverview.activities') }}
          </v-col>
          <v-col cols="10">
            <v-table>
              <thead>
                <tr>
                  <th width="70%">{{ $t('_global.name') }}</th>
                  <th width="15%">{{ $t('_global.version') }}</th>
                  <th width="15%">{{ $t('_global.status') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="activity in props.itemOverview.activities"
                  :key="activity.uid"
                >
                  <td>
                    <router-link
                      :to="{
                        name: 'ActivityOverview',
                        params: { id: activity.uid },
                      }"
                    >
                      {{ activity.name }}
                    </router-link>
                  </td>
                  <td>{{ activity.version }}</td>
                  <td>
                    <StatusChip :status="activity.status" />
                  </td>
                </tr>
              </tbody>
            </v-table>
          </v-col>
        </v-row>
      </template>

      <template #itemForm="{ show, item, close }">
        <v-dialog
          :model-value="show"
          persistent
          max-width="800px"
          content-class="top-dialog"
        >
          <ActivitiesGroupsForm
            ref="groupFormRef"
            :open="show"
            :subgroup="true"
            :edited-group-or-subgroup="item"
            @close="close"
          />
        </v-dialog>
      </template>
    </BaseActivityOverview>
  </div>
</template>

<script setup>
import { onMounted, ref, defineAsyncComponent } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/stores/app'

import BaseActivityOverview from './BaseActivityOverview.vue'
import StatusChip from '@/components/tools/StatusChip.vue'

const ActivitiesGroupsForm = defineAsyncComponent(
  () => import('@/components/library/ActivitiesGroupsForm.vue')
)

const props = defineProps({
  itemOverview: {
    type: Object,
    required: true,
  },
  itemUid: {
    type: String,
    required: true,
  },
  yamlVersion: {
    type: String,
    default: null,
  },
  cosmosVersion: {
    type: String,
    default: null,
  },
})
const emit = defineEmits(['refresh'])

const { t } = useI18n()
const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const overview = ref()
const groupFormRef = ref()

const historyHeaders = [
  { title: t('_global.library'), key: 'library_name' },
  { title: t('_global.name'), key: 'name' },
  { title: t('_global.definition'), key: 'definition' },
  { title: t('_global.version'), key: 'version' },
  { title: t('_global.start_date'), key: 'start_date' },
  { title: t('_global.end_date'), key: 'end_date' },
  { title: t('_global.status'), key: 'status' },
]

function transformItem(item) {
  item.item_key = item.uid
}

async function changeVersion(subgroup, version) {
  await router.push({
    name: 'SubgroupOverview',
    params: {
      id: subgroup.uid,
      version,
    },
  })
  emit('refresh')
}

function allVersions(item) {
  return [...item.all_versions].sort().reverse()
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
    t('Sidebar.library.activities_subgroups'),
    { name: 'Activities' },
    3,
    true
  )

  const subgroupName =
    props.itemOverview?.activity_subgroup?.name || t('_global.loading')

  appStore.addBreadcrumbsLevel(
    subgroupName,
    {
      name: 'SubgroupOverview',
      params: { id: route.params.id },
    },
    4,
    true
  )
})
</script>
