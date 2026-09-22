<template>
  <div>
    <!-- Status filter tabs -->
    <div
      v-if="!requested && showStatusTabs"
      class="d-flex flex-column align-center mb-4 mt-4"
    >
      <v-btn-toggle
        v-model="selectedStatusTab"
        mandatory
        density="compact"
        color="nnBaseBlue"
        divided
        variant="outlined"
        class="layoutSelector"
        @update:model-value="onStatusTabChange"
      >
        <v-btn v-for="tab in statusTabs" :key="tab.value" :value="tab.value">
          {{ tab.label }}
        </v-btn>
      </v-btn-toggle>
      <v-progress-linear
        v-if="isStatusLoading"
        indeterminate
        color="nnBaseBlue"
        class="mt-2"
        style="width: 200px"
      />
    </div>

    <NNTable
      ref="tableRef"
      :key="`activities-table-${source}`"
      :headers="currentHeaders"
      :items="activities"
      :table-id="source"
      :hide-export-button="source === 'activities-by-grouping'"
      :hide-default-switches="source === 'activities-by-grouping'"
      item-value="item_key"
      :items-length="total"
      :show-filter-bar-by-default="
        ['activities'].includes(source) && !requested
      "
      :column-data-resource="`concepts/activities/${source}`"
      :sub-tables="isExpand()"
      :filters-modify-function="modifyFilters"
      :modifiable-table="!isExpand()"
      :disable-filtering="source === 'activities-by-grouping'"
      :hide-search-field="source === 'activities-by-grouping'"
      :initial-sort-by="[{ key: 'name', order: 'asc' }]"
      :history-config="{
        excludedHeaders: historyExcludedHeaders,
        dataFetcher:
          source !== 'activities-by-grouping' ? fetchGlobalAuditTrail : null,
        changeField: 'change_description',
        title: $t('_global.audit_trail'),
      }"
      :export-config="{
        objectLabel: 'Activities',
        dataUrl: `concepts/activities/${source}`,
      }"
      @filter="fetchActivities"
      @update:expanded="getSubGroups"
    >
      <template
        v-if="isExpand()"
        #item="{ item, internalItem, toggleExpand, isExpanded }"
      >
        <tr style="background-color: rgb(var(--v-theme-dfltBackgroundLight1))">
          <td width="40%" :class="'font-weight-bold'">
            <v-row class="align-center">
              <v-btn
                v-if="isExpanded(internalItem)"
                icon="mdi-chevron-down"
                variant="text"
                @click="toggleExpand(internalItem)"
              />
              <v-btn
                v-else
                icon="mdi-chevron-right"
                variant="text"
                @click="toggleExpand(internalItem)"
              />
              <span class="ml-2">
                {{ item.name }}
              </span>
            </v-row>
          </td>
          <td width="25%">
            {{ $filters.date(item.start_date) }}
          </td>
          <td width="15%">
            <StatusChip :status="item.status" />
          </td>
          <td width="20%">
            {{ item.version }}
          </td>
        </tr>
      </template>
      <template #[`item.actions`]="{ item }">
        <div class="pr-0 mr-0">
          <ActionsMenu
            :actions="currentActions"
            :item="item"
            :source="source"
          />
        </div>
      </template>
      <template #[`item.name`]="{ item }">
        <template v-if="source === 'activity-instances'">
          <router-link
            :to="{ name: 'ActivityInstanceOverview', params: { id: item.uid } }"
          >
            {{ item.name }}
          </router-link>
        </template>
        <template v-else-if="source === 'activities'">
          <router-link
            :to="{ name: 'ActivityOverview', params: { id: item.uid } }"
          >
            {{ item.name }}
          </router-link>
        </template>
        <template v-else-if="source === 'activity-sub-groups'">
          <template v-if="getActivitySubgroupUID(item)">
            <router-link
              :to="{
                name: 'SubgroupOverview',
                params: { id: getActivitySubgroupUID(item) },
              }"
            >
              <span v-html="sanitizeHTML(subGroupsDisplay(item))"></span>
            </router-link>
          </template>
          <template v-else>
            <span v-html="sanitizeHTML(subGroupsDisplay(item))"></span>
          </template>
        </template>
        <template v-else-if="source === 'activity-groups'">
          <template v-if="getActivityGroupUID(item)">
            <router-link
              :to="{
                name: 'GroupOverview',
                params: { id: getActivityGroupUID(item) },
              }"
            >
              <span v-html="sanitizeHTML(groupsDisplay(item))"></span>
            </router-link>
          </template>
          <template v-else>
            <span v-html="sanitizeHTML(groupsDisplay(item))"></span>
          </template>
        </template>
        <template v-else>
          <div :class="isExpand() ? 'font-weight-bold' : ''">
            {{ item.name }}
          </div>
        </template>
      </template>
      <template #[`item.nci_concept_id`]="{ item }">
        <NCIConceptLink :concept-id="item.nci_concept_id" />
      </template>
      <template #[`item.synonyms`]="{ item }">
        <div v-html="sanitizeHTML(synonymsDisplay(item.synonyms))" />
      </template>
      <template #[`item.definition`]="{ item }">
        {{ item.definition || '-' }}
      </template>
      <template #[`item.status`]="{ item }">
        <StatusChip :status="item.status" />
      </template>
      <template #[`item.start_date`]="{ item }">
        <v-tooltip location="top">
          <template #activator="{ props }">
            <span v-bind="props">{{
              $filters.dateRelative(item.start_date)
            }}</span>
          </template>
          {{ $filters.date(item.start_date) }}
        </v-tooltip>
      </template>
      <template #[`item.groupings_status`]="{ item }">
        <StatusChip
          v-if="item.groupings_status"
          :status="item.groupings_status"
        />
      </template>
      <template #[`item.groupings_start_date`]="{ item }">
        {{
          item.groupings_start_date
            ? $filters.date(item.groupings_start_date)
            : ''
        }}
      </template>
      <template #[`item.used_by_studies`]="{ item }">
        {{ item.used_by_studies.join(', ') }}
      </template>
      <template #[`item.activity_groups`]="{ item }">
        <div
          v-if="
            Array.isArray(item.activity_groups) && item.activity_groups.length
          "
        >
          <template v-if="item.activity_groups.length === 1">
            <router-link
              :to="{
                name: 'GroupOverview',
                params: { id: item.activity_groups[0].uid },
              }"
            >
              {{ item.activity_groups[0].name }}
            </router-link>
          </template>

          <template v-else>
            <div
              v-for="group in item.activity_groups"
              :key="group.uid"
              style="margin-bottom: 4px"
            >
              <span>&#9679; </span>
              <router-link
                :to="{ name: 'GroupOverview', params: { id: group.uid } }"
              >
                {{ group.name }}
              </router-link>
            </div>
          </template>
        </div>
      </template>
      <template #[`item.activity_group.name`]="{ item }">
        <div v-if="item.activity_group && item.activity_group.name">
          <div v-if="Array.isArray(item.activity_group.name)">
            <template v-if="item.activity_group.name.length === 1">
              <router-link
                v-if="
                  item.activity_group.name[0].uid ||
                  (item.activity_groupings &&
                    item.activity_groupings[0] &&
                    (item.activity_groupings[0].activity_group_uid ||
                      item.activity_groupings[0].activity_group?.uid))
                "
                :to="{
                  name: 'GroupOverview',
                  params: {
                    id:
                      item.activity_group.name[0].uid ||
                      item.activity_groupings?.[0]?.activity_group_uid ||
                      item.activity_groupings?.[0]?.activity_group?.uid,
                  },
                }"
              >
                {{
                  item.activity_group.name[0].name ||
                  item.activity_group.name[0]
                }}
              </router-link>
              <span v-else>{{
                item.activity_group.name[0].name || item.activity_group.name[0]
              }}</span>
            </template>
            <template v-else-if="item.activity_group.name.length > 1">
              <div
                v-for="(group, idx) in item.activity_group.name"
                :key="idx"
                style="margin-bottom: 4px"
              >
                <span>&#9679; </span>
                <router-link
                  v-if="
                    (item.activity_groupings &&
                      item.activity_groupings[idx] &&
                      item.activity_groupings[idx].activity_group_uid) ||
                    group.uid
                  "
                  :to="{
                    name: 'GroupOverview',
                    params: {
                      id:
                        group.uid ||
                        item.activity_groupings[idx]?.activity_group_uid,
                    },
                  }"
                >
                  {{ group.name || group }}
                </router-link>
                <span v-else>{{ group.name || group }}</span>
              </div>
            </template>
          </div>

          <div v-else>
            <span>{{ item.activity_group.name }}</span>
          </div>
        </div>
      </template>

      <template #[`item.activity_subgroup.name`]="{ item }">
        <div v-if="item.activity_subgroup && item.activity_subgroup.name">
          <div v-if="Array.isArray(item.activity_subgroup.name)">
            <template v-if="item.activity_subgroup.name.length === 1">
              <router-link
                v-if="
                  item.activity_subgroup.name[0].uid ||
                  (item.activity_groupings &&
                    item.activity_groupings[0] &&
                    (item.activity_groupings[0].activity_subgroup_uid ||
                      item.activity_groupings[0].activity_subgroup?.uid))
                "
                :to="{
                  name: 'SubgroupOverview',
                  params: {
                    id:
                      item.activity_subgroup.name[0].uid ||
                      item.activity_groupings?.[0]?.activity_subgroup_uid ||
                      item.activity_groupings?.[0]?.activity_subgroup?.uid,
                  },
                }"
              >
                {{
                  item.activity_subgroup.name[0].name ||
                  item.activity_subgroup.name[0]
                }}
              </router-link>
              <span v-else>{{
                item.activity_subgroup.name[0].name ||
                item.activity_subgroup.name[0]
              }}</span>
            </template>
            <template v-else-if="item.activity_subgroup.name.length > 1">
              <div
                v-for="(subgroup, idx) in item.activity_subgroup.name"
                :key="idx"
                style="margin-bottom: 4px"
              >
                <span>&#9679; </span>
                <router-link
                  v-if="
                    (item.activity_groupings &&
                      item.activity_groupings[idx] &&
                      item.activity_groupings[idx].activity_subgroup_uid) ||
                    subgroup.uid
                  "
                  :to="{
                    name: 'SubgroupOverview',
                    params: {
                      id:
                        subgroup.uid ||
                        item.activity_groupings[idx]?.activity_subgroup_uid,
                    },
                  }"
                >
                  {{ subgroup.name || subgroup }}
                </router-link>
                <span v-else>{{ subgroup.name || subgroup }}</span>
              </div>
            </template>
          </div>

          <div v-else>
            <span>{{ item.activity_subgroup.name }}</span>
          </div>
        </div>
      </template>
      <template #[`item.activity_name`]="{ item }">
        <template v-if="item.activities && item.activities.length > 0">
          <router-link
            :to="{
              name: 'ActivityOverview',
              params: { id: item.activities[0].uid },
            }"
          >
            {{ item.activity_name }}
          </router-link>
        </template>
        <template v-else>
          {{ item.activity_name }}
        </template>
      </template>
      <template #[`item.activities.name`]="{ item }">
        {{ activitiesDisplay(item) }}
      </template>
      <template #[`item.is_research_lab`]="{ item }">
        {{ $filters.yesno(item.is_research_lab) }}
      </template>
      <template #[`item.is_data_collected`]="{ item }">
        {{ $filters.yesno(item.is_data_collected) }}
      </template>
      <template #[`item.is_used_by_legacy_instances`]="{ item }">
        {{ $filters.yesno(item.is_used_by_legacy_instances) }}
      </template>
      <template #[`item.is_required_for_activity`]="{ item }">
        {{ $filters.yesno(item.is_required_for_activity) }}
      </template>
      <template #[`item.is_default_selected_for_activity`]="{ item }">
        {{ $filters.yesno(item.is_default_selected_for_activity) }}
      </template>
      <template #[`item.is_data_sharing`]="{ item }">
        {{ $filters.yesno(item.is_data_sharing) }}
      </template>
      <template #[`item.is_legacy_usage`]="{ item }">
        {{ $filters.yesno(item.is_legacy_usage) }}
      </template>
      <template #expanded-row="{ columns, item }">
        <tr>
          <td :colspan="columns.length" class="pa-0">
            <v-data-table
              class="elevation-0"
              :items="item.subgroups"
              item-value="uid"
              :return-object="true"
              :items-per-page="-1"
              :loading="item.subgroupsLoading"
              :show-expand="true"
              @update:expanded="getSubgroupActivities"
            >
              <template #headers />
              <template #bottom />
              <template
                #item="{ item, internalItem, toggleExpand, isExpanded }"
              >
                <tr
                  style="
                    background-color: rgb(var(--v-theme-dfltBackgroundLight2));
                  "
                >
                  <td width="40%" class="font-weight-bold">
                    <div class="ml-6">
                      <v-row class="align-center">
                        <v-btn
                          v-if="isExpanded(internalItem)"
                          icon="mdi-chevron-down"
                          variant="text"
                          @click="toggleExpand(internalItem)"
                        />
                        <v-btn
                          v-else
                          icon="mdi-chevron-right"
                          variant="text"
                          @click="toggleExpand(internalItem)"
                        />
                        {{ item.name }}
                      </v-row>
                    </div>
                  </td>
                  <td width="25%">
                    {{ $filters.date(item.start_date) }}
                  </td>
                  <td width="15%">
                    <StatusChip :status="item.status" />
                  </td>
                  <td width="20%">
                    {{ item.version }}
                  </td>
                </tr>
              </template>
              <template #expanded-row="{ columns, item }">
                <tr>
                  <td :colspan="columns.length" class="pa-0">
                    <v-data-table
                      class="elevation-0"
                      :items="item.activities"
                      item-value="item_key"
                      :items-per-page="-1"
                      :loading="item.activitiesLoading"
                      :show-expand="true"
                    >
                      <template #headers />
                      <template #bottom />
                      <template #item="{ item }">
                        <tr>
                          <td width="40%">
                            <div class="ml-12">
                              {{ item.name }}
                            </div>
                          </td>
                          <td width="25%">
                            {{ $filters.date(item.start_date) }}
                          </td>
                          <td width="15%">
                            <StatusChip :status="item.status" />
                          </td>
                          <td width="20%">
                            {{ item.version }}
                          </td>
                        </tr>
                      </template>
                    </v-data-table>
                  </td>
                </tr>
              </template>
            </v-data-table>
          </td>
        </tr>
      </template>
      <template #afterSwitches>
        <v-switch
          v-if="requested"
          v-model="showFinalised"
          :label="$t('ActivityTable.show_only_handled')"
          hide-details
          @update:model-value="tableRef.filterTable()"
        />
        <v-switch
          v-if="source === 'activities'"
          v-model="onlyArchivedLibrary"
          :label="$t('ActivityTable.archived_library')"
          hide-details
          @update:model-value="updateArchivedView()"
        />
      </template>
      <template #actions="">
        <slot name="extraActions" />
        <v-btn
          v-if="source !== 'activities-by-grouping' && !requested"
          class="ml-2"
          variant="outlined"
          color="nnBaseBlue"
          icon
          size="small"
          data-cy="add-activity"
          :disabled="!accessGuard.checkPermission($roles.LIBRARY_WRITE)"
          @click.stop="showForm"
        >
          <v-icon>mdi-plus</v-icon>
          <v-tooltip activator="parent" location="top">
            {{ itemCreationTitle }}
          </v-tooltip>
        </v-btn>
      </template>
    </NNTable>
    <ActivitiesForm
      v-if="source === 'activities' && !requested"
      :open="showActivityForm"
      :edited-activity="activeItem"
      @close="closeForm"
    />
    <ActivityInstanceLinkingForm
      v-if="source === 'activities'"
      :open="showInstanceLinkingForm"
      :activity="instanceLinkingActivity"
      @close="closeInstanceLinkingForm"
    />
    <RequestedActivitiesForm
      v-if="requested"
      :open="showRequestedActivityForm"
      :edited-activity="activeItem"
      @close="closeForm"
    />
    <v-dialog
      v-if="source === 'activity-groups' || source === 'activity-sub-groups'"
      :model-value="showGroupsForm"
      persistent
      max-width="800px"
      content-class="top-dialog"
    >
      <ActivitiesGroupsForm
        ref="groupFormRef"
        :open="showGroupsForm"
        :subgroup="!groupMode"
        :edited-group-or-subgroup="activeItem"
        @close="closeForm"
      />
    </v-dialog>
    <v-dialog
      v-if="source === 'activity-instances'"
      v-model="showInstantiationsForm"
      persistent
      fullscreen
      content-class="fullscreen-dialog"
    >
      <FeatureDisabledDialog
        v-if="
          (!instanceEditMode && !newWizardStepper) ||
          (instanceEditMode && !newWizardStepperEditMode)
        "
        @close="closeForm"
      />
      <Suspense v-else>
        <ActivityInstanceForm
          :activity-instance-uid="activeItem?.uid"
          :edit-mode="instanceEditMode"
          @close="closeForm"
        />
        <template #fallback>
          <v-skeleton-loader
            class="fullscreen-dialog"
            type="card"
          ></v-skeleton-loader>
        </template>
      </Suspense>
    </v-dialog>
    <v-dialog
      v-model="showSponsorFromRequestedForm"
      persistent
      max-width="1200px"
      content-class="top-dialog"
    >
      <ActivitiesCreateSponsorFromRequestedForm
        :edited-activity="activeItem"
        @close="closeForm"
      />
    </v-dialog>
    <v-dialog
      v-model="showHistory"
      persistent
      :fullscreen="$globals.historyDialogFullscreen"
      @keydown.esc="closeHistory"
    >
      <HistoryTable
        :title="itemHistoryTitle"
        :headers="currentHeaders"
        :items="historyItems"
        :items-total="historyItems.length"
        :excluded-headers="historyExcludedHeaders"
        @close="closeHistory"
      />
    </v-dialog>
  </div>
