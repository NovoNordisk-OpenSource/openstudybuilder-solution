<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('StudyAuxiliaryDeviceForm.add_title')"
    :open="open"
    :action-label="$t('StudyAuxiliaryDeviceForm.add_title')"
    max-width="1000px"
    top-right-cancel
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col cols="12" md="8">
            <label class="v-label required">{{
              $t('StudyAuxiliaryDeviceForm.select_device')
            }}</label>
            <v-autocomplete
              v-model="selectedTermUid"
              data-cy="auxiliary-device-term"
              :items="availableTerms"
              item-title="sponsor_preferred_name"
              item-value="term_uid"
              :rules="[formRules.required]"
              clearable
              @update:model-value="onTermSelected"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12" md="4">
            <label class="v-label">{{
              $t('StudyAuxiliaryDevice.submission_value')
            }}</label>
            <v-textarea
              data-cy="auxiliary-device-submission-value"
              :model-value="selectedTermDetails.submission_value"
              disabled
              hide-details
              rows="1"
              auto-grow
            />
          </v-col>
          <v-col cols="12" md="4">
            <label class="v-label">{{
              $t('StudyAuxiliaryDevice.sponsor_preferred_name')
            }}</label>
            <v-textarea
              data-cy="auxiliary-device-sponsor-preferred-name"
              :model-value="selectedTermDetails.sponsor_preferred_name"
              disabled
              hide-details
              rows="1"
              auto-grow
            />
          </v-col>
          <v-col cols="12" md="4">
            <label class="v-label">{{
              $t('StudyAuxiliaryDevice.nci_preferred_name')
            }}</label>
            <v-textarea
              data-cy="auxiliary-device-nci-preferred-name"
              :model-value="selectedTermDetails.nci_preferred_name"
              disabled
              hide-details
              rows="1"
              auto-grow
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col cols="12" md="4">
            <label class="v-label">{{ $t('_global.definition') }}</label>
            <v-textarea
              data-cy="auxiliary-device-definition"
              :model-value="selectedTermDetails.definition"
              disabled
              hide-details
              rows="3"
              auto-grow
            />
          </v-col>
          <v-col cols="12" md="4">
            <label class="v-label">{{
              $t('StudyAuxiliaryDevice.algorithm')
            }}</label>
            <v-textarea
              data-cy="auxiliary-device-algorithm"
              :model-value="selectedTermDetails.algorithm"
              disabled
              hide-details
              rows="3"
              auto-grow
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import controlledTerminology from '@/api/controlledTerminology'
import study from '@/api/study'
import terms from '@/api/controlledTerminology/terms'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['notificationHub', 'formRules'],
  props: {
    open: Boolean,
  },
  emits: ['close'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: studiesGeneralStore.selectedStudy,
    }
  },
  data() {
    return {
      availableTerms: [],
      selectedTermUid: null,
      // term details populated on select; algorithm/definition fetched from attributes endpoint
      selectedTermDetails: {},
    }
  },
  watch: {
    // reload on every open so devices added since last time are hidden
    async open(value) {
      if (!value) return
      const [termsResp, selectedResp] = await Promise.all([
        terms.getTermsByCodelist('auxiliaryDevice', { all: true }),
        study.getStudyAuxiliaryDevices(this.selectedStudy.uid, {
          page_size: 0,
        }),
      ])
      const selected = new Set(
        selectedResp.data.items.map((item) => item.auxiliary_device_term_uid)
      )
      this.availableTerms = termsResp.data.items.filter(
        (term) => !selected.has(term.term_uid)
      )
    },
  },
  methods: {
    async onTermSelected(termUid) {
      if (!termUid) {
        this.selectedTermDetails = {}
        return
      }
      const term = this.availableTerms.find((t) => t.term_uid === termUid)
      this.selectedTermDetails = term ? { ...term } : {}
      // the study selection shows the Final attributes, so preview those
      try {
        const resp = await controlledTerminology.getCodelistTermAttributes(
          termUid,
          { status: 'Final' }
        )
        // a slower response for an earlier pick must not overwrite this one
        if (this.selectedTermUid !== termUid) return
        this.selectedTermDetails = {
          ...this.selectedTermDetails,
          nci_preferred_name: resp.data.nci_preferred_name,
          definition: resp.data.definition,
          algorithm: resp.data.algorithm,
        }
      } catch (_e) {
        // non-fatal: keep the list data (the axios interceptor still shows the error toast)
      }
    },
    close() {
      this.$emit('close')
      this.notificationHub.clearErrors()
      this.selectedTermUid = null
      this.selectedTermDetails = {}
      this.$refs.observer.reset()
    },
    async submit() {
      this.notificationHub.clearErrors()
      const data = { auxiliary_device_term_uid: this.selectedTermUid }
      study.createStudyAuxiliaryDevice(this.selectedStudy.uid, data).then(
        () => {
          this.$refs.form.working = false
          this.notificationHub.add({
            msg: this.$t('StudyAuxiliaryDeviceForm.add_success'),
          })
          this.close()
        },
        () => {
          this.$refs.form.working = false
        }
      )
    },
  },
}
</script>
