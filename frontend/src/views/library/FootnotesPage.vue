<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('FootnotesView.title') }}
      <HelpButton :help-text="$t('_help.FootnotesTable.general')" />
    </div>
    <v-tabs v-model="tab" bg-color="white">
      <v-tab
        v-for="type in footnoteTypes"
        :key="type.term_uid"
        :value="type.sponsor_preferred_name"
      >
        {{ type.sponsor_preferred_name }}
      </v-tab>
    </v-tabs>
    <v-window v-model="tab">
      <v-window-item
        v-for="type in footnoteTypes"
        :key="type.term_uid"
        :value="type.sponsor_preferred_name"
      >
        <FootnoteTable :key="type.refreshKey" :footnote-type="type" />
      </v-window-item>
    </v-window>
  </div>
</template>

<script>
import FootnoteTable from '@/components/library/FootnoteTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'
import terms from '@/api/controlledTerminology/terms'
import { useAppStore } from '@/stores/app'

export default {
  components: {
    FootnoteTable,
    HelpButton,
  },
  setup() {
    const appStore = useAppStore()
    return {
      addBreadcrumbsLevel: appStore.addBreadcrumbsLevel,
    }
  },
  data() {
    return {
      footnoteTypes: [],
      tab: 0,
    }
  },
  watch: {
    tab(newValue) {
      for (const type of this.footnoteTypes) {
        if (type.sponsor_preferred_name === newValue) {
          type.refreshKey++
          break
        }
      }
      this.$router.push({
        name: 'FootnoteInstances',
        params: { tab: newValue },
      })
      this.addBreadcrumbsLevel(newValue, undefined, 3, true)
    },
  },
  mounted() {
    terms.getTermsByCodelist('footnoteTypes').then((resp) => {
      this.footnoteTypes = resp.data.items.map((item) => {
        return { ...item, refreshKey: 1 }
      })
      this.tab =
        this.$route.params.tab || this.footnoteTypes[0].sponsor_preferred_name
    })
  },
}
</script>
