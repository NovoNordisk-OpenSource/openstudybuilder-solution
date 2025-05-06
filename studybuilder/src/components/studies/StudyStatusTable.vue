<template>
  <NNTable
    :headers="headers"
    :items="items"
    column-data-resource="studies"
    hide-default-switches
    hide-export-button
    disable-filtering
    :items-length="total"
    @filter="fetchItems"
  >
    <template #actions="">
      <v-btn
        v-if="
          studiesGeneralStore.selectedStudy.current_metadata.version_metadata
            .study_status === 'DRAFT' &&
          !studiesGeneralStore.selectedStudy.study_parent_part
        "
        size="small"
        color="red"
        :title="$t('_global.lock')"
        data-cy="lock-study"
        :disabled="!checkPermission($roles.STUDY_WRITE)"
        icon="mdi-lock-outline"
        :loading="loading"
        @click.stop="lockStudy"
      />
      <v-btn
        v-if="
          studiesGeneralStore.selectedStudy.current_metadata.version_metadata
            .study_status === 'DRAFT' &&
          !studiesGeneralStore.selectedStudy.study_parent_part
        "
        class="ml-2"
        size="small"
        variant="outlined"
        color="nnBaseBlue"
        :title="$t('_global.release')"
        data-cy="release-study"
        :disabled="!checkPermission($roles.STUDY_WRITE)"
        icon="mdi-share-variant"
        :loading="loading"
        @click.stop="releaseStudy"
      />
      <v-btn
        v-if="
          studiesGeneralStore.selectedStudy.current_metadata.version_metadata
            .study_status === 'LOCKED' &&
          !studiesGeneralStore.selectedStudy.study_parent_part
        "
        size="small"
        color="green"
        :title="$t('_global.unlock')"
        data-cy="unlock-study"
        :disabled="!checkPermission($roles.STUDY_WRITE)"
        icon="mdi-lock-open-outline"
        :loading="loading"
        @click.stop="unlockStudy"
      />
    </template>
    <template #[`item.actions`]="{ item }">
      <ActionsMenu
        v-if="checkIfSelectable(item)"
        :actions="actions"
        :item="item"
      />
    </template>
    <template
      #[`item.current_metadata.version_metadata.study_status`]="{ item }"
    >
      <StatusChip
        :status="item.current_metadata.version_metadata.study_status"
        :outlined="false"
      />
    </template>
    <template
      #[`item.current_metadata.version_metadata.version_timestamp`]="{ item }"
    >
      {{
        $filters.date(item.current_metadata.version_metadata.version_timestamp)
      }}
    </template>
  </NNTable>
  <StudyStatusForm
    :action="statusAction"
    :open="showStatusForm"
    @close="closeStatusForm"
    @status-changed="refreshData"
  />
  <ConfirmDialog ref="confirm" :text-cols="6" :action-cols="5" />
</template>

<script>
import api from '@/api/study'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import filteringParameters from '@/utils/filteringParameters'
import NNTable from '@/components/tools/NNTable.vue'
import StatusChip from '@/components/tools/StatusChip.vue'
import StudyStatusForm from './StudyStatusForm.vue'
import ActionsMenu from '@/components/tools/ActionsMenu.vue'
import { useAccessGuard } from '@/composables/accessGuard'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    ConfirmDialog,
    NNTable,
    StatusChip,
    StudyStatusForm,
    ActionsMenu,
  },
  inject: ['eventBusEmit'],
  setup() {
    const accessGuard = useAccessGuard()
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      studiesGeneralStore,
      ...accessGuard,
    }
  },
  data() {
    return {
      editedStudy: null,
      headers: [
        { title: '', key: 'actions', width: '1%' },
        {
          title: this.$t('Study.status'),
          key: 'current_metadata.version_metadata.study_status',
        },
        {
          title: this.$t('_global.version'),
          key: 'current_metadata.version_metadata.version_number',
        },
        {
          title: this.$t('Study.release_description'),
          key: 'current_metadata.version_metadata.version_description',
        },
        {
          title: this.$t('_global.modified'),
          key: 'current_metadata.version_metadata.version_timestamp',
        },
        {
          title: this.$t('_global.modified_by'),
          key: 'current_metadata.version_metadata.version_author',
        },
      ],
      loading: false,
      lockedHistory: [],
      showStatusForm: false,
      statusAction: null,
      items: [],
      total: 0,
      actions: [
        {
          label: this.$t('StudyTable.select'),
          icon: 'mdi-check-circle-outline',
          iconColor: 'primary',
          click: this.selectStudyVersion,
        },
      ],
    }
  },
  methods: {
    checkIfSelectable(studyVersion) {
      return (
        studyVersion.current_metadata.version_metadata.version_number !==
          this.studiesGeneralStore.selectedStudyVersion ||
        studyVersion.current_metadata.version_metadata.study_status !==
          this.studiesGeneralStore.selectedStudy.current_metadata
            .version_metadata.study_status
      )
    },
    selectStudyVersion(studyVersion) {
      this.studiesGeneralStore.selectStudy(studyVersion, true)
    },
    closeEditForm() {
      this.showEditForm = false
      this.fetchItems()
    },
    closeStatusForm() {
      this.loading = false
      this.showStatusForm = false
    },
    fetchItems(filters, options, filtersUpdated) {
      const params = filteringParameters.prepareParameters(
        options,
        filters,
        filtersUpdated
      )
      api
        .getStudySnapshotHistory(
          this.studiesGeneralStore.selectedStudy.uid,
          params
        )
        .then((resp) => {
          this.items = resp.data.items
          this.total = resp.data.total
        })
    },
    releaseStudy() {
      this.loading = true
      this.statusAction = 'release'
      this.showStatusForm = true
    },
    lockStudy() {
      this.loading = true
      this.statusAction = 'lock'
      this.showStatusForm = true
    },
    async refreshData() {
      this.fetchItems()
    },
    async unlockStudy() {
      this.loading = true
      const resp = await api.unlockStudy(
        this.studiesGeneralStore.selectedStudy.uid
      )
      this.studiesGeneralStore.selectStudy(resp.data)
      this.eventBusEmit('notification', {
        msg: this.$t('StudyStatusTable.unlock_success'),
        type: 'success',
      })
      this.loading = false
      this.fetchItems()
    },
  },
}
</script>
