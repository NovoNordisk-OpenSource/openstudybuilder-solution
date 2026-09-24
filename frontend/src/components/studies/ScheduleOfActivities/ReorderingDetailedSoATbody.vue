<template>
  <tbody ref="parent">
    <template
      v-for="(row, index) in soaRowsDrag"
      :key="`${row.cells[0].style}_${row.cells[0].text}`"
    >
      <tr
        :class="scheduleMethods.getSoaRowClasses(row)"
        :style="row.noIcon ? 'pointer-events: none !important' : ''"
      >
        <td
          :class="scheduleMethods.getSoaFirstCellClasses(row.cells[0])"
          class="sticky-column"
          style="min-width: 300px"
        >
          <div class="d-flex align-center justify-start">
            <v-icon v-if="!row.noIcon" size="small" class="ml-4">
              mdi-sort
            </v-icon>
            <v-btn variant="text" style="height: 32px" size="x-small" />
            <v-badge
              color="transparent"
              text-color="secondary"
              floating
              :content="
                row.cells[0].refs.length
                  ? scheduleMethods.getElementFootnotesLetters(
                      row.cells[0]?.refs[0]?.uid
                    )
                  : ''
              "
            >
              <v-tooltip bottom>
                <template #activator="{ props }">
                  <div v-bind="props">
                    <span
                      :class="
                        row.cells[0].style.replace(
                          /PlaceholderSubmitted|Placeholder/g,
                          ''
                        ) !== 'activity'
                          ? 'text-uppercase'
                          : ''
                      "
                    >
                      {{ row.cells[0].text.substring(0, 40) }}
                    </span>
                  </div>
                </template>
                <span
                  :class="
                    row.cells[0].style.replace(
                      /PlaceholderSubmitted|Placeholder/g,
                      ''
                    ) !== 'activity'
                      ? 'text-uppercase'
                      : ''
                  "
                >
                  {{ row.cells[0].text }}
                </span>
              </v-tooltip>
            </v-badge>
            <v-spacer />
            <v-btn icon disabled variant="text" style="height: auto">
              <v-icon v-if="!row.hide" size="x-small" color="success">
                mdi-eye-outline
              </v-icon>
              <v-icon v-else size="x-small"> mdi-eye-off-outline </v-icon>
            </v-btn>
          </div>
        </td>
        <td
          v-if="scheduleMethods.getSoaRowType(row) !== 'activity'"
          :colspan="row.cells.length - 1"
        />
        <td
          v-for="(visitCell, visitIndex) in soaVisitRow"
          v-else
          :key="`row-${index}-cell-${visitIndex}`"
        >
          <v-row class="mt-0">
            <v-badge
              color="transparent"
              floating
              text-color="secondary"
              offset-x="2"
              :content="
                row.cells[visitIndex + 1].refs &&
                row.cells[visitIndex + 1].refs.length
                  ? scheduleMethods.getElementFootnotesLetters(
                      row.cells[visitIndex + 1].refs[0].uid
                    )
                  : ''
              "
              overlap
            >
              <input
                v-model="
                  // eslint disabled since we're not mutating this prop. Checkbox is always disabled.
                  // eslint-disable-next-line vue/no-mutating-props
                  props.currentSelectionMatrix[row.cells[0].refs[0].uid][
                    visitCell.refs[0].uid
                  ].value
                "
                color="success"
                disabled
                hide-details
                density="compact"
                class="mx-0 ml-6 mb-3 px-0"
                type="checkbox"
              />
            </v-badge>
          </v-row>
        </td>
      </tr>
    </template>
  </tbody>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import scheduleMethods from '@/utils/scheduleMethods'
import { useDragAndDrop } from '@formkit/drag-and-drop/vue'
import study from '@/api/study'
import { useStudiesGeneralStore } from '@/stores/studies-general'

const studiesGeneralStore = useStudiesGeneralStore()

const [parent, soaRowsDrag] = useDragAndDrop([], {
  onDragend: (event) => {
    if (event.state.targetIndex !== event.state.initialIndex) {
      reorder(
        event.draggedNode.data.value.cells[0].refs[0].uid,
        event.state.targetIndex + 1 + orderAlignValue.value,
        event.draggedNode.data.value.cells[0].style.replace(
          /PlaceholderSubmitted|Placeholder/g,
          ''
        )
      )
    }
  },
})

const props = defineProps({
  soaRows: {
    type: Array,
    default: null,
  },
  selectedReorderItem: {
    type: Object,
    default: null,
  },
  soaVisitRow: {
    type: Object,
    default: null,
  },
  currentSelectionMatrix: {
    type: Object,
    default: null,
  },
})

const orderAlignValue = ref(0)

onMounted(() => {
  initiateReorder()
})

