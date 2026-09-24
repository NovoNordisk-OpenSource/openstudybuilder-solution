<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('StudyActivityBatchEditForm.title')"
    :help-items="helpItems"
    :open="open"
    max-width="600px"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <p>{{ $t('StudyActivityBatchEditForm.note') }}</p>
        <div class="d-flex align-center my-2">
          <div class="font-weight-bold">
            {{
              $t('StudyActivityBatchEditForm.items_selected', {
                number: selection.length,
              })
            }}
          </div>
        </div>
        <div
          v-for="item in selection"
          :key="item.name"
          class="d-flex mb-2 checkbox"
        >
          <v-checkbox
            :model-value="true"
            disabled
            hide-details
            :label="item.activity.name"
          />
          <v-spacer />
          <v-btn
            color="error"
            icon="mdi-close"
            variant="text"
            class="mt-1"
            @click="removeItem(item)"
          />
        </div>
        <slot name="body" />
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'

export default {
  components: {
    SimpleFormDialog,
  },
  props: {
    helpItems: {
      type: Array,
      default: () => [],
    },
    selection: {
      type: Array,
      default: () => [],
    },
    withDeleteAction: {
      type: Boolean,
      default: false,
    },
    open: Boolean,
  },
  emits: ['close', 'remove', 'submit'],
  data() {
    return {
      showItems: false,
    }
  },
  methods: {
    async submit() {
      if (this.$parent.$refs?.observer) {
        const { valid } = await this.$parent.$refs.observer.validate()
        if (!valid) {
          this.$refs.form.working = false
          return
        }
      }
      this.$emit('submit')
    },
    close() {
      this.showItems = false
      this.$emit('close')
    },
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
.checkbox {
  border-radius: 10px;
  background-color: rgb(var(--v-theme-nnGraniteGrey1));
}
</style>
