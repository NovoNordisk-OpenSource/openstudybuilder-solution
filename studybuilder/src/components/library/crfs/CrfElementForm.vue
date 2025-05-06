<template>
  <SimpleFormDialog
    ref="form"
    :title="title"
    :open="open"
    max-width="1000px"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col cols="6">
            <v-text-field
              v-model="form.name"
              :label="$t('CrfExtensions.ele_name')"
              density="compact"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
          <v-col>
            <v-select
              v-model="form.compatible_types"
              :label="$t('CrfExtensions.compatible_types')"
              :items="compatibleTypes"
              density="compact"
              multiple
              clearable
            />
          </v-col>
        </v-row>
        <v-row v-if="editItem.uid === undefined">
          <v-col cols="6">
            <v-select
              v-model="attribute"
              :label="$t('CrfExtensions.add_existing_attr')"
              :items="existingAttributes"
              return-object
              item-title="name"
              item-value="uid"
              density="compact"
              clearable
              @update:model-value="addExistingAttribute"
            />
          </v-col>
          <div class="mt-6">
            {{ $t('_global.or') }}
          </div>
          <v-col cols="3">
            <v-btn
              dark
              size="small"
              class="mt-2"
              color="primary"
              @click="addNewAttribute"
            >
              {{ $t('CrfExtensions.add_new_attr') }}
            </v-btn>
          </v-col>
        </v-row>
        <v-row v-for="attr in attributesToCreate" :key="attr.key">
          <v-col cols="3">
            <v-text-field
              v-model="attr.name"
              :disabled="editItem.uid !== undefined"
              :label="$t('CrfExtensions.attr_name')"
              density="compact"
              clearable
            />
          </v-col>
          <v-col cols="3">
            <v-select
              v-model="attr.data_type"
              :disabled="editItem.uid !== undefined"
              :label="$t('CrfExtensions.data_type')"
              :items="dataTypes"
              item-title="code_submission_value"
              item-value="code_submission_value"
              density="compact"
              clearable
            />
          </v-col>
          <v-col cols="3">
            <v-btn
              :disabled="editItem.uid !== undefined"
              class="ml-2"
              dark
              size="small"
              color="primary"
              icon="mdi-delete-outline"
              @click="removeAttribute(attr)"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import crfs from '@/api/crfs'
import terms from '@/api/controlledTerminology/terms'

export default {
  components: {
    SimpleFormDialog,
  },
  inject: ['formRules'],
  props: {
    open: Boolean,
    editItem: {
      type: Object,
      default: null,
    },
    parentUid: {
      type: String,
      default: null,
    },
    attributes: {
      type: Array,
      default: null,
    },
  },
  emits: ['close'],
  data() {
    return {
      form: {},
      dataTypes: [],
      attribute: null,
      attributesKeyIndex: 0,
      existingAttributes: [],
      attributesToCreate: [],
      compatibleTypes: ['FormDef', 'ItemGroupDef', 'ItemDef'],
    }
  },
  computed: {
    title() {
      return this.editItem.uid
        ? this.$t('CrfExtensions.edit_ele')
        : this.$t('CrfExtensions.new_ele')
    },
  },
  watch: {
    editItem(value) {
      this.initForm(value)
    },
    attributes() {
      this.existingAttributes = this.attributes
    },
  },
  mounted() {
    terms.getAttributesByCodelist('dataType').then((resp) => {
      this.dataTypes = resp.data.items
    })
  },
  methods: {
    addNewAttribute() {
      if (!this.attributesToCreate.find((attr) => attr.name === '')) {
        this.attributesToCreate.push({
          key: this.attributesKeyIndex,
          name: '',
          data_type: '',
        })
        this.attributesKeyIndex += 1
      }
    },
    addExistingAttribute(attribute) {
      if (attribute) {
        this.attributesToCreate.push(attribute)
        this.existingAttributes = this.existingAttributes.filter(
          (attr) => attr.uid !== attribute.uid
        )
        this.attribute = null
      }
    },
    removeAttribute(attribute) {
      this.attributesToCreate = this.attributesToCreate.filter(
        (attr) => attr.key !== attribute.key
      )
      if (attribute.uid) {
        this.existingAttributes.push(attribute)
      }
    },
    async cancel() {
      this.close()
    },
    close() {
      this.$refs.observer.reset()
      this.attributesToCreate = []
      this.form = {}
      this.$emit('close')
    },
    async submit() {
      this.form.vendor_namespace_uid = this.parentUid
      if (this.form.uid) {
        this.form.change_description = this.$t('_global.change_description')
        await crfs.editElement(this.form.uid, this.form).then(
          () => {
            this.close()
          },
          () => {
            this.$refs.form.working = false
          }
        )
      } else {
        let elementUid = ''
        await crfs.createElement(this.form).then(
          (resp) => {
            elementUid = resp.data.uid
          },
          () => {
            this.$refs.form.working = false
          }
        )
        if (this.attributesToCreate.length > 0 && elementUid !== '') {
          for (const attr of this.attributesToCreate) {
            delete attr.compatible_types
            attr.vendor_element_uid = elementUid
            await crfs.createAttribute(attr)
          }
          this.close()
        }
      }
    },
    initForm(item) {
      this.form = item
      this.attributes.forEach((attr) => {
        if (
          attr.vendor_element &&
          attr.vendor_element.uid === this.editItem.uid
        ) {
          this.attributesToCreate.push(attr)
        }
      })
    },
  },
}
</script>
