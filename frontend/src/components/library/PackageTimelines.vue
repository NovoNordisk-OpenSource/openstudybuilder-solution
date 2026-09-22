<template>
  <slot v-if="_isEmpty(packages)" name="empty" />
  <v-tabs v-if="!_isEmpty(packages)" v-model="tab" bg-color="dfltBackground">
    <v-tab
      v-for="(pckgs, catalogue) in packages"
      :key="catalogue"
      :value="catalogue"
      :data-cy="catalogue"
    >
      {{ catalogue }}
    </v-tab>
  </v-tabs>
  <v-window v-if="!_isEmpty(packages)" v-model="tab">
    <v-window-item
      v-for="(cataloguePackages, catalogue) in packages"
      :key="`${catalogue}-${tabKeys[catalogue]}`"
      :value="catalogue"
    >
      <PackageTimeline
        :ref="(el) => (timelineRefs[catalogue] = el)"
        :catalogue-packages="cataloguePackages"
        :with-add-button="sponsor"
        @package-changed="(pkg) => emit('packageChanged', catalogue, pkg)"
        @add-package="emit('addPackage')"
      >
        <template v-for="(_, slot) of $slots" #[slot]="scope">
          <slot :name="slot" v-bind="scope" :catalogue_name="catalogue" />
        </template>
      </PackageTimeline>
    </v-window-item>
  </v-window>
</template>

<script setup>
import { nextTick, ref, onMounted, watch } from 'vue'
import { useCtCataloguesStore } from '@/stores/library-ctcatalogues'
import { useTabKeys } from '@/composables/tabKeys'
import { DateTime } from 'luxon'
import _isEmpty from 'lodash/isEmpty'
import controlledTerminology from '@/api/controlledTerminology'
import PackageTimeline from './PackageTimeline.vue'

const props = defineProps({
  catalogueName: {
    type: String,
    default: null,
    required: false,
  },
  packageName: {
    type: String,
    default: null,
    required: false,
  },
  sponsor: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['addPackage', 'catalogueChanged', 'packageChanged'])
const ctCataloguesStore = useCtCataloguesStore()
const { tabKeys, updateTabKey } = useTabKeys()

const packages = ref({})
const tab = ref(null)
const timelineRefs = ref({})

watch(tab, (newValue, oldValue) => {
  if (oldValue) {
    emit('catalogueChanged', newValue)
  }
  if (newValue !== props.catalogueName) {
    ctCataloguesStore.currentCataloguePage = 1
  }
  updateTabKey(newValue)
  nextTick(() => {
    if (timelineRefs.value[newValue]) {
      timelineRefs.value[newValue].restorePackage()
    }
  })
})

function fetchPackages() {
  const endpoint = props.sponsor
    ? controlledTerminology.getSponsorPackages
    : controlledTerminology.getPackages
  endpoint().then((resp) => {
    packages.value = sortPackages(resp.data)
    if (props.catalogueName) {
      tab.value = props.catalogueName
    } else if (!_isEmpty(packages.value)) {
      tab.value = Object.keys(packages.value)[0]
    }
  })
}

onMounted(() => {
  fetchPackages()
})

function sortPackages(packages) {
  const result = {}
  packages.forEach((pkg) => {
    if (result[pkg.catalogue_name] === undefined) {
      result[pkg.catalogue_name] = []
    }
    const date = DateTime.fromISO(pkg.effective_date).toJSDate()
    result[pkg.catalogue_name].push({
      date,
      name: pkg.name,
      selectedPackage: null,
    })
  })
  for (const catalogue in result) {
    result[catalogue].sort((a, b) => {
      return b.date - a.date
    })
  }
  return result
}

defineExpose({
  packages,
  fetchPackages,
})
</script>
