<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('TemplateIndexingDialog.title')"
    :open="show"
    v-bind="$attrs"
    @submit="submit"
    @close="close"
  >
    <template #body>
      <v-form ref="observer">
        <slot name="form" :form="form" :template="template" />
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import templates from '@/api/templates'
import templatePreInstances from '@/api/templatePreInstances'

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['notificationHub'],
  props: {
    preparePayloadFunc: {
      type: Function,
      default: null,
    },
    template: {
      type: Object,
      default: null,
    },
    urlPrefix: {
      type: String,
      default: null,
    },
    show: Boolean,
    preInstanceMode: {
      type: Boolean,
      default: false,
    },
  },
  emits: ['close', 'updated'],
  data() {
    return {
      form: {},
    }
  },
  watch: {
    template: {
      handler: function (value) {
        if (value) {
          this.form = { ...value }
        }
      },
      immediate: true,
    },
  },
  methods: {
    close() {
      this.notificationHub.clearErrors()
      this.$refs.observer.reset()
      this.$emit('close')
    },
    getBaseObjectType() {
      let result = this.urlPrefix.replace('-templates', '')
      if (result === '/activity') {
        result = '/activity-instruction'
      }
      return result.slice(1)
    },
    async submit() {
      this.notificationHub.clearErrors()

      const data = this.preparePayloadFunc()
      const api = this.preInstanceMode
        ? templatePreInstances(this.getBaseObjectType())
        : templates(this.urlPrefix)
      api.updateIndexings(this.template.uid, data).then(
        () => {
          this.$emit('updated')
          this.$emit('close')
          const msg = this.$t('TemplateIndexingDialog.update_success')
          this.notificationHub.add({ msg, type: 'success' })
        },
        () => {
          this.$refs.form.working = false
        }
      )
    },
  },
}
</script>
