<template>
  <div class="search-field-container d-flex align-center">
    <v-text-field
      ref="searchFieldRef"
      v-model="search"
      clearable
      clear-icon="mdi-close"
      prepend-inner-icon="mdi-magnify"
      :label="$t('_global.search')"
      single-line
      color="nnBaseBlue"
      hide-details
      style="min-width: 240px; max-width: 300px"
      class="searchFieldLabel ml-0"
      data-cy="search-field"
      v-bind="$attrs"
    >
      <template #append-inner>
        <v-menu
          v-model="menuOpen"
          :close-on-content-click="false"
          :target="searchFieldRef?.$el"
          location="bottom end"
        >
          <template #activator="{ props: menuProps }">
            <v-btn
              icon="mdi-tune-variant"
              variant="text"
              size="x-small"
              color="nnBaseBlue"
              data-cy="advanced-search-button"
              :title="$t('_global.advanced_search')"
              v-bind="menuProps"
              @mousedown.stop
              @click.stop
            />
          </template>

          <v-card min-width="240" data-cy="advanced-search-menu">
            <v-card-text class="py-2">
              <v-switch
                v-model="matchWholeWords"
                :label="$t('_global.match_whole_words')"
                color="nnBaseBlue"
                density="compact"
                hide-details
                data-cy="match-whole-words-switch"
              />
            </v-card-text>
          </v-card>
        </v-menu>
      </template>
    </v-text-field>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineOptions({
  inheritAttrs: false,
})

const search = defineModel('search', { type: String, default: '' })
const matchWholeWords = defineModel('matchWholeWords', {
  type: Boolean,
  default: false,
})

const menuOpen = ref(false)
const searchFieldRef = ref(null)
</script>

<style scoped>
.search-field-container {
  min-height: 42px;
}

.searchFieldLabel.v-text-field {
  margin-left: 0 !important;
}

.searchFieldLabel.v-text-field label {
  font-size: 14px;
}

.searchFieldLabel.v-text-field :deep(input) {
  color: rgba(0, 0, 0, 0.87) !important;
}
</style>