</template>

<script setup>
import activitiesApi from '@/api/activities'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import ActivitiesForm from '@/components/library/ActivitiesForm.vue'
import RequestedActivitiesForm from '@/components/library/RequestedActivitiesForm.vue'
import ActivitiesGroupsForm from '@/components/library/ActivitiesGroupsForm.vue'
import ActivityInstanceForm from '@/components/library/ActivityInstanceForm.vue'
import FeatureDisabledDialog from '@/components/tools/FeatureDisabledDialog.vue'
import ActivityInstanceLinkingForm from '@/components/library/ActivityInstanceLinkingForm.vue'
import ActivitiesCreateSponsorFromRequestedForm from '@/components/library/ActivitiesCreateSponsorFromRequestedForm.vue'
import libConstants from '@/constants/libraries'
import { useAccessGuard } from '@/composables/accessGuard'
import NCIConceptLink from '@/components/tools/NCIConceptLink.vue'
import filteringParameters from '@/utils/filteringParameters'
import statuses from '@/constants/statuses'
import _isEmpty from 'lodash/isEmpty'
import { useFeatureFlagsStore } from '@/stores/feature-flags'
import { computed, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { sanitizeHTML, escapeHTML } from '@/utils/sanitize'

const props = defineProps({
  source: {
    type: String,
    default: null,
  },
  requested: {
    type: Boolean,
    default: false,
  },
})

const { t } = useI18n()
const accessGuard = useAccessGuard()
const featureFlagsStore = useFeatureFlagsStore()
const notificationHub = inject('notificationHub')
const roles = inject('roles')
const tableRef = ref()
const groupFormRef = ref()

const baseActions = [
  {
    label: t('ActivityTable.handle_placeholder_request'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) => item.status === statuses.FINAL && props.requested,
    accessRole: roles.LIBRARY_WRITE,
    click: createSponsorFromRequested,
  },
  {
    label: t('_global.approve'),
    icon: 'mdi-check-decagram',
    iconColor: 'success',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'approve'),
    accessRole: roles.LIBRARY_WRITE,
    click: approveItem,
  },
  {
    label: t('_global.edit'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'edit') &&
      !props.requested,
    accessRole: roles.LIBRARY_WRITE,
    click: editItem,
  },
  {
    label: t('_global.new_version'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'new_version'),
    accessRole: roles.LIBRARY_WRITE,
    click: newItemVersion,
  },
  {
    label: t('_global.inactivate'),
    icon: 'mdi-close-octagon-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'inactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: inactivateItem,
  },
  {
    label: t('_global.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'reactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: reactivateItem,
  },
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) =>
      item.possible_actions.find((action) => action === 'delete'),
    accessRole: roles.LIBRARY_WRITE,
    click: deleteItem,
  },
  {
    label: t('_global.history'),
    icon: 'mdi-history',
    accessRole: roles.LIBRARY_READ,
    click: openItemHistory,
  },
]

