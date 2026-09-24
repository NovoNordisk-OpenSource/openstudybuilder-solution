<template>
  <div>
    <v-card>
      <v-card-title v-if="!noTitle">
        <span class="dialog-title">{{ $t('OdmViewer.odm_references') }}</span>
      </v-card-title>
      <v-row v-show="loading" class="justify-center" center>
        <v-col cols="12" sm="4">
          <v-progress-circular
            color="primary"
            indeterminate
            size="128"
            class="ml-4"
          />
        </v-col>
      </v-row>
      <v-card-text v-show="!loading">
        <v-treeview
          :key="graphKey"
          :items="crfData"
          activatable
          density="compact"
          item-value="name"
          disabled
          :open-all="openAll"
          :active="activeNodes"
        >
          <template #prepend="{ prepItem }">
            <v-icon :color="iconTypeAndColor(prepItem).color">
              {{ iconTypeAndColor(prepItem).type }}
            </v-icon>
          </template>
          <template #label="{ lblItem }">
            <div v-if="lblItem" class="black--text">
              {{ lblItem.name }}
            </div>
          </template>
        </v-treeview>
      </v-card-text>
      <v-card-actions v-if="!noActions">
        <v-spacer />
        <v-btn class="secondary-btn" color="white" @click="close()">
          {{ $t('_global.close') }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'

import crfs from '@/api/crfs'

const props = defineProps({
  item: {
    type: Object,
    default: null,
  },
  type: {
    type: String,
    default: null,
  },
  noTitle: {
    type: Boolean,
    default: false,
  },
  noActions: {
    type: Boolean,
    default: false,
  },
  fullData: {
    type: Boolean,
    default: true,
  },
  openAll: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['close'])

const collections = ref([])
const forms = ref([])
const groups = ref([])
const items = ref([])
const crfData = ref([])
const graphKey = ref(0)
const loading = ref(false)
const activeNodes = ref([])

watch(
  () => props.item,
  (value) => {
    if (value) {
      fetchData()
    }
  }
)

watch(
  () => props.openAll,
  () => {
    graphKey.value += 1
  }
)

onMounted(() => {
  fetchData()
})

const close = () => {
  collections.value = []
  forms.value = []
  groups.value = []
  items.value = []
  crfData.value = []
  emit('close')
}

const iconTypeAndColor = (item) => {
  if (item) {
    if (item.collection) {
      return { type: 'mdi-alpha-t-circle-outline', color: 'primary' }
    } else if (item.form) {
      return { type: 'mdi-alpha-f-circle-outline', color: 'success' }
    } else if (item.group) {
      return { type: 'mdi-alpha-g-circle-outline', color: 'secondary' }
    } else {
      return { type: 'mdi-alpha-i-circle-outline', color: 'error' }
    }
  }
  return {}
}

const getCrfData = async () => {
  loading.value = true
  const params = {}

  await crfs.get('study-events', { params }).then((resp) => {
    collections.value = resp.data.items
    for (const collection of collections.value) {
      collections.value[collections.value.indexOf(collection)].collection = true
    }
  })
  await crfs.get('forms', { params }).then((resp) => {
    forms.value = resp.data.items
    for (const form of forms.value) {
      forms.value[forms.value.indexOf(form)].form = true
    }
  })
  await crfs.get('item-groups', { params }).then((resp) => {
    groups.value = resp.data.items
    for (const group of groups.value) {
      groups.value[groups.value.indexOf(group)].group = true
    }
  })

  crfData.value = [props.item]
  groups.value = groups.value.filter((group) =>
    group.items.some((item) => item.uid === props.item.uid)
  )
  for (const group of groups.value) {
    groups.value[groups.value.indexOf(group)].children = [props.item]
  }
  if (groups.value.length > 0) {
    crfData.value = groups.value
  } else {
    loading.value = false
    graphKey.value += 1
    return
  }

  forms.value = forms.value.filter((form) =>
    groups.value.some((group) =>
      form.item_groups.some((g) => g.uid === group.uid)
    )
  )
  for (const form of forms.value) {
    forms.value[forms.value.indexOf(form)].children = forms.value[
      forms.value.indexOf(form)
    ].item_groups
      .map((group) => groups.value.find((el) => el.uid === group.uid))
      .filter(function (val) {
        return val !== undefined
      })
  }
  if (forms.value.length > 0) {
    crfData.value = forms.value
  } else {
    loading.value = false
    graphKey.value += 1
    return
  }

  collections.value = collections.value.filter((collection) =>
    forms.value.some((form) => collection.forms.some((g) => g.uid === form.uid))
  )
  for (const collection of collections.value) {
    collections.value[collections.value.indexOf(collection)].children =
      collections.value[collections.value.indexOf(collection)].forms
        .map((form) => forms.value.find((el) => el.uid === form.uid))
        .filter(function (val) {
          return val !== undefined
        })
  }
  if (collections.value.length > 0) {
    crfData.value = collections.value
  }

  loading.value = false
  graphKey.value += 1
}

const getCollections = async (form) => {
  await crfs.getRelationships(form.uid, 'forms').then((resp) => {
    collections.value = resp.data.OdmStudyEvent
  })
  if (collections.value) {
    const params = {
      filters: {
        uid: { v: collections.value },
      },
    }
    await crfs.get('study-events', { params }).then((resp) => {
      collections.value = resp.data.items
    })
  }
}

const getForms = async (collection, group) => {
  if (collection) {
    const params = {
      filters: {
        uid: {
          v: Array.from(collection.forms.map((f) => (f.uid ? f.uid : f))),
        },
      },
    }
    await crfs.get('forms', { params }).then((resp) => {
      forms.value = resp.data.items
    })
  } else {
    await crfs.getRelationships(group.uid, 'item-groups').then((resp) => {
      forms.value = resp.data.OdmForm
    })
  }
}

const getGroups = async (form, item) => {
  if (form) {
    const params = {
      filters: {
        uid: {
          v: Array.from(form.item_groups.map((f) => (f.uid ? f.uid : f))),
        },
      },
    }
    await crfs.get('item-groups', { params }).then((resp) => {
      groups.value = resp.data.items
    })
  } else {
    await crfs.getRelationships(item.uid, 'items').then((resp) => {
      groups.value = resp.data.OdmItemGroup
    })
  }
}

const getDataFromCollectionLevel = async () => {
  loading.value = true
  crfData.value = [
    {
      name: props.item.name,
      uid: props.item.uid,
      children: [],
      collection: true,
    },
  ]
  await getForms(props.item, null)
  crfData.value[0].children = forms.value
  for (const form of crfData.value[0].children) {
    await getGroups(form, null)
    for (const group of groups.value) {
      groups.value[groups.value.indexOf(group)] = {
        name: group.name,
        uid: group.uid,
        children: group.items,
        group: true,
      }
    }
    const index = crfData.value[0].children.indexOf(form)
    crfData.value[0].children[index] = {
      name: form.name,
      uid: form.uid,
      children: groups.value,
      form: true,
    }
  }
  loading.value = false
  graphKey.value += 1
}

const getDataFromFormLevel = async () => {
  loading.value = true
  await getGroups(props.item, null)
  const dataFromForm = [
    {
      name: props.item.name,
      uid: props.item.uid,
      children: groups.value,
      form: true,
    },
  ]
  crfData.value = dataFromForm
  if (dataFromForm[0].children && dataFromForm[0].children.length > 0) {
    for (const group of dataFromForm[0].children) {
      const index = dataFromForm[0].children.indexOf(group)
      dataFromForm[0].children[index] = {
        name: group.name,
        uid: group.uid,
        children: group.items,
        group: true,
      }
    }
  }
  if (props.fullData) {
    await getCollections(props.item)
    if (collections.value && collections.value.length > 0) {
      crfData.value = collections.value
      for (const el of crfData.value) {
        crfData.value[crfData.value.indexOf(el)] = {
          name: el.name,
          uid: el.uid,
          children: dataFromForm,
          collection: true,
        }
      }
    }
  }
  loading.value = false
  graphKey.value += 1
}

const getDataFromGroupLevel = async () => {
  loading.value = true
  const dataFromGroup = [
    {
      name: props.item.name,
      uid: props.item.uid,
      children: props.item.items,
      group: true,
    },
  ]
  crfData.value = dataFromGroup
  if (props.fullData) {
    await getForms(null, props.item)
    if (forms.value && forms.value.length > 0) {
      const formsWrapper = {
        forms: forms.value,
      }
      await getForms(formsWrapper, null)
      for (const form of forms.value) {
        forms.value[forms.value.indexOf(form)] = {
          name: form.name,
          uid: form.uid,
          children: dataFromGroup,
          form: true,
        }
      }
      crfData.value = forms.value
      for (const form of forms.value) {
        await getCollections(form)
        if (collections.value && collections.value.length > 0) {
          crfData.value = []
          for (const collection of collections.value) {
            crfData.value.push({
              name: collection.name,
              uid: collection.uid,
              children: [form],
              collection: true,
            })
          }
        }
      }
    }
    const output = []
    crfData.value.forEach(function (item) {
      const existing = output.filter(function (v) {
        return v.name === item.name
      })
      if (existing.length) {
        const existingIndex = output.indexOf(existing[0])
        output[existingIndex].children = output[existingIndex].children.concat(
          item.children
        )
      } else {
        output.push(item)
      }
    })
    crfData.value = output
  }
  loading.value = false
  graphKey.value += 1
}

const fetchData = () => {
  if (!props.item) return
  activeNodes.value = [props.item.name]

  if (props.type === 'collection') {
    getDataFromCollectionLevel()
  } else if (props.type === 'form') {
    getDataFromFormLevel()
  } else if (props.type === 'group') {
    getDataFromGroupLevel()
  } else if (props.type === 'item') {
    getCrfData()
  }
}
</script>
<style scoped>
.highlight {
  background-color: lightblue;
}
</style>
