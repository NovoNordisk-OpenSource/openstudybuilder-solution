<template>
  <div>
    <BaseActivityOverview
      ref="overview"
      :source="'activity-groups'"
      :item-uid="itemUid"
      :transform-func="transformItem"
      :navigate-to-version="changeVersion"
      :history-headers="historyHeaders"
      :yaml-version="props.yamlVersion"
      :cosmos-version="props.cosmosVersion"
      v-bind="$attrs"
    >
      <template #htmlContent>
        <!-- Group Details -->
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.name') }}
          </v-col>
          <v-col cols="10">
            {{ itemOverview.group.name }}
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.sentence_case_name') }}
          </v-col>
          <v-col cols="10">
            <template v-if="itemOverview.group.name_sentence_case">
              {{ itemOverview.group.name_sentence_case }}
            </template>
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.version') }}
          </v-col>
          <v-col cols="2">
            <v-select
              :items="allVersions(itemOverview)"
              :model-value="itemOverview.group.version"
              @update:model-value="
                (value) => changeVersion(itemOverview.group, value)
              "
            ></v-select>
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.status') }}
          </v-col>
          <v-col cols="2">
            <StatusChip :status="itemOverview.group.status" />
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.start_date') }}
          </v-col>
          <v-col cols="2">
            <template v-if="itemOverview.group.start_date">
              {{ $filters.date(itemOverview.group.start_date) }}
            </template>
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.end_date') }}
          </v-col>
          <v-col cols="2">
            <template v-if="itemOverview.group.end_date">
              {{ $filters.date(itemOverview.group.end_date) }}
            </template>
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.library') }}
          </v-col>
          <v-col cols="10">
            <template v-if="itemOverview.group.library_name">
              {{ itemOverview.group.library_name }}
            </template>
          </v-col>
        </v-row>

        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.author') }}
          </v-col>
          <v-col cols="10">
            {{ itemOverview.group.author_username }}
          </v-col>
        </v-row>

        <v-row v-if="itemOverview.group.definition">
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.definition') }}
          </v-col>
          <v-col cols="10">
            {{ itemOverview.group.definition }}
          </v-col>
        </v-row>

        <!-- Subgroups List -->
        <v-row v-if="itemOverview.subgroups && itemOverview.subgroups.length">
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityOverview.activity_subgroups') }}
          </v-col>
          <v-col cols="10">
            <v-table>
              <thead>
                <tr>
                  <th>{{ $t('_global.name') }}</th>
                  <th>{{ $t('_global.definition') }}</th>
                  <th>{{ $t('_global.version') }}</th>
                  <th>{{ $t('_global.status') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="subgroup in itemOverview.subgroups"
                  :key="subgroup.uid"
                >
                  <td>
                    <router-link
                      :to="{
                        name: 'SubgroupOverview',
                        params: { id: subgroup.uid, version: subgroup.version },
                      }"
                    >
                      {{ subgroup.name }}
                    </router-link>
                  </td>
                  <td>{{ subgroup.definition }}</td>
                  <td>{{ subgroup.version }}</td>
                  <td>
                    <StatusChip :status="subgroup.status" />
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
            :subgroup="false"
            :edited-group-or-subgroup="item"
            @close="close"
          />
        </v-dialog>
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
import { defineAsyncComponent } from 'vue'

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

function allVersions(item) {
  return [...item.all_versions].sort().reverse()
}

async function changeVersion(group, version) {
  await router.push({
    name: 'GroupOverview',
    params: { id: group.uid, version },
  })
  emit('refresh')
}

function transformItem(item) {
  item.item_key = item.uid
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
    t('Sidebar.library.activities_groups'),
    { name: 'Activities' },
    3,
    true
  )

  const groupName = props.itemOverview?.group?.name || t('_global.loading')

  appStore.addBreadcrumbsLevel(
    groupName,
    {
      name: 'GroupOverview',
      params: { id: route.params.id },
    },
    4,
    true
  )
})
</script>