function initiateReorder() {
  // When we want to reoder items other then SoA groups then we need to add to the table parents of that item
  // (eg. if we want to reorder groups we need to add SoA group parent of that group)
  // Because of that we have more items in a table then what we want to reorder.
  // orderAlignValue variable was introduced to align correct orders for reordering
  if (
    props.selectedReorderItem.style.replace(
      /PlaceholderSubmitted|Placeholder/g,
      ''
    ) === 'activity'
  ) {
    orderAlignValue.value = -3
  } else if (props.selectedReorderItem.style === 'subGroup') {
    orderAlignValue.value = -2
  } else if (props.selectedReorderItem.style === 'group') {
    orderAlignValue.value = -1
  }
  try {
    soaRowsDrag.value = []
    if (props.selectedReorderItem.style === 'soaGroup') {
      props.soaRows.forEach((row) => {
        if (
          row.cells[0].style.replace(
            /PlaceholderSubmitted|Placeholder/g,
            ''
          ) === props.selectedReorderItem.style
        ) {
          soaRowsDrag.value.push(row)
        }
      })
    } else {
      gatherReorderData(
        props.selectedReorderItem,
        props.selectedReorderItem.tableIndex
      )
    }
  } catch (error) {
    console.error(error)
  }
}

function gatherReorderData(selectedReorderItem, index) {
  // We can enable reordering from any item in SoA table.
  // So to gather all eg. activities for a subgroup we're checking if an item is first in a parent
  // If no we're going up the table to find first item
  if (selectedReorderItem.order !== 1) {
    for (let i = index; i > 0; i--) {
      if (
        props.soaRows[i].cells[0].style.replace(
          /PlaceholderSubmitted|Placeholder/g,
          ''
        ) ===
          selectedReorderItem.style.replace(
            /PlaceholderSubmitted|Placeholder/g,
            ''
          ) &&
        props.soaRows[i].order === 1
      ) {
        selectedReorderItem = props.soaRows[i].cells[0]
        break
      }
    }
    try {
      index = props.soaRows.indexOf(
        props.soaRows.find(
          (item) =>
            item?.cells[0]?.refs[0]?.uid === selectedReorderItem.refs[0].uid
        )
      )
    } catch (error) {
      console.error(error)
    }
  }
  // And then down the table to gather all items with the same type (style)
  for (let i = index; i <= props.soaRows.length; i++) {
    if (
      props.soaRows[i]?.cells[0]?.style.replace(
        /PlaceholderSubmitted|Placeholder/g,
        ''
      ) ===
      selectedReorderItem.style.replace(/PlaceholderSubmitted|Placeholder/g, '')
    ) {
      soaRowsDrag.value.push(props.soaRows[i])
    } else if (
      props.soaRows[i]?.cells[0]?.style ===
      getStopType(
        selectedReorderItem.style.replace(
          /PlaceholderSubmitted|Placeholder/g,
          ''
        )
      )
    ) {
      break
    }
  }
  if (selectedReorderItem.style !== 'soaGroup') {
    getParents(
      index,
      selectedReorderItem.style.replace(/PlaceholderSubmitted|Placeholder/g, '')
    )
  }
}

function getStopType(type) {
  switch (type) {
    case 'group':
      return 'soaGroup'
    case 'subGroup':
      return 'group'
    case 'activity':
      return 'subGroup'
  }
}

function getParents(index, type) {
  const parentsMatrix = ['soaGroup', 'group', 'subGroup']
  let currentParentIndex = 0
  if (type === 'activity') {
    currentParentIndex = 2
  } else if (type === 'subGroup') {
    currentParentIndex = 1
  }
  for (let i = index; i >= 0; i--) {
    if (props.soaRows[i].cells[0].style === parentsMatrix[currentParentIndex]) {
      const el = props.soaRows[i]
      el.noIcon = true
      soaRowsDrag.value.unshift(el)
      if (currentParentIndex === 0) {
        break
      }
      currentParentIndex = currentParentIndex - 1
    }
  }
}

function reorder(uid, newOrder, type) {
  study.reorderSoa(
    studiesGeneralStore.selectedStudy.uid,
    uid,
    newOrder,
    getApiCallType(type)
  )
}

function getApiCallType(type) {
  switch (type) {
    case 'soaGroup':
      return 'study-soa-groups'
    case 'group':
      return 'study-activity-groups'
    case 'subGroup':
      return 'study-activity-subgroups'
    case 'activity':
      return 'study-activities'
  }
}
</script>

<style lang="scss" scoped>
thead {
  background-color: rgb(var(--v-theme-tableGray));
  font-weight: 600;
}
tr {
  padding: 4px;
  &.section {
    background-color: rgb(var(--v-theme-tableGray));
    font-weight: 600;
  }
}
tbody tr {
  border-bottom: 1px solid rgb(var(--v-theme-greyBackground));
}
th {
  vertical-align: bottom;
  background-color: rgb(var(--v-theme-nnLightBlue100));
}
th,
td {
  position: relative;
  font-size: 11px;
  z-index: 0;
}

td {
  background-color: inherit;
}

.sticky-header {
  overflow-y: auto;

  thead th {
    position: sticky;
    top: 0;
    z-index: 3;
  }
}
.sticky-column {
  position: sticky;
  left: 0px;
  z-index: 4 !important;
}
.flowchart {
  background-color: rgb(var(--v-theme-nnSeaBlue300));
}
.group {
  background-color: rgb(var(--v-theme-nnSeaBlue200));
}
.subgroup {
  background-color: rgb(var(--v-theme-nnSeaBlue100));
  font-weight: 600;
}
.v-card-text {
  display: inline-flex;
}
input[type='checkbox'] {
  cursor: pointer;
}
</style>
