<template>
  <StudyActivitySelectionBaseForm
    :help-items="helpItems"
    :selection="selection"
    with-delete-action
    :open="open"
    @submit="submit"
    @close="close"
    @remove="unselectItem"
  >
    <template #body>
      <v-autocomplete
        v-model="form.flowchart_group"
        :label="$t('StudyActivityForm.flowchart_group')"
        :items="flowchartGroups"
        item-title="sponsor_preferred_name"
        return-object
        clearable
        class="mt-4"
        color="nnBaseBlue"
      />
      <v-checkbox
        v-model="form.deleteSelection"
        :color="form.deleteSelection ? 'error' : ''"
      >
        <template #label>
          <span :class="{ 'error--text': form.deleteSelection }">
            {{ $t('StudyActivityBatchEditForm.delete_selection') }}
          </span>
        </template>
      </v-checkbox>
    </template>
  </StudyActivitySelectionBaseForm>
</template>

<script>
import { computed } from 'vue'
import study from '@/api/study'
import StudyActivitySelectionBaseForm from './StudyActivitySelectionBaseForm.vue'
import terms from '@/api/controlledTerminology/terms'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    StudyActivitySelectionBaseForm,
  },
  inject: ['notificationHub'],
  props: {
    selection: {
      type: Array,
      default: () => [],
    },
    open: Boolean,
  },
  emits: ['close', 'remove', 'updated'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
    }
  },
  data() {
    return {
      flowchartGroups: [],
      form: {},
      helpItems: [],
    }
  },
  mounted() {
    terms.getTermsByCodelist('flowchartGroups').then((resp) => {
      this.flowchartGroups = resp.data.items
    })
  },
  methods: {
    close() {
      this.notificationHub.clearErrors()
      this.form = {}
      this.$emit('close')
    },
    unselectItem(item) {
      this.$emit('remove', item)
    },
    async submit() {
      this.notificationHub.clearErrors()

      const data = []
      if (this.form.deleteSelection) {
        for (const item of this.selection) {
          data.push({
            method: 'DELETE',
            content: {
              study_activity_uid: item.study_activity_uid,
            },
          })
        }
      }
      if (this.form.flowchart_group || this.form.note) {
        for (const item of this.selection) {
          const content = {
            note: this.form.note,
          }
          if (this.form.flowchart_group) {
            content.soa_group_term_uid = this.form.flowchart_group.term_uid
          }
          data.push({
            method: 'PATCH',
            content: {
              study_activity_uid: item.study_activity_uid,
              content,
            },
          })
        }
      }
      if (data.length) {
        study
          .studyActivityBatchOperations(this.selectedStudy.uid, data)
          .then(() => {
            this.notificationHub.add({
              type: 'success',
              msg: this.$t('StudyActivityBatchEditForm.update_success'),
            })
            this.$emit('updated')
            this.close()
          })
      } else {
        this.close()
      }
    },
  },
}
</script>
