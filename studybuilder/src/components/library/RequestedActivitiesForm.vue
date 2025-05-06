<template>
  <SimpleFormDialog
    ref="form"
    :title="title"
    :help-items="helpItems"
    :open="open"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row data-cy="requestedform-activity-group-class">
          <v-col>
            <v-autocomplete
              v-model="form.activity_groupings[0].activity_group_uid"
              :label="$t('ActivityForms.activity_group')"
              data-cy="requestedform-activity-group-dropdown"
              :items="activitiesStore.activityGroups"
              item-title="name"
              item-value="uid"
              :rules="[formRules.required]"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row data-cy="requestedform-activity-subgroup-class">
          <v-col>
            <v-autocomplete
              v-model="form.activity_groupings[0].activity_subgroup_uid"
              :label="$t('ActivityForms.activity_subgroup')"
              data-cy="requestedform-activity-subgroup-dropdown"
              :items="filteredSubGroups"
              item-title="name"
              item-value="uid"
              density="compact"
              :rules="[formRules.required]"
              clearable
              :disabled="
                form.activity_groupings[0].activity_group_uid ? false : true
              "
            />
          </v-col>
        </v-row>
        <v-row data-cy="requestedform-activity-name-class">
          <v-col>
            <v-text-field
              v-model="form.name"
              :label="$t('ActivityForms.activity_name')"
              data-cy="requestedform-activity-name-field"
              density="compact"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <SentenceCaseNameField
          v-model="form.name_sentence_case"
          :name="form.name"
        />
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.abbreviation"
              :label="$t('ActivityFormsRequested.abbreviation')"
              data-cy="requestedform-abbreviation-field"
              density="compact"
              clearable
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-textarea
              v-model="form.definition"
              :label="$t('ActivityFormsRequested.definition')"
              data-cy="requestedform-definition-field"
              density="compact"
              clearable
              auto-grow
              rows="1"
            />
          </v-col>
        </v-row>
        <v-row data-cy="requestedform-rationale-for-request-class">
          <v-col>
            <v-textarea
              v-model="form.request_rationale"
              :label="$t('ActivityFormsRequested.rationale_for_request')"
              data-cy="requestedform-rationale-for-request-field"
              density="compact"
              clearable
              auto-grow
              rows="1"
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row v-if="isEdit">
          <v-col>
            <label class="v-label">{{
              $t('ActivityForms.reason_for_change')
            }}</label>
            <v-textarea
              v-model="form.change_description"
              data-cy="requestedform-change-description-field"
              density="compact"
              clearable
              auto-grow
              rows="1"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import _isEmpty from 'lodash/isEmpty'
import activities from '@/api/activities'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import libConstants from '@/constants/libraries'
import SentenceCaseNameField from '@/components/tools/SentenceCaseNameField.vue'
import { useFormStore } from '@/stores/form'
import { useLibraryActivitiesStore } from '@/stores/library-activities'

export default {
  components: {
    SimpleFormDialog,
    SentenceCaseNameField,
  },
  inject: ['eventBusEmit', 'formRules'],
  props: {
    editedActivity: {
      type: Object,
      default: null,
    },
    open: Boolean,
  },
  emits: ['close'],
  setup() {
    const formStore = useFormStore()
    const activitiesStore = useLibraryActivitiesStore()
    return {
      formStore,
      activitiesStore,
    }
  },
  data() {
    return {
      form: {
        activity_groupings: [{}],
      },
      libraries: [],
      helpItems: [],
    }
  },
  computed: {
    isEdit() {
      return !_isEmpty(this.editedActivity)
    },
    title() {
      return !_isEmpty(this.editedActivity)
        ? this.$t('ActivityForms.edit_activity_request')
        : this.$t('ActivityForms.add_activity_request')
    },
    filteredSubGroups() {
      return this.activitiesStore.activitySubGroups.filter(
        (el) =>
          el.activity_groups.find(
            (o) => o.uid === this.form.activity_groupings[0].activity_group_uid
          ) !== undefined
      )
    },
  },
  watch: {
    editedActivity: {
      handler(value) {
        if (value) {
          activities.getObject('activities', value.uid).then((resp) => {
            this.initForm(resp.data)
          })
        } else {
          this.form = {
            activity_groupings: [{}],
          }
          this.formStore.reset()
        }
      },
      immediate: true,
    },
  },
  mounted() {
    if (this.isEdit) {
      this.initForm(this.editedActivity)
    }
  },
  methods: {
    initForm(value) {
      this.form = JSON.parse(JSON.stringify(value))
      this.formStore.save(this.form)
    },
    async cancel() {
      if (this.formStore.isEmpty || this.formStore.isEqual(this.form)) {
        this.close()
      } else {
        const options = {
          type: 'warning',
          cancelLabel: this.$t('_global.cancel'),
          agreeLabel: this.$t('_global.continue'),
        }
        if (
          await this.$refs.form.confirm(
            this.$t('_global.cancel_changes'),
            options
          )
        ) {
          this.close()
        }
      }
    },
    close() {
      this.$emit('close')
      this.form = { activity_groupings: [{}] }
      this.formStore.reset()
      this.$refs.observer.reset()
    },
    async submit() {
      this.form.library_name = libConstants.LIBRARY_REQUESTED
      this.form.is_request_final = true
      if (!this.isEdit) {
        activities.create(this.form, 'activities').then(
          () => {
            this.eventBusEmit('notification', {
              msg: this.$t('ActivityForms.activity_created'),
            })
            this.close()
          },
          () => {
            this.$refs.form.working = false
          }
        )
      } else {
        activities
          .update(this.editedActivity.uid, this.form, {}, 'activities')
          .then(
            () => {
              this.eventBusEmit('notification', {
                msg: this.$t('ActivityForms.activity_updated'),
              })
              this.close()
            },
            () => {
              this.$refs.form.working = false
            }
          )
      }
    },
  },
}
</script>
