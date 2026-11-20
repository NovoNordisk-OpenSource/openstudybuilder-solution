<template>
  <!-- How much in the library stands behind one finding, as the assessment counted it.
       `usage_count` is null on every kind it does not apply to, and then nothing is
       shown. The tooltip says what was counted, because that differs by kind. -->
  <v-chip
    v-if="finding.usage_count != null"
    size="x-small"
    variant="tonal"
    :color="finding.usage_count ? 'warning' : 'success'"
    class="mt-1"
    data-cy="standards-import-finding-usage"
  >
    {{
      finding.usage_count
        ? $t('StandardsImport.finding_usage_count', finding.usage_count)
        : $t('StandardsImport.finding_usage_free')
    }}
    <v-tooltip location="top" max-width="400">
      <template #activator="{ props: tooltipProps }">
        <v-icon v-bind="tooltipProps" size="12" class="ml-1">
          mdi-information-outline
        </v-icon>
      </template>
      {{ hint }}
    </v-tooltip>
  </v-chip>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  finding: {
    type: Object,
    required: true,
  },
})

// On SPONSOR_TERM_DUPLICATE the count is about the sponsor term the CDISC term collides
// with, and zero is a real answer: checked, and free to displace. On the two CDISC term
// changes it is about the CDISC term, through the finding's own codelist only - those
// kinds are raised only when it is above zero.
const hint = computed(() =>
  props.finding.type === 'SPONSOR_TERM_DUPLICATE'
    ? t('StandardsImport.finding_usage_hint_sponsor_term')
    : t('StandardsImport.finding_usage_hint_cdisc_term')
)
</script>
