<template>
  <v-expansion-panels flat tile accordion>
    <v-expansion-panel>
      <v-expansion-panel-title
        data-cy="cl-summary-title"
        class="text-headline-small text-grey"
      >
        {{ $t('CodelistSummary.title') }}
      </v-expansion-panel-title>
      <v-expansion-panel-text>
        <v-row class="mt-2 mb-4">
          <v-col cols="9">
            <v-row>
              <v-col sm="2" md="1">
                <span class="v-label">{{
                  $t('CodelistSummary.concept_id')
                }}</span>
              </v-col>
              <v-col data-cy="Concept ID" sm="10" md="11">
                {{ codelistAttributes.codelist_uid }}
              </v-col>
            </v-row>
          </v-col>
        </v-row>
        <v-row class="my-4">
          <v-col cols="9">
            <v-row>
              <v-col sm="2" md="1">
                <span class="v-label">{{ $t('_global.name') }}</span>
              </v-col>
              <v-col data-cy="Name" sm="10" md="11">
                {{ codelistAttributes.name }}
              </v-col>
              <v-col sm="2" md="1">
                <span class="v-label">{{ $t('_global.label') }}</span>
              </v-col>
              <v-col data-cy="Label" sm="10" md="11">
                {{ codelistNames.name }}
              </v-col>
              <v-col sm="2" md="1">
                <span class="v-label">{{ $t('_global.definition') }}</span>
              </v-col>
              <v-col data-cy="Definition" sm="10" md="11">
                {{ codelistAttributes.definition }}
              </v-col>
            </v-row>
          </v-col>
          <v-col cols="3">
            <v-row>
              <v-col cols="6">
                <span class="v-label">{{ $t('_global.library') }}</span>
              </v-col>
              <v-col data-cy="Library" cols="6">
                {{ codelistNames.library_name }}
              </v-col>
              <v-col cols="6">
                <span class="v-label">{{
                  $t('CtCatalogueTable.template_parameter')
                }}</span>
              </v-col>
              <v-col data-cy="Template parameter" cols="6">
                {{ $filters.yesno(codelistNames.template_parameter) }}
              </v-col>
              <v-col cols="6">
                <span class="v-label">{{
                  $t('CtCatalogueTable.extensible')
                }}</span>
              </v-col>
              <v-col data-cy="Extensible" cols="6">
                {{ $filters.yesno(codelistAttributes.extensible) }}
              </v-col>
            </v-row>
          </v-col>
        </v-row>
      </v-expansion-panel-text>
    </v-expansion-panel>
  </v-expansion-panels>
</template>

<script setup>
// eslint-disable-next-line no-unused-vars
const props = defineProps({
  codelistNames: {
    type: Object,
    default: null,
  },
  codelistAttributes: {
    type: Object,
    default: null,
  },
})
</script>

<style scoped>
.col {
  padding-top: 2px !important;
  padding-bottom: 2px !important;
}
</style>
