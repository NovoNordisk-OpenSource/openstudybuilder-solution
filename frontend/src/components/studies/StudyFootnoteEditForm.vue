<template>
  <StudySelectionEditForm
    v-if="editedObject"
    ref="form"
    :title="$t('StudyFootnoteEditForm.title')"
    :study-selection="editedObject"
    :template="template"
    :library-name="library"
    object-type="footnote"
    :open="open"
    :get-object-from-selection="(selection) => selection.footnote"
    :prepare-template-payload-func="prepareTemplatePayload"
    @init-form="initForm"
    @submit="submit"
    @close="close"
  >
    <template #formFields="{}">
      <p class="mt-6 text-secondary text-headline-small">
        {{ $t('StudyFootnoteEditForm.linked_items') }}
      </p>
      <v-row>
        <v-col cols="12">
          <v-text-field
            v-if="referencedSoAGroups.length > 0"
            v-model="referencedSoAGroups"
            :label="$t('StudyFootnoteEditForm.ref_soa_groups')"
            disabled
            readonly
          />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <v-text-field
            v-if="referencedActivities.length > 0"
            v-model="referencedActivities"
            :label="$t('StudyFootnoteEditForm.ref_activities')"
            disabled
            readonly
          />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <v-text-field
            v-if="referencedEpochsAndVisits.length > 0"
            v-model="referencedEpochsAndVisits"
            :label="$t('StudyFootnoteEditForm.ref_epochs_visits')"
            disabled
            readonly
          />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12">
          <v-text-field
            v-if="referencedSchedules.length > 0"
            v-model="referencedSchedules"
            :label="$t('StudyFootnoteEditForm.ref_schedules')"
            disabled
            readonly
          />
        </v-col>
      </v-row>
    </template>
  </StudySelectionEditForm>
</template>

<script>
import { computed } from 'vue'
import constants from '@/constants/libraries'
import _isEmpty from 'lodash/isEmpty'
import formUtils from '@/utils/forms'
import study from '@/api/study'
import StudySelectionEditForm from './StudySelectionEditForm.vue'
import terms from '@/api/controlledTerminology/terms'
import footnoteConstants from '@/constants/footnotes'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import { useFootnotesStore } from '@/stores/studies-footnotes'

export default {
  components: {
    StudySelectionEditForm,
  },
  inject: ['notificationHub'],
  props: {
    studyFootnote: {
      type: Object,
      default: undefined,
    },
    open: Boolean,
  },
  emits: ['close', 'enableFootnoteMode', 'updated'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    const footnotesStore = useFootnotesStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      footnotesStore,
    }
  },
  data() {
    return {
      editedObject: {},
      referencedSoAGroups: [],
      referencedActivities: [],
      referencedEpochsAndVisits: [],
      referencedSchedules: [],
    }
  },
  computed: {
    template() {
      return this.editedObject.footnote
        ? {
            uid: this.editedObject.footnote.template_uid,
            name: this.editedObject.footnote.template_name,
          }
        : this.editedObject.template
    },
    library() {
      if (!this.studyFootnote) return null
      return this.studyFootnote.footnote
        ? this.studyFootnote.footnote.library_name
        : this.studyFootnote.template?.library_name
    },
  },
  watch: {
    studyFootnote: {
      handler: function (value) {
        if (!_isEmpty(value)) {
          study
            .getStudyFootnote(this.selectedStudy.uid, this.studyFootnote.uid)
            .then((resp) => {
              this.editedObject = resp.data
            })
        }
      },
      immediate: true,
    },
  },
  mounted() {
    terms.getTermsByCodelist('footnoteTypes').then((resp) => {
      for (const type of resp.data.items) {
        if (
          type.sponsor_preferred_name === footnoteConstants.FOOTNOTE_TYPE_SOA
        ) {
          this.footnoteType = type
          break
        }
      }
    })
  },
  methods: {
    initForm(form) {
      this.originalForm = JSON.parse(JSON.stringify(form))
      this.referencedActivities = []
      this.referencedEpochsAndVisits = []
      this.studyFootnote.referenced_items.forEach((item) => {
        if (['StudySoAGroup'].indexOf(item.item_type) > -1) {
          this.referencedSoAGroups.push(item.item_name)
        } else if (
          [
            'StudyActivity',
            'StudyActivityGroup',
            'StudyActivitySubGroup',
          ].indexOf(item.item_type) > -1
        ) {
          this.referencedActivities.push(item.item_name)
        } else if (['StudyVisit', 'StudyEpoch'].indexOf(item.item_type) > -1) {
          this.referencedEpochsAndVisits.push(item.item_name)
        } else if (['StudyActivitySchedule'].indexOf(item.item_type) > -1) {
          this.referencedSchedules.push(item.item_name)
        }
      })
      this.referencedActivities = this.removeDuplicates(
        this.referencedActivities
      ).join(', ')
      this.referencedSoAGroups = this.removeDuplicates(
        this.referencedSoAGroups
      ).join(', ')
      this.referencedEpochsAndVisits = this.referencedEpochsAndVisits.join(', ')
      this.referencedSchedules = this.referencedSchedules.join(', ')
    },
    removeDuplicates(arr) {
      return arr.filter((item, index, self) => {
        return self.indexOf(item) === index
      })
    },
    prepareTemplatePayload(data) {
      data.type_uid = this.footnoteType.term_uid
    },
    async submit(newTemplate, form, parameters) {
      this.notificationHub.clearErrors()

      const payload = formUtils.getDifferences(this.originalForm, form)
      payload.parameters = parameters
      if (_isEmpty(payload) && !newTemplate) {
        this.notificationHub.add({
          msg: this.$t('_global.no_changes'),
          type: 'info',
        })
        this.$refs.form.close()
        return
      }
      const args = {
        studyUid: this.selectedStudy.uid,
        studyFootnoteUid: this.editedObject.uid,
        form: payload,
        library: {
          name: constants.LIBRARY_USER_DEFINED,
        },
      }
      if (newTemplate) {
        args.template = newTemplate
      } else {
        args.template = this.template
      }
      try {
        await this.footnotesStore.updateStudyFootnote(args)
        this.notificationHub.add({
          msg: this.$t('StudyFootnoteEditForm.update_success'),
        })
        this.$emit('updated')
        this.$refs.form.close()
      } catch (error) {
        console.error('Error updating footnote:', error)
      } finally {
        this.$refs.form.$refs.form.working = false
      }
    },
    close() {
      this.notificationHub.clearErrors()
      this.editedObject = {}
      this.referencedSoAGroups = []
      this.referencedActivities = []
      this.referencedEpochsAndVisits = []
      this.referencedSchedules = []
      this.$emit('close')
    },
  },
}
</script>
