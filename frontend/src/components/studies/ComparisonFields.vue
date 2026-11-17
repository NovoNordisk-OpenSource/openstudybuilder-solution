<template>
  <v-table density="compact">
    <thead>
      <tr>
        <th>{{ $t('StudyComparison.field') }}</th>
        <th>{{ $t('StudyComparison.value_a') }}</th>
        <th>{{ $t('StudyComparison.value_b') }}</th>
      </tr>
    </thead>
    <tbody>
      <tr
        v-for="change in changes"
        :key="change.field"
        :class="{ 'comparison-changed': change.changed }"
      >
        <td>{{ change.field }}</td>
        <td class="text-pre-wrap">{{ formatValue(change.old_value) }}</td>
        <td class="text-pre-wrap">{{ formatValue(change.new_value) }}</td>
      </tr>
    </tbody>
  </v-table>
</template>

<script setup>
defineProps({
  changes: { type: Array, required: true },
})

function formatValue(value) {
  if (value === null || value === undefined) {
    return '—'
  }
  return typeof value === 'object' ? JSON.stringify(value) : String(value)
}
</script>

<style scoped>
.comparison-changed {
  background-color: rgba(var(--v-theme-warning), 0.15);
  font-weight: 500;
}
</style>
