<template>
  <ConfirmDialog ref="confirm" :text-cols="5" :action-cols="6">
    <template #actions>
      <v-btn
        color="nnBaseBlue"
        rounded="xl"
        class="mr-2"
        elevation="1"
        @click="openSelectStudyDialog"
      >
        {{ $t('_global.select_study') }}
      </v-btn>
      <v-btn
        color="nnBaseBlue"
        rounded="xl"
        elevation="1"
        @click="redirectToStudyTable"
      >
        {{ $t('_global.add_study') }}
      </v-btn>
    </template>
  </ConfirmDialog>
  <v-dialog v-model="showSelectForm" persistent max-width="600px">
    <StudyQuickSelectForm
      @close="showSelectForm = false"
      @selected="goToNextUrl"
    />
  </v-dialog>
</template>

<script>
import { computed } from 'vue'
import ConfirmDialog from '@/components/tools/ConfirmDialog.vue'
import StudyQuickSelectForm from '@/components/studies/StudyQuickSelectForm.vue'
import { useAppStore } from '@/stores/app'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import generalUtils from '@/utils/generalUtils'

export default {
  components: {
    ConfirmDialog,
    StudyQuickSelectForm,
  },
  props: {
    target: {
      type: Object,
      default: undefined,
    },
  },
  setup() {
    const appStore = useAppStore()
    const studiesGeneralStore = useStudiesGeneralStore()
    return {
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
      selectedStudy: computed(() => studiesGeneralStore.selectedStudy),
    }
  },
  data() {
    return {
      items: [],
      expanded: false,
      showSelectForm: false,
      nextUrl: null,
    }
  },
  watch: {
    target(value) {
      this.redirect(value)
    },
  },
  mounted() {
    this.items = this.studies
  },
  methods: {
    startFrom(arr, idx) {
      return arr.slice(idx)
    },
    async redirect(target) {
      if (
        target.subitem &&
        target.subitem.studyRequired &&
        !this.selectedStudy
      ) {
        const options = {
          type: 'warning',
        }
        this.nextUrl = target.subitem.url
        await this.$refs.confirm.open(
          this.$t('_global.no_study_selected'),
          options
        )
      } else {
        target.subitem
          ? this.$router.push(target.subitem.url)
          : this.$router.push(target.item.url)
      }
      if (Object.prototype.hasOwnProperty.call(target.item, 'meta')) {
        const breads = target.item.meta.breadcrumb
        this.addBreadcrumbsLevel(breads[0].name)
        this.addBreadcrumbsLevel(breads[1].name)
      } else {
        this.addBreadcrumbsLevel(target.item.title, target.item.url, 1)
        if (target.subitem !== undefined) {
          this.addBreadcrumbsLevel(target.subitem.title, target.subitem.url, 2)
        }
      }
    },
    openSelectStudyDialog() {
      this.$refs.confirm.cancel()
      this.showSelectForm = true
    },
    redirectToStudyTable() {
      this.$refs.confirm.cancel()
      this.$router.push({ name: 'SelectOrAddStudy' })
    },
    goToNextUrl() {
      this.nextUrl.params = {
        study_id: generalUtils.extractStudyUidFromLocalStorage(),
      }
      const resolved = this.$router.resolve(this.nextUrl)
      document.location.href = resolved.href
    },
  },
}
</script>
