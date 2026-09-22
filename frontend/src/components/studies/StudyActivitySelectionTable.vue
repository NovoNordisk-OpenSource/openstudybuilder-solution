<template>
  <div class="d-flex align-center">
    <div>
      {{ title }} <span class="font-weight-bold">{{ selection.length }}</span>
    </div>
    <div class="ml-10 d-flex align-center">
      {{ $t('StudyActivitySelectionTable.show_items') }}
      <v-checkbox
        v-model="showItems"
        on-icon="mdi-close-circle-outline"
        off-icon="mdi-dots-horizontal-circle-outline"
        hide-details
        class="ml-2"
      />
    </div>
  </div>
  <v-table v-if="showItems" density="compact" class="mt-4 preview">
    <tbody>
      <tr v-for="item in selection" :key="item.name">
        <td>{{ item.activity.name }}</td>
        <td v-if="withDeleteAction" class="text-right">
          <v-btn
            color="error"
            icon="mdi-close"
            variant="text"
            @click="removeItem(item)"
          />
        </td>
      </tr>
    </tbody>
  </v-table>
</template>

<script>
export default {
  props: {
    selection: {
      type: Array,
      default: () => [],
    },
    title: {
      type: String,
      default: '',
    },
    withDeleteAction: {
      type: Boolean,
      default: true,
    },
  },
  emits: ['remove'],
  data() {
    return {
      showItems: false,
    }
  },
  methods: {
    removeItem(item) {
      this.$emit('remove', item)
    },
  },
}
</script>

<style scoped lang="scss">
.preview {
  max-height: 150px;
  overflow: auto;
}
</style>
