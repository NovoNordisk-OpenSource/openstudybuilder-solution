<template>
  <v-tooltip v-if="valueExist()" bottom>
    <template #activator="{ props }">
      <v-icon color="darkGrey" v-bind="props">
        {{ getIcon() }}
      </v-icon>
    </template>
    <span>{{ getTooltip() }}</span>
  </v-tooltip>
</template>

<script setup>
import { useI18n } from 'vue-i18n'

const props = defineProps({
  item: {
    type: Object,
    default: null,
  },
  value: {
    type: String,
    default: null,
  },
})

const { t } = useI18n()

const valueExist = () => {
  if (!props.item || !props.value) {
    return false
  }

  if (props.item[props.value] === 'Yes') {
    return true
  } else if (props.value === 'refAttrs') {
    return props.item.vendor.attributes.length > 0
  } else if (props.value === 'dataType') {
    return props.item.datatype.submission_value
  } else if (props.value === 'vendor') {
    return (
      props.item.vendor_attributes &&
      props.item.vendor_attributes.length +
        props.item.vendor_element_attributes.length +
        props.item.vendor_elements.length >
        0
    )
  }
  return false
}

const getTooltip = () => {
  if (valueExist()) {
    switch (props.value) {
      case 'repeating':
        return t('CRFTree.repeating')
      case 'locked':
        return t('CRFTree.locked')
      case 'mandatory':
        return t('CRFTree.mandatory')
      case 'is_reference_data':
        return t('CRFTree.ref_data')
      case 'refAttrs':
        return t('CRFTree.ref_vendor_extension_applied')
      case 'dataType':
        return props.item.datatype.submission_value + t('CRFTree.data_type')
      case 'vendor':
        return t('CRFTree.vendor_extension_applied')
    }
  }
}

const getIcon = () => {
  if (valueExist()) {
    switch (props.value) {
      case 'dataType':
        return getDataTypeIcon()
      case 'repeating':
        return 'mdi-repeat'
      case 'locked':
        return 'mdi-lock-outline'
      case 'mandatory':
        return 'mdi-database-lock'
      case 'is_reference_data':
        return 'mdi-arrow-decision-outline'
      case 'refAttrs':
        return 'mdi-toy-brick-plus-outline'
      case 'vendor':
        return 'mdi-toy-brick-plus-outline'
    }
  }
}

const getDataTypeIcon = () => {
  switch (props.item.datatype.submission_value.toLowerCase()) {
    case 'uri':
      return 'mdi-web'
    case 'string':
      return 'mdi-format-list-bulleted-square'
    case 'comment':
    case 'text':
      return 'mdi-alphabetical'
    case 'boolean':
    case 'hexbinary':
    case 'base64binary':
      return 'mdi-order-bool-ascending'
    case 'integer':
    case 'float':
    case 'double':
    case 'hexfloat':
    case 'base64float':
      return 'mdi-numeric'
  }
  return 'mdi-calendar-clock'
}
</script>
