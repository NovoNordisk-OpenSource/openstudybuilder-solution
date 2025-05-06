<template>
  <div class="fullscreen-bg">
    <h1>{{ $t('_global.library') }}</h1>
    <p>
      {{ $t('Library.description_top_before') }}
      <strong>{{ $t('_global.library') }}</strong>
      {{ $t('Library.description_top_after') }}
    </p>
    <p>{{ $t('Library.description_bottom') }}</p>
    <v-row data-cy="tiles-box" class="mt-6 justify-center box-container">
      <v-col
        v-for="item in startFrom(appStore.libraryMenu.items, 1)"
        :key="item.title"
        cols="8"
        xs="4"
        sm="4"
        md="3"
        lg="3"
        class="item"
        :data-cy="item.title"
      >
        <div :id="item.id" class="text-white item-content">
          <v-menu location="bottom" offset-y>
            <template #activator="{ props }">
              <div class="d-flex align-center pa-1">
                <v-icon size="large" color="white">
                  {{ item.icon }}
                </v-icon>
                <span class="mx-2 text-h6">{{ item.title }}</span>
                <v-spacer />
                <v-btn
                  v-if="item.children"
                  data-cy="dropdown-button"
                  icon="mdi-menu"
                  color="white"
                  variant="text"
                  v-bind="props"
                />
              </div>
            </template>
            <v-list>
              <template v-for="subitem in item.children" :key="subitem.title">
                <v-list-item v-if="checkFeatureFlag(subitem)" :to="subitem.url">
                  <v-list-item-title>{{ subitem.title }}</v-list-item-title>
                </v-list-item>
              </template>
            </v-list>
          </v-menu>
        </div>
        <ExpandableHeaderContent :item="item" />
      </v-col>
    </v-row>
  </div>
</template>

<script setup>
import { useAppStore } from '@/stores/app'
import ExpandableHeaderContent from '@/components/tools/ExpandableHeaderContent.vue'
import { useFeatureFlagsStore } from '@/stores/feature-flags'

const appStore = useAppStore()
const featureFlagsStore = useFeatureFlagsStore()

function startFrom(arr, idx) {
  return arr.slice(idx)
}

function checkFeatureFlag(item) {
  if (!item.featureFlag) return true
  return featureFlagsStore.getFeatureFlag(item.featureFlag) !== false
}
</script>

<style scoped>
.fullscreen-bg {
  background-image: url('../../assets/library-background.jpg');
}
h1 {
  margin-bottom: 1rem;
  font-size: 60px;
}
p {
  font-size: 20px;
}
.item {
  padding: 0px;
  margin: 20px;
}
.item-content {
  background: #6675a3;
}
.item-description {
  background: #fff;
  padding: 5px;
}
</style>
