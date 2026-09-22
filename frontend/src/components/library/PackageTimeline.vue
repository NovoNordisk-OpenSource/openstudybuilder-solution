<template>
  <v-row no-gutters style="flex-wrap: nowrap">
    <v-col
      cols="1"
      class="flex-grow-1 flex-shrink-0"
      style="min-width: 100px; max-width: 200px"
    >
      <div v-if="withAddButton" class="text-center">
        <v-btn
          size="small"
          variant="outlined"
          color="nnBaseBlue"
          class="mb-2"
          icon="mdi-plus"
          :title="$t('PackageTimeline.add_label')"
          @click="emit('addPackage')"
        />
      </div>
      <v-timeline
        data-cy="timeline"
        density="compact"
        class="mr-4"
        align="start"
      >
        <v-timeline-item
          v-for="(pkg, index) in cataloguePackages"
          :key="index"
          :dot-color="
            selectedPackage && pkg.name === selectedPackage.name
              ? 'primary'
              : 'grey'
          "
          size="small"
        >
          <v-btn
            variant="text"
            :color="
              selectedPackage && selectedPackage.name === pkg.name
                ? 'primary'
                : 'default'
            "
            data-cy="timeline-date"
            @click.stop="selectPackage(pkg, true)"
          >
            {{ displayDate(pkg.date) }}
          </v-btn>
        </v-timeline-item>
      </v-timeline>
    </v-col>
    <v-col
      cols="10"
      style="min-width: 100px; max-width: 100%"
      class="flex-grow-1 flex-shrink-0 pb-4"
    >
      <slot :selected-package="selectedPackage" />
    </v-col>
  </v-row>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { onMounted } from 'vue'
import { ref } from 'vue'
import { DateTime } from 'luxon'

const props = defineProps({
  cataloguePackages: {
    type: Array,
    default: null,
  },
  withAddButton: {
    type: Boolean,
    default: false,
  },
})
const emit = defineEmits(['packageChanged', 'addPackage'])
const route = useRoute()

const selectedPackage = ref()

function displayDate(date) {
  return DateTime.fromJSDate(date).toISODate()
}

function selectPackage(pkg, sendEvent) {
  if (sendEvent) {
    emit('packageChanged', pkg)
  }
  selectedPackage.value = pkg
}

function restorePackage() {
  if (route.params.package_name) {
    for (const pkg of props.cataloguePackages) {
      if (pkg.name === route.params.package_name) {
        selectPackage(pkg)
        return
      }
    }
  }
  selectPackage(props.cataloguePackages[0], true)
}

onMounted(() => {
  if (!route.params.package_name) {
    selectPackage(props.cataloguePackages[0], true)
  } else {
    for (const pkg of props.cataloguePackages) {
      if (pkg.name === route.params.package_name) {
        selectPackage(pkg)
        break
      }
    }
  }
})

defineExpose({
  restorePackage,
})
</script>
