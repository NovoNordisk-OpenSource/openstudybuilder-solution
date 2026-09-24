<template>
  <SimpleFormDialog
    ref="formDialog"
    :title="title"
    :help-items="helpItems"
    :open="open"
    @close="cancel"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <v-row>
          <v-col cols="6">
            <v-text-field
              v-model="form.name"
              :label="$t('_global.name')"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
          <v-col cols="6">
            <v-text-field
              v-model="form.prefix"
              :label="$t('CRFExtensions.prefix')"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
        <v-row>
          <v-col>
            <v-text-field
              v-model="form.url"
              :label="$t('CRFExtensions.url')"
              clearable
              :rules="[formRules.required]"
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
</template>

<script setup>
import { computed, inject, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import crfs from '@/api/crfs'

const props = defineProps({
  open: Boolean,
  editItem: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['close'])

const formRules = inject('formRules')
const { t } = useI18n()

const formDialog = ref(null)
const observer = ref(null)

const form = ref({})
const helpItems = ref([])

const title = computed(() =>
  props.editItem?.uid
    ? t('CRFExtensions.edit_namespace')
    : t('CRFExtensions.new_namespace')
)

watch(
  () => props.editItem,
  (value) => {
    initForm(value)
  }
)

const cancel = async () => {
  close()
}

const close = () => {
  observer.value?.reset?.()
  emit('close')
}

const submit = async () => {
  if (props.editItem?.uid) {
    crfs.editNamespace(props.editItem.uid, form.value).then(
      () => {
        close()
      },
      () => {
        if (formDialog.value) {
          formDialog.value.working = false
        }
      }
    )
  } else {
    crfs.createNamespace(form.value).then(
      () => {
        close()
      },
      () => {
        if (formDialog.value) {
          formDialog.value.working = false
        }
      }
    )
  }
}

const initForm = (item) => {
  form.value = item || {}
}
</script>
