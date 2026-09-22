<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('ActivityFormsRequested.reject_activity')"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col>
            <v-textarea
              v-model="form.reason_for_rejecting"
              :label="$t('ActivityFormsRequested.rejecting_reason')"
              clearable
              auto-grow
              rows="3"
              :rules="[
                formRules.required,
                (value) => formRules.max(value, 200),
              ]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.contact_person"
              :label="$t('ActivityFormsRequested.contact')"
              clearable
              :rules="[formRules.required, (value) => formRules.max(value, 5)]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import activities from '@/api/activities'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import { useFormStore } from '@/stores/form'

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['notificationHub', 'formRules'],
  props: {
    activityUid: {
      type: String,
      default: null,
    },
    open: Boolean,
  },
  emits: ['close', 'cancel'],
  setup() {
    const formStore = useFormStore()
    return {
      formStore,
    }
  },
  data() {
    return {
      form: {},
    }
  },
  methods: {
    submit() {
      this.notificationHub.clearErrors()

      activities
        .rejectActivityRequest(this.activityUid, this.form)
        .then(() => {
          this.notificationHub.add({
            msg: this.$t('ActivityFormsRequested.activity_rejected'),
          })
          this.close()
        })
        .catch(() => {
          this.$refs.form.working = false
        })
    },
    cancel() {
      this.$emit('cancel')
      this.form = {}
    },
    close() {
      this.$emit('close')
      this.notificationHub.clearErrors()
      this.form = {}
    },
  },
}
</script>