const instanceActions = [
  // --- Attributes actions ---
  {
    label: t('ActivitiesTable.approve_attributes'),
    icon: 'mdi-check-decagram',
    iconColor: 'success',
    condition: (item) => item.possible_actions?.includes('approve'),
    accessRole: roles.LIBRARY_WRITE,
    click: (item) => approveItem(item, 'activity-instances', 'attributes'),
  },
  {
    label: t('ActivitiesTable.edit_attributes'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) => item.possible_actions?.includes('edit'),
    accessRole: roles.LIBRARY_WRITE,
    click: (item) => editInstanceAttributes(item),
  },
  {
    label: t('ActivitiesTable.new_version_attributes'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: (item) => item.possible_actions?.includes('new_version'),
    accessRole: roles.LIBRARY_WRITE,
    click: (item) => newItemVersion(item, 'activity-instances', 'attributes'),
  },
  {
    label: t('ActivitiesTable.inactivate'),
    icon: 'mdi-close-octagon-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.possible_actions?.includes('inactivate') ||
      item.groupings_possible_actions?.includes('inactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: (item) => inactivateInstance(item),
  },
  {
    label: t('ActivitiesTable.reactivate'),
    icon: 'mdi-undo-variant',
    iconColor: 'primary',
    condition: (item) =>
      item.status === statuses.RETIRED &&
      item.possible_actions?.includes('reactivate'),
    accessRole: roles.LIBRARY_WRITE,
    click: (item) => reactivateInstance(item),
  },
  // --- Groupings actions ---
  {
    label: t('ActivitiesTable.approve_groupings'),
    icon: 'mdi-check-decagram',
    iconColor: 'success',
    condition: (item) => item.groupings_possible_actions?.includes('approve'),
    accessRole: roles.LIBRARY_WRITE,
    click: (item) => approveItem(item, 'activity-instances', 'groupings'),
  },
  {
    label: t('ActivitiesTable.edit_groupings'),
    icon: 'mdi-pencil-outline',
    iconColor: 'primary',
    condition: (item) => item.groupings_possible_actions?.includes('edit'),
    accessRole: roles.LIBRARY_WRITE,
    click: (item) => editInstanceGroupings(item),
  },
  {
    label: t('ActivitiesTable.new_version_groupings'),
    icon: 'mdi-plus-circle-outline',
    iconColor: 'primary',
    condition: (item) =>
      item.groupings_possible_actions?.includes('new_version'),
    accessRole: roles.LIBRARY_WRITE,
    click: (item) => newItemVersion(item, 'activity-instances', 'groupings'),
  },
  // --- Shared actions ---
  {
    label: t('_global.delete'),
    icon: 'mdi-delete-outline',
    iconColor: 'error',
    condition: (item) => item.possible_actions?.includes('delete'),
    accessRole: roles.LIBRARY_WRITE,
    click: deleteItem,
  },
  {
    label: t('ActivitiesTable.history_attributes'),
    icon: 'mdi-history',
    accessRole: roles.LIBRARY_READ,
    click: (item) => openItemHistory(item, 'activity-instances', 'attributes'),
  },
  {
    label: t('ActivitiesTable.history_groupings'),
    icon: 'mdi-history',
    accessRole: roles.LIBRARY_READ,
    click: (item) => openItemHistory(item, 'activity-instances', 'groupings'),
  },
]

const currentActions = computed(() => {
  return props.source === 'activity-instances' ? instanceActions : baseActions
})

const activities = ref([])
const activitiesHeaders = [
  { title: '', key: 'actions', width: '1%', noFilter: true },
  { title: t('_global.library'), key: 'library_name' },
  {
    title: t('ActivityTable.activity_group'),
    key: 'activity_group.name',
    externalFilterSource: 'concepts/activities/activity-groups$name',
    width: '15%',
    exludeFromHeader: [
      'is_data_collected',
      'is_used_by_legacy_instances',
      'synonyms',
    ],
  },
  {
    title: t('ActivityTable.activity_subgroup'),
    key: 'activity_subgroup.name',
    externalFilterSource: 'concepts/activities/activity-sub-groups$name',
    width: '15%',
    exludeFromHeader: [
      'is_data_collected',
      'is_used_by_legacy_instances',
      'synonyms',
    ],
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
  {
    title: t('ActivityTable.definition'),
    key: 'definition',
  },
  {
    title: t('ActivityTable.nci_concept_id'),
    key: 'nci_concept_id',
  },
  {
    title: t('ActivityTable.nci_concept_name'),
    key: 'nci_concept_name',
  },
  { title: t('ActivityTable.abbreviation'), key: 'abbreviation' },
  {
    title: t('ActivityTable.is_data_collected'),
    key: 'is_data_collected',
  },
  {
    title: t('ActivityTable.is_legacy_usage'),
    key: 'is_used_by_legacy_instances',
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'author_username' },
  { title: t('_global.status'), key: 'status', noFilter: true },
  { title: t('_global.version'), key: 'version' },
]
const instantiationsHeaders = [
  { title: '', key: 'actions', width: '1%', noFilter: true },
  { title: t('_global.library'), key: 'library_name' },
  {
    title: t('ActivityTable.activity_group'),
    key: 'activity_group.name',
    externalFilterSource: 'concepts/activities/activity-groups$name',
    width: '15%',
    disableColumnFilters: true,
    exludeFromHeader: [
      'is_data_collected',
      'is_used_by_legacy_instances',
      'synonyms',
    ],
  },
  {
    title: t('ActivityTable.activity_subgroup'),
    key: 'activity_subgroup.name',
    externalFilterSource: 'concepts/activities/activity-sub-groups$name',
    width: '15%',
    disableColumnFilters: true,
    exludeFromHeader: [
      'is_data_collected',
      'is_used_by_legacy_instances',
      'synonyms',
    ],
  },
  {
    title: t('ActivityTable.activity'),
    key: 'activity_name',
    disableColumnFilters: true,
  },
  {
    title: t('ActivityTable.type'),
    key: 'activity_instance_class.name',
  },
  { title: t('ActivityTable.instance'), key: 'name' },
  {
    title: t('ActivityTable.nci_concept_id'),
    key: 'nci_concept_id',
  },
  {
    title: t('ActivityTable.nci_concept_name'),
    key: 'nci_concept_name',
  },
  {
    title: t('ActivityTable.is_research_lab'),
    key: 'is_research_lab',
  },
  {
    title: t('ActivityTable.molecular_weight'),
    key: 'molecular_weight',
  },
  { title: t('ActivityTable.topic_code'), key: 'topic_code' },
  { title: t('ActivityTable.adam_code'), key: 'adam_param_code' },
  {
    title: t('ActivityTable.is_required_for_activity'),
    key: 'is_required_for_activity',
  },
  {
    title: t('ActivityTable.is_default_selected_for_activity'),
    key: 'is_default_selected_for_activity',
  },
  {
    title: t('ActivityTable.is_data_sharing'),
    key: 'is_data_sharing',
  },
  {
    title: t('ActivityTable.is_legacy_usage'),
    key: 'is_legacy_usage',
  },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'author_username' },
  { title: t('_global.status'), key: 'status', noFilter: true },
  { title: t('_global.version'), key: 'version' },
  { title: t('ActivityTable.groupings_modified'), key: 'groupings_start_date' },
  {
    title: t('ActivityTable.groupings_modified_by'),
    key: 'groupings_author_username',
  },
  {
    title: t('ActivityTable.groupings_status'),
    key: 'groupings_status',
    noFilter: true,
  },
  { title: t('ActivityTable.groupings_version'), key: 'groupings_version' },
]
const groupsHeaders = [
  { title: t('ActivityTable.group_or_subgroup'), key: 'name' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.status'), key: 'status', noFilter: true },
  { title: t('_global.version'), key: 'version' },
]
const requestedHeaders = [
  { title: '', key: 'actions', width: '1%' },
  {
    title: t('ActivityTable.activity_group'),
    key: 'activity_group.name',
    externalFilterSource: 'concepts/activities/activity-groups$name',
    exludeFromHeader: ['request_rationale'],
  },
  {
    title: t('ActivityTable.activity_subgroup'),
    key: 'activity_subgroup.name',
    externalFilterSource: 'concepts/activities/activity-sub-groups$name',
    exludeFromHeader: ['request_rationale'],
  },
  {
    title: t('ActivityTable.activity'),
    key: 'name',
    externalFilterSource: 'concepts/activities/activities$name',
  },
  {
    title: t('ActivityTable.sentence_case_name'),
    key: 'name_sentence_case',
  },
  { title: t('ActivityTable.abbreviation'), key: 'abbreviation' },
  { title: t('ActivityTable.definition'), key: 'definition' },
  {
    title: t('ActivityTable.rationale_for_request'),
    key: 'request_rationale',
  },
  { title: t('ActivityTable.study_id'), key: 'used_by_studies' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.modified_by'), key: 'author_username' },
  { title: t('_global.status'), key: 'status', noFilter: true },
  { title: t('_global.version'), key: 'version' },
]
const activityGroupHeaders = [
  { title: '', key: 'actions', width: '1%' },
  { title: t('ActivityTable.activity_group'), key: 'name' },
  {
    title: t('ActivityTable.sentence_case_name'),
    key: 'name_sentence_case',
  },
  { title: t('ActivityTable.abbreviation'), key: 'abbreviation' },
  { title: t('_global.definition'), key: 'definition' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.status'), key: 'status', noFilter: true },
  { title: t('_global.version'), key: 'version' },
]
const activitySubgroupHeaders = [
  { title: '', key: 'actions', width: '1%' },
  {
    title: t('ActivityTable.activity_subgroup'),
    key: 'name',
    externalFilterSource: 'concepts/activities/activity-sub-groups$name',
    value: 'activity_subgroup.name',
  },
  {
    title: t('ActivityTable.sentence_case_name'),
    key: 'name_sentence_case',
  },
  { title: t('ActivityTable.abbreviation'), key: 'abbreviation' },
  { title: t('_global.definition'), key: 'definition' },
  { title: t('_global.modified'), key: 'start_date' },
  { title: t('_global.status'), key: 'status', noFilter: true },
  { title: t('_global.version'), key: 'version' },
]
const groupMode = ref(false)
const historyItems = ref([])
const historyExcludedHeaders = ['actions']
const total = ref(0)
const savedFilters = ref('')
const showActivityForm = ref(false)
const showRequestedActivityForm = ref(false)
const showGroupsForm = ref(false)
const showHistory = ref(false)
const showInstantiationsForm = ref(false)
const instanceEditMode = ref(null)
const showSponsorFromRequestedForm = ref(false)
const activeItem = ref(null)
const showFinalised = ref(false)
const showInstanceLinkingForm = ref(false)
const instanceLinkingActivity = ref(null)
const selectedStatusTab = ref('final') // Default to 'final' tab
const isStatusLoading = ref(false)
const onlyArchivedLibrary = ref(false)

const statusTabs = [
  { value: 'all', label: 'All' },
  { value: 'final', label: 'Final' },
  { value: 'retired', label: 'Retired' },
  { value: 'draft', label: 'Draft' },
]

const itemCreationTitle = computed(() => {
  if (props.source === 'activities') {
    return t('ActivityForms.add_activity')
  } else if (props.source === 'activity-instances') {
    return t('ActivityForms.addInstance')
  } else if (props.source === 'activity-groups') {
    return t('ActivityForms.add_group')
  } else if (props.source === 'activity-sub-groups') {
    return t('ActivityForms.add_subgroup')
  }
  return ''
})

const itemHistoryTitle = computed(() => {
  if (activeItem.value) {
    let type
    switch (props.source) {
      case 'activities':
        type = t('ActivitiesTable.activity')
        break
      case 'activity-groups':
        type = t('ActivitiesTable.activity_group')
        break
      case 'activity-sub-groups':
        type = t('ActivitiesTable.activity_subgroup')
        break
      case 'activity-instances':
        type = t('ActivitiesTable.activity_instance')
        break
    }
    return t('ActivitiesTable.item_history_title', {
      uid: activeItem.value.uid,
      type,
    })
  }
  return ''
})

const currentHeaders = computed(() => {
  switch (props.source) {
    case 'activities':
      return props.requested ? requestedHeaders : activitiesHeaders
    case 'activity-groups':
      return activityGroupHeaders
    case 'activity-sub-groups':
      return activitySubgroupHeaders
    case 'activities-by-grouping':
      return groupsHeaders
    case 'activity-instances':
      return instantiationsHeaders
  }
  return []
})

const newWizardStepper = computed(() => {
  return featureFlagsStore.getFeatureFlag(
    'new_activity_instance_wizard_stepper'
  )
})

const newWizardStepperEditMode = computed(() => {
  return featureFlagsStore.getFeatureFlag(
    'activity_instance_wizard_stepper_edit_mode'
  )
})

const showStatusTabs = computed(() => {
  return [
    'activities',
    'activity-groups',
    'activity-sub-groups',
    'activity-instances',
  ].includes(props.source)
})

function normalizeFiltersObject(filters) {
  if (_isEmpty(filters)) {
    return {}
  }

  if (typeof filters === 'string') {
    try {
      const parsedFilters = JSON.parse(filters)
      return parsedFilters && typeof parsedFilters === 'object'
        ? parsedFilters
        : {}
    } catch {
      return {}
    }
  }

  if (typeof filters === 'object') {
    return filters
  }

  return {}
}

function getActivitySubgroupUID(item) {
  if (item.activity_subgroup?.uid) {
    return item.activity_subgroup.uid
  }

  if (Array.isArray(item.activity_groupings)) {
    for (const grouping of item.activity_groupings) {
      if (grouping.activity_subgroup_uid) {
        return grouping.activity_subgroup_uid
      }
    }
  }
  return null
}

function getActivityGroupUID(item) {
  if (item.activity_group?.uid) {
    return item.activity_group.uid
  }

  if (Array.isArray(item.activity_groupings)) {
    for (const grouping of item.activity_groupings) {
      if (grouping.activity_group_uid) {
        return grouping.activity_group_uid
      }
    }
  }
  return null
}

function transformItems(items) {
  const activities = []
  if (props.source === 'activities') {
    for (const item of items) {
      if (item.activity_groupings.length > 0) {
        const groups = []
        const subgroups = []
        for (const grouping of item.activity_groupings) {
          groups.push(grouping.activity_group_name)
          subgroups.push(grouping.activity_subgroup_name)
        }
        activities.push({
          activity_group: { name: groups },
          activity_subgroup: { name: subgroups },
          item_key: item.uid,
          ...item,
        })
      } else {
        activities.push({
          activity_group: { name: '' },
          activity_subgroup: { name: '' },
          item_key: item.uid,
          ...item,
        })
      }
    }
  } else if (props.source === 'activity-sub-groups') {
    for (const item of items) {
      activities.push({
        activity_subgroup: {
          name: item.name,
          uid: item.uid,
        },
        item_key: item.uid,
        ...item,
      })
    }
  } else if (props.source === 'activity-instances') {
    for (const item of items) {
      if (item.activity_groupings && item.activity_groupings.length > 0) {
        const groups = []
        const subgroups = []
        // Set activities from the first grouping if it exists
        const itemActivities = item.activity_groupings[0]?.activity
          ? [item.activity_groupings[0].activity]
          : item.activities || []

        for (const grouping of item.activity_groupings) {
          groups.push(grouping.activity_group.name)
          subgroups.push(grouping.activity_subgroup.name)
        }
        // Remove existing activity_group and activity_subgroup to avoid conflicts
        const cleanItem = { ...item }
        delete cleanItem.activity_group
        delete cleanItem.activity_subgroup
        activities.push({
          ...cleanItem,
          activities: itemActivities,
          activity_group: { name: groups },
          activity_subgroup: { name: subgroups },
          item_key: item.uid,
        })
      } else {
        activities.push({
          ...item,
          activity_group: { name: '' },
          activity_subgroup: { name: '' },
          item_key: item.uid,
        })
      }
    }
  } else if (props.source === 'activity-groups') {
    for (const item of items) {
      item.activity_group = {
        name: item.name,
        uid: item.uid,
      }
      item.item_key = item.uid
      activities.push(item)
    }
  } else if (props.source === 'activities-by-grouping') {
    for (const item of items) {
      item.subgroups = []
      item.subgroupsLoading = false
      item.item_key = item.uid
      activities.push(item)
    }
  } else {
    for (const item of items) {
      item.item_key = item.uid
      activities.push(item)
    }
  }
  return activities
}

function onStatusTabChange() {
  // Trigger a new fetch when tab changes
  isStatusLoading.value = true
  if (tableRef.value) {
    tableRef.value.filterTable()
  }
}

function getSelectedStatusValue() {
  if (selectedStatusTab.value === 'final') {
    return statuses.FINAL
  }
  if (selectedStatusTab.value === 'retired') {
    return statuses.RETIRED
  }
  if (selectedStatusTab.value === 'draft') {
    return statuses.DRAFT
  }
  return null
}

function fetchActivities(filters, options, filtersUpdated) {
  try {
    if (filters !== undefined) {
      savedFilters.value = filters
    }
    const params = filteringParameters.prepareParameters(
      options,
      savedFilters.value,
      filtersUpdated
    )
    if (options.sortBy[0] && options.sortBy[0].key === 'activity_group.name') {
      params.sort_by = JSON.stringify({
        'activity_groupings[0].activity_group_name':
          options.sortBy[0].order === 'desc' ? false : true,
      })
    } else if (
      options.sortBy[0] &&
      options.sortBy[0].key === 'activity_subgroup.name'
    ) {
      params.sort_by = JSON.stringify({
        'activity_groupings[0].activity_subgroup_name':
          options.sortBy[0].order === 'desc' ? false : true,
      })
    }
    params.filters = {}
    if (props.requested) {
      params.library_name = libConstants.LIBRARY_REQUESTED
    }
    if (
      (savedFilters.value &&
        savedFilters.value !== undefined &&
        savedFilters.value !== '{}' &&
        props.source === 'activities') ||
      props.source === 'activity-instances'
    ) {
      const filtersObj = JSON.parse(savedFilters.value)
      if (filtersObj['activity_group.name']) {
        params.activity_group_names = []
        filtersObj['activity_group.name'].v.forEach((value) => {
          params.activity_group_names.push(value)
        })
        delete filtersObj['activity_group.name']
      }
      if (filtersObj['activity_subgroup.name']) {
        params.activity_subgroup_names = []
        filtersObj['activity_subgroup.name'].v.forEach((value) => {
          params.activity_subgroup_names.push(value)
        })
        delete filtersObj['activity_subgroup.name']
      }
      if (filtersObj.name) {
        let param =
          props.source === 'activity-instances' ? 'names' : 'activity_names'
        params[param] = []
        filtersObj.name.v.forEach((value) => {
          params[param].push(value)
        })
        delete filtersObj.name
      }
      if (filtersObj['activities.name']) {
        params.activity_names = []
        filtersObj['activities.name'].v.forEach((value) => {
          params.activity_names.push(value)
        })
        delete filtersObj['activities.name']
      }
      if (filtersObj.specimen) {
        params.specimen_names = []
        filtersObj.specimen.v.forEach((value) => {
          params.specimen_names.push(value)
        })
        delete filtersObj.specimen
      }
      if (
        Object.keys(filtersObj).length !== 0 &&
        filtersObj.constructor === Object
      ) {
        params.filters = JSON.stringify(filtersObj)
      }
    } else if (
      savedFilters.value !== undefined &&
      savedFilters.value !== '{}' &&
      props.source === 'activity-sub-groups'
    ) {
      const filtersObj = JSON.parse(savedFilters.value)
      if (filtersObj.activity_groups) {
        params.activity_group_names = []
        filtersObj.activity_groups.v.forEach((value) => {
          params.activity_group_names.push(value)
        })
        delete filtersObj.activity_groups
      }
      if (
        Object.keys(filtersObj).length !== 0 &&
        filtersObj.constructor === Object
      ) {
        params.filters = JSON.stringify(filtersObj)
      }
    } else if (
      savedFilters.value !== undefined &&
      savedFilters.value !== '{}'
    ) {
      params.filters = savedFilters.value
    }

    // Apply status filtering based on selected tab
    if (!props.requested && showStatusTabs.value) {
      const selectedStatusValue = getSelectedStatusValue()

      if (props.source === 'activity-instances') {
        if (selectedStatusValue) {
          params.status = selectedStatusValue
        } else {
          delete params.status
        }
      } else if (selectedStatusValue) {
        const statusFilter = { status: { v: [selectedStatusValue] } }
        if (_isEmpty(params.filters)) {
          params.filters = statusFilter
        } else {
          const filtersObj = normalizeFiltersObject(params.filters)
          Object.assign(filtersObj, statusFilter)
          params.filters = filtersObj
        }
      }
    }

    if (props.requested) {
      const filtersObj = normalizeFiltersObject(params.filters)
      filtersObj.is_finalized = { v: [showFinalised.value] }
      filtersObj.is_request_final = { v: [true] }
      params.filters = filtersObj
    }

    if (props.source === 'activities') {
      params.filters = normalizeFiltersObject(params.filters)
      if (onlyArchivedLibrary.value) {
        params.library_name = libConstants.LIBRARY_ARCHIVED
      }
    }

    if (props.source === 'activities-by-grouping') {
      params.library_name = libConstants.LIBRARY_SPONSOR
      const filtersObj = normalizeFiltersObject(params.filters)
      filtersObj.status = { v: [statuses.FINAL] }
      params.filters = filtersObj
    }

    // Ensure filters are stringified if they're objects
    if (params.filters && typeof params.filters === 'object') {
      params.filters = JSON.stringify(params.filters)
    }

    const source =
      props.source !== 'activities-by-grouping'
        ? props.source
        : 'activity-groups'
    activitiesApi.get(params, source).then((resp) => {
      activities.value = transformItems(resp.data.items)
      total.value = resp.data.total
      isStatusLoading.value = false
    })
    if (groupFormRef.value) {
      groupFormRef.value.getGroups()
    }
  } catch (error) {
    console.error('Error fetching activities:', error)
  }
}

async function fetchGlobalAuditTrail(options) {
  const resp = await activitiesApi.getAuditTrail(props.source, options)
  return {
    items: transformItems(resp.data.items),
    total: resp.data.total,
  }
}

function modifyFilters(jsonFilter, params) {
  if (jsonFilter['activity_group.name']) {
    params.activity_group_names = []
    jsonFilter['activity_group.name'].v.forEach((value) => {
      params.activity_group_names.push(value)
    })
    delete jsonFilter['activity_group.name']
  }
  if (jsonFilter.activity_groups) {
    params.activity_group_names = []
    jsonFilter.activity_groups.v.forEach((value) => {
      params.activity_group_names.push(value)
    })
    delete jsonFilter.activity_groups
  }
  if (jsonFilter['activity_subgroup.name']) {
    params.activity_subgroup_names = []
    jsonFilter['activity_subgroup.name'].v.forEach((value) => {
      params.activity_subgroup_names.push(value)
    })
    delete jsonFilter['activity_subgroup.name']
  }
  if (jsonFilter.name && props.source === 'activities') {
    params.activity_names = []
    jsonFilter.name.v.forEach((value) => {
      params.activity_names.push(value)
    })
    delete jsonFilter.name
  }
  if (jsonFilter['activities.name']) {
    params.activity_names = []
    jsonFilter['activities.name'].v.forEach((value) => {
      params.activity_names.push(value)
    })
    delete jsonFilter['activities.name']
  }
  if (jsonFilter.specimen) {
    params.specimen_names = []
    jsonFilter.activities.v.forEach((value) => {
      params.specimen_names.push(value)
    })
    delete jsonFilter.specimen
  }

  // Apply status filtering based on selected tab for filter dropdowns
  if (!props.requested && showStatusTabs.value) {
    if (props.source === 'activity-instances') {
      delete jsonFilter.status
    } else {
      const selectedStatusValue = getSelectedStatusValue()
      if (selectedStatusValue) {
        jsonFilter.status = { v: [selectedStatusValue] }
      } else if (jsonFilter.status) {
        // 'all' tab doesn't apply any status filter, so remove it if it exists.
        delete jsonFilter.status
      }
    }

    if (selectedStatusTab.value === 'all' && jsonFilter.status) {
      delete jsonFilter.status
    }
  }

  if (onlyArchivedLibrary.value) {
    delete jsonFilter.library_name
    params.library_name = libConstants.LIBRARY_ARCHIVED
  }

  return {
    jsonFilter: jsonFilter,
    params: params,
  }
}

function isExpand() {
  return props.source === 'activities-by-grouping'
}

function synonymsDisplay(item) {
  if (!item?.length) return ''
  return item.map((element) => `&#9679; ${escapeHTML(element)}`).join('<br />')
}

function groupsDisplay(item) {
  if (!item.activity_group || !item.activity_group.name) {
    return ''
  }

  const groupName = item.activity_group.name

  if (Array.isArray(groupName)) {
    if (groupName.length === 1) {
      return escapeHTML(groupName[0])
    } else {
      return groupName
        .map((name) => `&#9679; ${escapeHTML(name)}`)
        .join('<br />')
    }
  }

  return escapeHTML(groupName)
}

function subGroupsDisplay(item) {
  if (!item.activity_subgroup || !item.activity_subgroup.name) {
    return ''
  }

  const subName = item.activity_subgroup.name

  if (Array.isArray(subName)) {
    if (subName.length === 1) {
      return escapeHTML(subName[0])
    } else {
      return subName.map((name) => `&#9679; ${escapeHTML(name)}`).join('<br />')
    }
  }

  return escapeHTML(subName)
}

function activitiesDisplay(item) {
  let display = ''
  if (item.activities) {
    item.activities.forEach((element) => {
      display += element.name + ', '
    })
  }
  return display.slice(0, -2)
}

function inactivateItem(item, source, subitem) {
  source = source === undefined ? props.source : source
  activitiesApi.inactivate(item.uid, source, subitem).then(() => {
    notificationHub.add({
      msg: t(`ActivitiesTable.inactivate_${props.source}_success`),
      type: 'success',
    })
    tableRef.value.filterTable()
  })
}

function inactivateInstance(item) {
  activitiesApi.inactivate(item.uid, 'activity-instances').then(() => {
    notificationHub.add({
      msg: t(`ActivitiesTable.inactivate_${props.source}_success`),
      type: 'success',
    })
    tableRef.value.filterTable()
  })
}

function reactivateItem(item, source, subitem) {
  source = source === undefined ? props.source : source
  activitiesApi.reactivate(item.uid, source, subitem).then(() => {
    notificationHub.add({
      msg: t(`ActivitiesTable.reactivate_${props.source}_success`),
      type: 'success',
    })
    tableRef.value.filterTable()
  })
}

function reactivateInstance(item) {
  activitiesApi.reactivate(item.uid, 'activity-instances').then(() => {
    notificationHub.add({
      msg: t(`ActivitiesTable.reactivate_${props.source}_success`),
      type: 'success',
    })
    tableRef.value.filterTable()
  })
}

function deleteItem(item, source) {
  source = source === undefined ? props.source : source
  activitiesApi.delete(item.uid, source).then(() => {
    notificationHub.add({
      msg: t(`ActivitiesTable.delete_${props.source}_success`),
      type: 'success',
    })
    tableRef.value.filterTable()
  })
}

function approveItem(item, source, subitem) {
  source = source === undefined ? props.source : source
  const options = {}
  if (['activity-groups', 'activity-sub-groups'].includes(source)) {
    options.cascade_edit_and_approve = true
  }
  if (source === 'activities') {
    options.cascade_edit_and_approve = false
  }
  activitiesApi.approve(item.uid, source, options, subitem).then(() => {
    notificationHub.add({
      msg: t(`ActivitiesTable.approve_${props.source}_success`),
      type: 'success',
    })
    tableRef.value.filterTable()

    if (source === 'activities') {
      openInstanceLinkingForm(item)
    }
  })
}

function openInstanceLinkingForm(item) {
  instanceLinkingActivity.value = item
  showInstanceLinkingForm.value = true
}

function closeInstanceLinkingForm() {
  showInstanceLinkingForm.value = false
  instanceLinkingActivity.value = null
  tableRef.value.filterTable()
}

function newItemVersion(item, source, subitem) {
  source = source === undefined ? props.source : source
  activitiesApi.newVersion(item.uid, source, subitem).then(() => {
    notificationHub.add({
      msg: t('_global.new_version_success'),
      type: 'success',
    })
    tableRef.value.filterTable()
  })
}

function showForm() {
  switch (props.source) {
    case 'activities':
      if (props.requested) {
        showRequestedActivityForm.value = true
      } else {
        showActivityForm.value = true
      }
      return
    case 'activity-groups':
      groupMode.value = true
      showGroupsForm.value = true
      return
    case 'activity-sub-groups':
      groupMode.value = false
      showGroupsForm.value = true
      return
    case 'activity-instances':
      showInstantiationsForm.value = true
  }
}

function editItem(item) {
  activeItem.value = item
  switch (props.source) {
    case 'activities':
      if (props.requested) {
        showRequestedActivityForm.value = true
      } else {
        showActivityForm.value = true
      }
      return
    case 'activity-groups':
      groupMode.value = true
      showGroupsForm.value = true
      return
    case 'activity-sub-groups':
      groupMode.value = false
      showGroupsForm.value = true
      return
    case 'activity-instances':
      showInstantiationsForm.value = true
  }
}

function editInstanceAttributes(item) {
  activeItem.value = item
  instanceEditMode.value = 'attributes'
  showInstantiationsForm.value = true
}

function editInstanceGroupings(item) {
  activeItem.value = item
  instanceEditMode.value = 'groupings'
  showInstantiationsForm.value = true
}

async function openItemHistory(item, source, subitem) {
  source = source === undefined ? props.source : source
  activeItem.value = item
  const resp = await activitiesApi.getVersions(source, item.uid, subitem)
  historyItems.value = transformItems(resp.data)
  showHistory.value = true
}

function closeHistory() {
  activeItem.value = null
  showHistory.value = false
}

function createSponsorFromRequested(item) {
  activeItem.value = item
  showSponsorFromRequestedForm.value = true
}

function getSubGroups(items) {
  for (const expandedItem of items) {
    const group = activities.value.find((a) => a.uid === expandedItem.uid)
    if (!group || (group.subgroups && group.subgroups.length > 0)) {
      continue
    }
    group.subgroupsLoading = true
    activitiesApi.getSubGroups(group.uid).then((resp) => {
      group.subgroups = resp.data.items.filter(
        (sg) => sg.status === statuses.FINAL
      )
      for (const subgroup of group.subgroups) {
        subgroup.activities = []
        subgroup.activitiesLoading = false
        subgroup.group_uid = group.uid
        subgroup.item_key = group.uid + '.' + subgroup.uid
      }
      group.subgroupsLoading = false
    })
  }
}

function getSubgroupActivities(items) {
  for (const expandedItem of items) {
    const group = activities.value.find(
      (a) => a.subgroups && a.subgroups.some((s) => s.uid === expandedItem.uid)
    )
    const subgroup = group?.subgroups?.find((s) => s.uid === expandedItem.uid)
    if (!subgroup || (subgroup.activities && subgroup.activities.length > 0)) {
      continue
    }
    subgroup.activitiesLoading = true
    activitiesApi
      .getSubGroupActivities(subgroup.uid, subgroup.group_uid, {
        library_name: libConstants.LIBRARY_SPONSOR,
        filters: JSON.stringify({ status: { v: [statuses.FINAL] } }),
      })
      .then((resp) => {
        subgroup.activities = resp.data.items
        subgroup.activitiesLoading = false
      })
  }
}

function updateArchivedView() {
  if (onlyArchivedLibrary.value) {
    selectedStatusTab.value = 'all'
  } else {
    selectedStatusTab.value = 'final'
  }
  savedFilters.value = ''
  tableRef.value.showFilterBar = false
  tableRef.value.clearFilters()
  tableRef.value.loadFilters = false
}

function closeForm() {
  showActivityForm.value = false
  showRequestedActivityForm.value = false
  showGroupsForm.value = false
  showInstantiationsForm.value = false
  instanceEditMode.value = null
  showSponsorFromRequestedForm.value = false
  activeItem.value = null
  tableRef.value.filterTable()
}
</script>

<style scoped>
.layoutSelector {
  border-color: rgb(var(--v-theme-nnBaseBlue));
}

.layoutSelector :deep(.v-btn) {
  text-transform: none;
}
</style>
