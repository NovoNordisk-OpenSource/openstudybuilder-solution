<template>
  <TemplateIndexingForm
    ref="baseForm"
    :form="form"
    :template="template"
    @emit-form="updateForm"
  >
    <template #templateIndexFields>
      <v-row>
        <v-col cols="11">
          <v-autocomplete
            v-model="localForm.activity_group"
            :label="$t('ActivityInstructionTemplateForm.group')"
            data-cy="template-activity-group"
            :items="groups"
            item-title="name"
            item-value="uid"
            clearable
            :rules="[formRules.required]"
            @update:model-value="setSubGroups"
          />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="11">
          <v-autocomplete
            v-model="localForm.activity_subgroups"
            :label="$t('ActivityInstructionTemplateForm.sub_group')"
            data-cy="template-activity-sub-group"
            :items="subGroups"
            item-title="name"
            item-value="uid"
            clearable
            multiple
            :rules="[formRules.required]"
            @update:model-value="setActivities"
          />
        </v-col>
      </v-row>
      <NotApplicableField
        :checked="
          template && (!template.activities || !template.activities.length)
        "
        :clean-function="() => (localForm.activities = null)"
      >
        <template #mainField="{ notApplicable }">
          <v-row>
            <v-col cols="11">
              <v-autocomplete
                v-model="localForm.activities"
                :label="$t('ActivityInstructionTemplateForm.activity')"
                data-cy="template-activity-activity"
                :items="activities"
                item-title="name"
                return-object
                clearable
                multiple
                :disabled="notApplicable"
                :rules="[
                  (value) => formRules.requiredIfNotNA(value, notApplicable),
                ]"
              />
            </v-col>
          </v-row>
        </template>
      </NotApplicableField>
    </template>
  </TemplateIndexingForm>
</template>

<script>
import activities from '@/api/activities'
import NotApplicableField from '@/components/tools/NotApplicableField.vue'
import TemplateIndexingForm from './TemplateIndexingForm.vue'

export default {
  components: {
    NotApplicableField,
    TemplateIndexingForm,
  },
  inject: ['formRules'],
  props: {
    form: {
      type: Object,
      default: null,
    },
    template: {
      type: Object,
      default: null,
    },
  },
  data() {
    return {
      activities: [],
      groups: [],
      subGroups: [],
      localForm: { ...this.form },
    }
  },
  watch: {
    template: {
      handler: async function (value) {
        if (value && value.activity_groups && value.activity_groups.length) {
          if (!this.groups.length) {
            const resp = await activities.getGroups()
            this.groups = resp.data.items
          }
          const activityGroupUid =
            typeof this.template.activity_groups[0] !== 'string'
              ? this.template.activity_groups[0].uid
              : this.template.activity_groups[0]
          this.localForm.activity_group = activityGroupUid
          await this.setSubGroups(this.localForm.activity_group, true)
          if (!this.localForm.activity_subgroups) {
            this.localForm.activity_subgroups = value.activity_subgroups
          }
          const subgroupUids = this.localForm.activity_subgroups.map(
            (g) => g.uid
          )
          this.setActivities(subgroupUids, true)
          if (!this.localForm.activities) {
            this.localForm.activities = value.activities
          }
        }
      },
      immediate: true,
    },
  },
  created() {
    if (!this.groups.length) {
      activities.getGroups({ page_size: 0 }).then((resp) => {
        this.groups = resp.data.items
      })
    }
  },
  methods: {
    updateForm(indications) {
      this.localForm = { ...this.localForm, ...indications }
    },
    preparePayload() {
      const result = {}
      Object.assign(result, this.$refs.baseForm.preparePayload())
      result.activity_group_uids = [this.localForm.activity_group]
      result.activity_subgroup_uids = []
      for (const item of this.localForm.activity_subgroups) {
        const itemUid = typeof item !== 'string' ? item.uid : item
        result.activity_subgroup_uids.push(itemUid)
      }
      if (this.localForm.activities) {
        result.activity_uids = this.localForm.activities.map((item) => item.uid)
      } else {
        result.activity_uids = []
      }
      return result
    },
    async setSubGroups(group, noSubgroupReset) {
      if (group) {
        const resp = await activities.getSubGroups(group)
        this.subGroups = resp.data.items
      }
      if (!noSubgroupReset) {
        this.localForm.activity_subgroups = []
        this.localForm.activities = []
      }
    },
    setActivities(subgroupUids) {
      this.activities = []
      for (const sg of subgroupUids) {
        activities.getSubGroupActivities(sg).then((resp) => {
          this.activities = this.activities.concat(resp.data.items)
        })
      }
    },
  },
}
</script>
