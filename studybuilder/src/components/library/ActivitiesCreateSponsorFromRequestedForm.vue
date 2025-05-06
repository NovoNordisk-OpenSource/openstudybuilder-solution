<template>
  <StepperForm
    ref="stepper"
    :title="title"
    :steps="steps"
    :form-observer-getter="getObserver"
    :help-items="helpItems"
    @close="close"
    @save="submit"
  >
    <template #[`step.request`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="activity.activity_groupings[0].activity_group_uid"
              :label="$t('ActivityForms.activity_group')"
              data-cy="handlerequestform-activity-group-dropdown"
              :items="groups"
              item-title="name"
              item-value="uid"
              density="compact"
              readonly
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="activity.activity_groupings[0].activity_subgroup_uid"
              :label="$t('ActivityForms.activity_subgroup')"
              data-cy="handlerequestform-activity-subgroup-dropdown"
              :items="subGroups"
              item-title="name"
              item-value="uid"
              density="compact"
              readonly
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="activity.name"
              :label="$t('ActivityForms.activity_name')"
              data-cy="handlerequestform-activity-name-field"
              density="compact"
              readonly
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="activity.abbreviation"
              :label="$t('ActivityFormsRequested.abbreviation')"
              data-cy="handlerequestform-abbreviation-field"
              density="compact"
              readonly
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              v-model="activity.definition"
              :label="$t('ActivityFormsRequested.definition')"
              data-cy="handlerequestform-definition-field"
              density="compact"
              auto-grow
              rows="1"
              readonly
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              v-model="activity.request_rationale"
              :label="$t('ActivityFormsRequested.rationale_for_request')"
              data-cy="handlerequestform-rationale-for-request-field"
              density="compact"
              auto-grow
              rows="1"
              readonly
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.sponsor`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col>
            <v-autocomplete
              v-model="group"
              :label="$t('ActivityForms.activity_group')"
              data-cy="sponsorform-activity-group-dropdown"
              :items="groups"
              item-title="name"
              item-value="uid"
              density="compact"
              clearable
              :rules="[formRules.required]"
              return-object
              @update:model-value="filterSubGroups"
            />
            <v-autocomplete
              v-model="subgroup"
              :label="$t('ActivityForms.activity_subgroup')"
              data-cy="sponsorform-activity-subgroup-dropdown"
              :items="filteredSubGroups"
              item-title="name"
              item-value="uid"
              density="compact"
              clearable
              :disabled="group ? false : true"
              :rules="[formRules.required]"
              return-object
            />
            <v-text-field
              v-model="form.name"
              :label="$t('ActivityForms.activity_name')"
              data-cy="sponsorform-activity-name-field"
              density="compact"
              clearable
              :rules="[formRules.required]"
              @input="getActivities"
            />
            <SentenceCaseNameField
              v-model="form.name_sentence_case"
              :name="form.name"
              :initial-name="form.name_sentence_case"
            />
            <v-row>
              <v-col>
                <v-text-field
                  v-model="form.nci_concept_id"
                  :label="$t('ActivityForms.nci_concept_id')"
                  data-cy="sponsorform-nciconceptid-field"
                  density="compact"
                  clearable
                />
              </v-col>
            </v-row>
            <v-text-field
              v-model="form.abbreviation"
              :label="$t('ActivityFormsRequested.abbreviation')"
              data-cy="sponsorform-abbreviation-field"
              density="compact"
              clearable
            />
            <v-textarea
              v-model="form.definition"
              :label="$t('ActivityFormsRequested.definition')"
              data-cy="sponsorform-definition-field"
              density="compact"
              clearable
              auto-grow
              rows="1"
              :rules="[formRules.required]"
            />
            <v-textarea
              v-model="form.request_rationale"
              :label="$t('ActivityFormsRequested.rationale_for_request')"
              data-cy="sponsorform-rationale-for-request-field"
              density="compact"
              clearable
              auto-grow
              rows="1"
              :rules="[formRules.required]"
            />
            <v-row>
              <v-col>
                <v-checkbox
                  v-model="form.is_data_collected"
                  :label="$t('ActivityForms.is_data_collected')"
                  data-cy="sponsorform-datacollected-checkbox"
                />
              </v-col>
            </v-row>
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #[`step.confirm`]="{ step }">
      <v-form :ref="`observer_${step}`">
        <v-row>
          <v-col cols="6">
            <div class="text-h5 mb-8">
              {{ $t('ActivityFormsRequested.requested_activity') }}
            </div>
            <v-text-field
              v-if="
                activity.activity_groupings[0].activity_group_uid ? true : false
              "
              v-model="activity.activity_groupings[0].activity_group_name"
              :label="$t('ActivityForms.activity_group')"
              data-cy="confirmation-request-group-field"
              density="compact"
              readonly
            />
            <v-text-field
              v-if="
                activity.activity_groupings[0].activity_group_uid ? true : false
              "
              v-model="activity.activity_groupings[0].activity_subgroup_name"
              :label="$t('ActivityForms.activity_subgroup')"
              data-cy="confirmation-request-subgroup-field"
              density="compact"
              readonly
            />
            <v-text-field
              v-model="activity.name"
              :label="$t('ActivityForms.activity_name')"
              data-cy="confirmation-request-activity-name-field"
              density="compact"
              readonly
            />
          </v-col>
          <v-col cols="6">
            <div class="text-h5 mb-8">
              {{ $t('ActivityFormsRequested.new_sponsor_concept') }}
            </div>
            <v-text-field
              v-if="group"
              v-model="group.name"
              :label="$t('ActivityForms.activity_group')"
              data-cy="confirmation-sponsor-group-field"
              density="compact"
              readonly
            />
            <v-text-field
              v-if="subgroup"
              v-model="subgroup.name"
              :label="$t('ActivityForms.activity_subgroup')"
              data-cy="confirmation-sponsor-subgroup-field"
              density="compact"
              readonly
            />
            <v-text-field
              v-model="form.name"
              :label="$t('ActivityForms.activity_name')"
              data-cy="confirmation-sponsor-activity-name-field"
              density="compact"
              readonly
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
    <template #extraActions>
      <v-btn
        color="error"
        elevation="2"
        class="ml-2"
        width="120px"
        @click="openRejectForm"
      >
        {{ $t('_global.reject') }}
      </v-btn>
    </template>
  </StepperForm>
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
  <RejectActivityRequestForm
    :open="showRejectForm"
    :activity-uid="editedActivity ? editedActivity.uid : ''"
    @close="closeRejectForm"
    @cancel="cancelRejectForm"
  />
</template>

<script>
import _isEmpty from 'lodash/isEmpty'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import StepperForm from '@/components/tools/StepperForm.vue'
import activities from '@/api/activities'
import libConstants from '@/constants/libraries'
import SentenceCaseNameField from '@/components/tools/SentenceCaseNameField.vue'
import RejectActivityRequestForm from '@/components/library/RejectActivityRequestForm.vue'

export default {
  components: {
    ConfirmDialog,
    StepperForm,
    SentenceCaseNameField,
    RejectActivityRequestForm,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    editedActivity: {
      type: Object,
      default: null,
    },
  },
  emits: ['close'],
  data() {
    return {
      activity: { activity_groupings: [] },
      form: { activity_groupings: [{}] },
      subgroup: {},
      group: {},
      steps: [
        {
          name: 'request',
          title: this.$t('ActivityFormsRequested.activity_request'),
        },
        {
          name: 'sponsor',
          title: this.$t('ActivityFormsRequested.sponsor_activity'),
        },
        {
          name: 'confirm',
          title: this.$t('ActivityFormsRequested.confirmation'),
        },
      ],
      groups: [],
      subGroups: [],
      loading: false,
      helpItems: [],
      activities: [],
      headers: [
        {
          title: this.$t('ActivityTable.activity_group'),
          key: 'activity_group.name',
        },
        {
          title: this.$t('ActivityTable.activity_subgroup'),
          key: 'activity_subgroup.name',
        },
        { title: this.$t('ActivityTable.activity'), key: 'name' },
      ],
      options: {},
      total: 0,
      filteredSubGroups: [],
      showRejectForm: false,
    }
  },
  computed: {
    title() {
      return this.editedActivity
        ? this.$t('ActivityForms.edit_activity')
        : this.$t('ActivityForms.add_activity')
    },
  },
  watch: {
    editedActivity: {
      async handler(value) {
        if (value) {
          await activities.getObject('activities', value.uid).then((resp) => {
            this.initForm(resp.data)
          })
        }
      },
      immediate: true,
    },
  },
  mounted() {
    this.getActivities()
  },
  methods: {
    initForm(editedActivity) {
      if (editedActivity) {
        this.activity = editedActivity
        this.form = JSON.parse(JSON.stringify(this.activity))
        this.form.activity_groupings = []
        if (
          !_isEmpty(this.activity) &&
          this.activity.activity_groupings.length
        ) {
          this.form.activity_groupings.push(this.activity.activity_groupings[0])
        } else {
          this.activity.activity_groupings.push({})
          this.form.activity_groupings.push({})
        }
      } else {
        this.activity = { activity_groupings: [{}] }
      }
      this.getGroups()
    },
    filterSubGroups() {
      this.subgroup = null
      if (!this.group.uid) {
        this.filteredSubGroups = []
      }
      this.filteredSubGroups = this.subGroups.filter(
        (el) =>
          el.activity_groups.find((o) => o.uid === this.group.uid) !== undefined
      )
    },
    getObserver(step) {
      return this.$refs[`observer_${step}`]
    },
    close() {
      this.$emit('close')
      this.form = { activity_groupings: [{}] }
      this.$refs.stepper.reset()
    },
    async submit() {
      this.form.library_name = libConstants.LIBRARY_SPONSOR
      this.form.activity_request_uid = this.editedActivity.uid
      if (this.subgroup) {
        this.form.activity_subgroup = this.subgroup.uid
        this.form.activity_groupings[0].activity_subgroup_uid =
          this.subgroup.uid
      }
      if (this.group) {
        this.form.activity_group = this.group.uid
        this.form.activity_groupings[0].activity_group_uid = this.group.uid
      }
      activities.createFromActivityRequest(this.form).then(
        () => {
          this.eventBusEmit('warning', {
            msg: this.$t('ActivityFormsRequested.new_concept_warning'),
          })
          this.close()
          this.$refs.stepper.loading = false
        },
        () => {
          this.$refs.form.working = false
        }
      )
    },
    openRejectForm() {
      this.showRejectForm = true
    },
    closeRejectForm() {
      this.showRejectForm = false
      this.close()
    },
    cancelRejectForm() {
      this.showRejectForm = false
    },
    async getGroups() {
      await activities.get({ page_size: 0 }, 'activity-groups').then((resp) => {
        this.groups = resp.data.items
      })
      await activities
        .get({ page_size: 0 }, 'activity-sub-groups')
        .then((resp) => {
          this.subGroups = resp.data.items
          this.subgroup = this.subGroups.find(
            (sg) =>
              sg.uid ===
              this.activity.activity_groupings[0].activity_subgroup_uid
          )
        })
      if (this.subGroups.length > 0) {
        this.group = this.groups.find(
          (sg) =>
            sg.uid === this.activity.activity_groupings[0].activity_group_uid
        )

        this.filterSubGroups()
        this.subgroup = this.subGroups.find(
          (sg) =>
            sg.uid === this.activity.activity_groupings[0].activity_subgroup_uid
        )
      }
    },
    getActivities() {
      const params = {
        page_number: this.options.page,
        page_size: this.options.itemsPerPage,
        total_count: true,
        library_name: 'Sponsor',
        filters: `{"*":{"v":["${this.form.name}"]}}`,
      }
      activities.get(params, 'activities').then((resp) => {
        const activities = []
        for (const item of resp.data.items) {
          if (item.activity_groupings.length > 0) {
            for (const grouping of item.activity_groupings) {
              activities.push({
                activity_group: {
                  name: grouping.activity_group_name,
                  uid: grouping.activity_group_uid,
                },
                activity_subgroup: {
                  name: grouping.activity_subgroup_name,
                  uid: grouping.activity_subgroup_uid,
                },
                item_key:
                  item.uid +
                  grouping.activity_group_uid +
                  grouping.activity_subgroup_uid,
                ...item,
              })
            }
          } else {
            activities.push({
              activity_group: { name: '', uid: '' },
              activity_subgroup: { name: '', uid: '' },
              item_key: item.uid,
              ...item,
            })
          }
        }
        this.activities = activities
        this.total = resp.data.total
      })
    },
  },
}
</script>
