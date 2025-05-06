<template>
  <div>
    <NNTable
      :headers="headers"
      :items="formatedStudyCompoudDosings"
      :items-length="studiesCompoundsStore.studyCompoundDosingTotal"
      item-value="study_compound_dosing_uid"
      export-object-label="StudyCompoundDosings"
      :export-data-url="exportDataUrl"
      column-data-resource="study-compound-dosings"
      :history-data-fetcher="fetchCompoundDosingsHistory"
      :history-title="$t('StudyCompoundDosingTable.global_history_title')"
    >
      <template #actions="">
        <v-btn
          data-cy="add-study-compound-dosing"
          class="ml-2"
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          :title="$t('StudyCompoundForm.add_title')"
          :disabled="
            !checkPermission($roles.STUDY_WRITE) ||
            selectedStudyVersion !== null
          "
          icon="mdi-plus"
          @click.stop="showForm = true"
        />
      </template>
      <template #[`item.actions`]="{ item }">
        <ActionsMenu :actions="actions" :item="item" />
      </template>
    </NNTable>
    <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
    <v-dialog
      v-model="showForm"
      persistent
      fullscreen
      content-class="fullscreen-dialog"
    >
      <CompoundDosingForm
        :study-compound-dosing="selectedStudyCompoundDosing"
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
        :title="studyCompoundDosingHistoryTitle"
        :headers="headers"
        :items="compoundDosingHistoryItems"
        @close="closeHistory"
      />
    </v-dialog>
  </div>
</template>

<script>
import { computed } from 'vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import CompoundDosingForm from './CompoundDosingForm.vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import HistoryTable from '@/components/tools/HistoryTable.vue'
import dataFormating from '@/utils/dataFormating'
import NNTable from '@/components/tools/NNTable.vue'
import study from '@/api/study'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesCompoundsStore } from '@/stores/studies-compounds'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    ActionsMenu,
    CompoundDosingForm,
    ConfirmDialog,
    HistoryTable,
    NNTable,
  },
  inject: ['eventBusEmit'],
  setup() {
    const accessGuard = useAccessGuard()
    const studiesCompoundsStore = useStudiesCompoundsStore()
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
      selectedStudyVersion: computed(
        () => studiesGeneralStore.selectedStudyVersion
      ),
      studiesCompoundsStore,
      ...accessGuard,
    }
  },
  data() {
    return {
      actions: [
        {
          label: this.$t('_global.edit'),
          icon: 'mdi-pencil-outline',
          iconColor: 'primary',
          condition: () => !this.selectedStudyVersion,
          click: this.editStudyCompoundDosing,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.delete'),
          icon: 'mdi-delete-outline',
          iconColor: 'error',
          condition: () => !this.selectedStudyVersion,
          click: this.deleteStudyCompoundDosing,
          accessRole: this.$roles.STUDY_WRITE,
        },
        {
          label: this.$t('_global.history'),
          icon: 'mdi-history',
          click: this.openHistory,
        },
      ],
      headers: [
        { title: '', key: 'actions', width: '1%' },
        { title: '#', key: 'order' },
        {
          title: this.$t('StudyCompoundDosingTable.element'),
          key: 'study_element.name',
        },
        {
          title: this.$t('StudyCompoundDosingTable.compound'),
          key: 'study_compound.compound.name',
        },
        {
          title: this.$t('StudyCompoundDosingTable.compound_alias'),
          key: 'study_compound.compound_alias.name',
        },
        {
          title: this.$t('StudyCompoundDosingTable.preferred_alias'),
          key: 'study_compound.compound_alias.is_preferred_synonym',
        },
        {
          title: this.$t('StudyCompoundDosingTable.dose_value'),
          key: 'dose_value',
        },
        {
          title: this.$t('StudyCompoundDosingTable.dose_frequency'),
          key: 'dose_frequency.name',
        },
      ],
      selectedStudyCompoundDosing: null,
      showForm: false,
      showHistory: false,
      compoundDosingHistoryItems: [],
    }
  },
  computed: {
    exportDataUrl() {
      return `studies/${this.selectedStudy.uid}/study-compound-dosings`
    },
    formatedStudyCompoudDosings() {
      return this.transformItems(
        this.studiesCompoundsStore.studyCompoundDosings
      )
    },
    studyCompoundDosingHistoryTitle() {
      if (this.selectedStudyCompoundDosing) {
        return this.$t(
          'StudyCompoundDosingTable.study_compound_dosing_history_title',
          {
            studyCompoundDosingUid:
              this.selectedStudyCompoundDosing.study_compound_dosing_uid,
          }
        )
      }
      return ''
    },
  },
  mounted() {
    this.studiesCompoundsStore.fetchStudyCompoundDosings(this.selectedStudy.uid)
  },
  methods: {
    async deleteStudyCompoundDosing(studyCompoundDosing) {
      const options = { type: 'warning' }
      const compound = studyCompoundDosing.study_compound.compound_alias.name
      const element = studyCompoundDosing.study_element.name
      const msg = this.$t('StudyCompoundDosingTable.confirm_delete', {
        compound,
        element,
      })
      if (!(await this.$refs.confirm.open(msg, options))) {
        return
      }
      this.studiesCompoundsStore
        .deleteStudyCompoundDosing(
          this.selectedStudy.uid,
          studyCompoundDosing.study_compound_dosing_uid
        )
        .then(() => {
          this.eventBusEmit('notification', {
            msg: this.$t('StudyCompoundDosingTable.delete_success'),
          })
        })
    },
    editStudyCompoundDosing(studyCompoundDosing) {
      this.selectedStudyCompoundDosing = studyCompoundDosing
      this.showForm = true
    },
    async fetchCompoundDosingsHistory() {
      const resp = await study.getStudyCompoundDosingsAuditTrail(
        this.selectedStudy.uid
      )
      return this.transformItems(resp.data)
    },
    async openHistory(studyCompoundDosing) {
      this.selectedStudyCompoundDosing = studyCompoundDosing
      const resp = await study.getStudyCompoundDosingAuditTrail(
        this.selectedStudy.uid,
        studyCompoundDosing.study_compound_dosing_uid
      )
      this.compoundDosingHistoryItems = this.transformItems(resp.data)
      this.showHistory = true
    },
    closeHistory() {
      this.selectedStudyCompoundDosing = null
      this.showHistory = false
    },
    closeForm() {
      this.showForm = false
      this.selectedStudyCompoundDosing = null
    },
    transformItems(items) {
      const result = []
      for (const item of items) {
        const newItem = { ...item }
        if (newItem.study_compound.compound_alias) {
          newItem.study_compound.compound_alias.is_preferred_synonym =
            dataFormating.yesno(
              newItem.study_compound.compound_alias.is_preferred_synonym
            )
        }
        if (newItem.dose_value) {
          newItem.dose_value = dataFormating.numericValue(newItem.dose_value)
        }
        result.push(newItem)
      }
      return result
    },
  },
}
</script>
