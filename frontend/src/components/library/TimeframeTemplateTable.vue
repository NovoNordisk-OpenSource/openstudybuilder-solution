<template>
  <StudybuilderTemplateTable
    url-prefix="/timeframe-templates"
    translation-type="TimeframeTemplateTable"
    object-type="timeframeTemplates"
    :with-indexing-properties="false"
    :with-pre-instances="false"
  >
    <template #editform="{ closeForm, selectedObject, filter, updateTemplate }">
      <StudybuilderTemplateForm
        :template="selectedObject"
        url-prefix="/timeframe-templates"
        translation-type="TimeframeTemplateTable"
        object-type="timeframeTemplates"
        :with-classification-attributes="false"
        @close="closeForm"
        @template-added="filter()"
        @template-updated="updateTemplate(arguments[0], 'Draft')"
      />
    </template>
  </StudybuilderTemplateTable>
</template>

<script setup>
import StudybuilderTemplateTable from '@/components/library/StudybuilderTemplateTable.vue'
import StudybuilderTemplateForm from '@/components/library/StudybuilderTemplateForm.vue'
</script>
