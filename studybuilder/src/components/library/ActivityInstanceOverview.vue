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
            {{ itemOverview.activity_instance.name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.sentence_case_name') }}
          </v-col>
          <v-col cols="10">
            {{ itemOverview.activity_instance.name_sentence_case }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.version') }}
          </v-col>
          <v-col cols="2">
            <v-select
              :items="allVersions(itemOverview)"
              :value="itemOverview.activity_instance.version"
              @update:model-value="
                (value) => changeVersion(itemOverview, value)
              "
            ></v-select>
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.status') }}
          </v-col>
          <v-col cols="2">
            <StatusChip
              v-if="item"
              :status="itemOverview.activity_instance.status"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.start_date') }}
          </v-col>
          <v-col cols="2">
            {{
              itemOverview.activity_instance.start_date
                ? $filters.date(itemOverview.activity_instance.start_date)
                : $t('_global.date_null')
            }}
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.end_date') }}
          </v-col>
          <v-col cols="2">
            {{
              itemOverview.activity_instance.end_date
                ? $filters.date(itemOverview.activity_instance.end_date)
                : $t('_global.date_null')
            }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.definition') }}
          </v-col>
          <v-col cols="10">
            {{ itemOverview.activity_instance.definition }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityInstanceOverview.class') }}
          </v-col>
          <v-col cols="10">
            {{ itemOverview.activity_instance.activity_instance_class.name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.abbreviation') }}
          </v-col>
          <v-col cols="2">
            {{ itemOverview.activity_instance.abbreviation }}
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('_global.library') }}
          </v-col>
          <v-col cols="2">
            {{ itemOverview.activity_instance.library_name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityInstanceOverview.nci_concept_id') }}
          </v-col>
          <v-col cols="10">
            <NCIConceptLink
              :concept-id="itemOverview.activity_instance.nci_concept_id"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityInstanceOverview.nci_concept_name') }}
          </v-col>
          <v-col cols="10">
            {{ itemOverview.activity_instance.nci_concept_name }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityInstanceOverview.is_research_lab') }}
          </v-col>
          <v-col cols="10">
            {{ $filters.yesno(itemOverview.activity_instance.is_research_lab) }}
          </v-col>
        </v-row>
        <v-row v-if="showMolecularWeight(itemOverview)">
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityInstanceOverview.molecular_weight') }}
          </v-col>
          <v-col cols="10">
            {{ itemOverview.activity_instance.molecular_weight }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityInstanceOverview.adam_code') }}
          </v-col>
          <v-col cols="2">
            {{ itemOverview.activity_instance.adam_param_code }}
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityInstanceOverview.topic_code') }}
          </v-col>
          <v-col cols="2">
            {{ itemOverview.activity_instance.topic_code }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityInstanceOverview.is_required_for_activity') }}
          </v-col>
          <v-col cols="2">
            {{
              $filters.yesno(
                itemOverview.activity_instance.is_required_for_activity
              )
            }}
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{
              $t('ActivityInstanceOverview.is_default_selected_for_activity')
            }}
          </v-col>
          <v-col cols="2">
            {{
              $filters.yesno(
                itemOverview.activity_instance.is_default_selected_for_activity
              )
            }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityInstanceOverview.is_data_sharing') }}
          </v-col>
          <v-col cols="2">
            {{ $filters.yesno(itemOverview.activity_instance.is_data_sharing) }}
          </v-col>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityInstanceOverview.is_legacy_usage') }}
          </v-col>
          <v-col cols="2">
            {{ $filters.yesno(itemOverview.activity_instance.is_legacy_usage) }}
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityInstanceOverview.activity_groupings') }}
          </v-col>
          <v-col cols="10">
            <v-table>
              <thead>
                <tr class="text-left">
                  <th scope="col">
                    {{ $t('ActivityInstanceOverview.activity_group') }}
                  </th>
                  <th scope="col">
                    {{ $t('ActivityInstanceOverview.activity_subgroup') }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="grouping in itemOverview.activity_groupings"
                  :key="grouping.activity_subgroup_name"
                >
                  <td>
                    <router-link
                      :to="{
                        name: 'GroupOverview',
                        params: {
                          id: grouping.activity_group.uid,
                          version: grouping.activity_group.version || '1.0',
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
                          version: grouping.activity_subgroup.version || '1.0',
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
            {{ $t('ActivityInstanceOverview.activity') }}
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
                    {{ $t('_global.library') }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <router-link
                      :to="{
                        name: 'ActivityOverview',
                        params: {
                          id: itemOverview.activity_groupings[0].activity.uid,
                          version:
                            itemOverview.activity_groupings[0].activity.version,
                        },
                      }"
                    >
                      {{ itemOverview.activity_groupings[0].activity.name }}
                    </router-link>
                  </td>
                  <td>
                    {{ itemOverview.activity_groupings[0].activity.definition }}
                  </td>
                  <td>
                    {{ itemOverview.activity_groupings[0].activity.version }}
                  </td>
                  <td>
                    {{ itemOverview.activity_groupings[0].activity.status }}
                  </td>
                  <td>
                    {{
                      itemOverview.activity_groupings[0].activity.library_name
                    }}
                  </td>
                </tr>
              </tbody>
            </v-table>
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="2" class="font-weight-bold">
            {{ $t('ActivityInstanceOverview.items') }}
          </v-col>
          <v-col cols="10">
            <v-table>
              <thead>
                <tr class="text-left">
                  <th scope="col">
                    {{ $t('ActivityInstanceOverview.item_type') }}
                  </th>
                  <th scope="col">
                    {{ $t('_global.name') }}
                  </th>
                  <th scope="col">
                    {{ $t('ActivityInstanceOverview.item_class') }}
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(activityItem, index) in prepareItems(
                    itemOverview.activity_items
                  )"
                  :key="`item-${index}`"
                >
                  <td>
                    {{
                      activityItem.type === 'term'
                        ? $t('ActivityInstanceOverview.item_type_term')
                        : $t('ActivityInstanceOverview.item_type_unit')
                    }}
                  </td>
                  <td>
                    <v-table>
                      <tbody>
                        <tr
                          v-for="(name, nameIndex) in activityItem.names"
                          :key="`name-${nameIndex}`"
                        >
                          {{
                            name
                          }}
                        </tr>
                      </tbody>
                    </v-table>
                  </td>
                  <td>{{ activityItem.item_class.name }}</td>
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
          fullscreen
          content-class="top-dialog"
        >
          <ActivitiesInstantiationsForm
            :edited-activity="item"
            @close="close"
          />
        </v-dialog>
      </template>
    </BaseActivityOverview>
  </div>
</template>

<script>
import ActivitiesInstantiationsForm from '@/components/library/ActivitiesInstantiationsForm.vue'
import constants from '@/constants/parameters'
import BaseActivityOverview from './BaseActivityOverview.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import NCIConceptLink from '@/components//tools/NCIConceptLink.vue'
import { useAppStore } from '@/stores/app'

export default {
  components: {
    ActivitiesInstantiationsForm,
    BaseActivityOverview,
    StatusChip,
    NCIConceptLink,
  },
  emits: ['refresh'],
  setup() {
    const appStore = useAppStore()
    return {
      appStore,
    }
  },
  data() {
    return {
      historyHeaders: [
        { title: this.$t('_global.library'), key: 'library_name' },
        {
          title: this.$t('ActivityTable.type'),
          key: 'activity_instance_class.name',
        },
        {
          title: this.$t('ActivityTable.activity'),
          key: 'activity.name',
          externalFilterSource: 'concepts/activities/activities$name',
        },
        {
          title: this.$t('ActivityTable.activity_group'),
          key: 'activity_group.name',
          externalFilterSource: 'concepts/activities/activity-groups$name',
        },
        {
          title: this.$t('ActivityTable.activity_subgroup'),
          key: 'activity_subgroup.name',
          externalFilterSource: 'concepts/activities/activity-sub-groups$name',
        },
        { title: this.$t('ActivityTable.instance'), key: 'name' },
        {
          title: this.$t('ActivityTable.is_research_lab'),
          key: 'is_research_lab',
        },
        {
          title: this.$t('ActivityTable.molecular_weight'),
          key: 'molecular_weight',
        },
        { title: this.$t('_global.definition'), key: 'definition' },
        { title: this.$t('ActivityTable.topic_code'), key: 'topic_code' },
        { title: this.$t('ActivityTable.adam_code'), key: 'adam_param_code' },
        {
          title: this.$t('ActivityTable.is_required_for_activity'),
          key: 'is_required_for_activity',
        },
        {
          title: this.$t('ActivityTable.is_default_selected_for_activity'),
          key: 'is_default_selected_for_activity',
        },
        {
          title: this.$t('ActivityTable.is_data_sharing'),
          key: 'is_data_sharing',
        },
        {
          title: this.$t('ActivityTable.is_legacy_usage'),
          key: 'is_legacy_usage',
        },
        { title: this.$t('_global.modified'), key: 'start_date' },
        { title: this.$t('_global.modified_by'), key: 'author_username' },
        { title: this.$t('_global.status'), key: 'status' },
        { title: this.$t('_global.version'), key: 'version' },
      ],
    }
  },
  mounted() {
    this.appStore.addBreadcrumbsLevel(
      this.$t('Sidebar.library.concepts'),
      { name: 'Activities' },
      1,
      false
    )
    this.appStore.addBreadcrumbsLevel(
      this.$t('Sidebar.library.activities'),
      { name: 'Activities' },
      2,
      true
    )
    this.appStore.addBreadcrumbsLevel(
      this.$t('Sidebar.library.activities_instances'),
      { name: 'Activities' },
      3,
      true
    )
    this.appStore.addBreadcrumbsLevel(
      this.$refs.overview.itemOverview.activity_instance.name,
      { name: 'Activities' },
      4,
      true
    )
  },
  methods: {
    showMolecularWeight(item) {
      return (
        item.activity_instance.activity_instance_class.name ==
          constants.NUMERIC_FINDING &&
        item.activity_items.some((activity_item) => {
          return activity_item.unit_definitions.some((unit_definition) => {
            return unit_definition.dimension_name
              .toLowerCase()
              .includes('concentration')
          })
        })
      )
    },
    allVersions(item) {
      var all_versions = [...item.all_versions].sort().reverse()
      return all_versions
    },
    async changeVersion(activity_instance, version) {
      await this.$router.push({
        name: 'ActivityInstanceOverview',
        params: { id: activity_instance.uid, version: version },
      })
      this.$emit('refresh')
    },
    prepareItems(items) {
      const itemsForDisplay = []
      for (const item of items) {
        const newItem = { item_class: item.activity_item_class, names: [] }
        if (item.ct_terms.length > 0) {
          newItem.type = 'term'
          for (const term of item.ct_terms) {
            newItem.names.push(term.name)
          }
        } else if (item.unit_definitions.length > 0) {
          newItem.type = 'unit'
          for (const unit of item.unit_definitions) {
            newItem.names.push(unit.name)
          }
        } else {
          newItem.type = ''
        }
        itemsForDisplay.push(newItem)
      }
      return itemsForDisplay
    },
    transformItem(item) {
      if (item.activity_groupings.length > 0) {
        item.activities = [item.activity_groupings[0].activity]
        const groups = []
        const subgroups = []
        item.activity = { name: item.activity_groupings[0].activity.name }
        for (const grouping of item.activity_groupings) {
          groups.push(grouping.activity_group.name)
          subgroups.push(grouping.activity_subgroup.name)
        }
        item.activity_group = { name: groups }
        item.activity_subgroup = { name: subgroups }
      } else {
        item.activity_group = { name: [] }
        item.activity_subgroup = { name: [] }
        item.activity = { name: '' }
      }
      item.item_key = item.uid
    },
  },
}
</script>
