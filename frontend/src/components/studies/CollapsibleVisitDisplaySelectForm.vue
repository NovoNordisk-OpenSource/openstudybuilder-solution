<template>
  <SimpleFormDialog
    ref="form"
    :title="$t('CollapsibleVisitGroupForm.format_title')"
    :open="open"
    max-width="600px"
    @close="close"
    @submit="submit"
  >
    <template #body>
      <v-form ref="observer">
        <div class="label mb-4">
          {{
            $t('CollapsibleVisitGroupForm.selected_visits', {
              number: visits.length,
            })
          }}
        </div>
        <v-sheet
          v-for="visit in visits"
          :key="visit.text"
          color="nnLightBlue100"
          rounded="lg"
          class="mb-2"
          max-width="400px"
          border="xs"
        >
          <v-checkbox
            v-model="checkVisits"
            :label="visit.text"
            disabled
            hide-details
          />
        </v-sheet>
        <v-row class="mt-2">
          <v-col>
            <div class="label mb-2">
              {{ $t('CollapsibleVisitGroupForm.format_question') }}
            </div>
            <v-radio-group
              v-model="format"
              hide-details
              :rules="[formRules.required]"
            >
              <v-radio
                :title="
                  $t(
                    'CollapsibleVisitGroupForm.range_selection_only_consecutive'
                  )
                "
                :disabled="!props.areConsecutiveVisitsSelected"
                :label="
                  $t('CollapsibleVisitGroupForm.range_visits', {
                    visits: `${visits[0].text}-${visits[visits.length - 1].text}`,
                  })
                "
                value="range"
              >
                <template #label>
                  <div class="chkText">
                    {{
                      $t('CollapsibleVisitGroupForm.range_visits', {
                        visits: `${visits[0].text}-${visits[visits.length - 1].text}`,
                      })
                    }}
                  </div>
                </template>
              </v-radio>
              <v-alert
                v-if="!props.areConsecutiveVisitsSelected"
                type="warning"
                :text="
                  $t(
                    'CollapsibleVisitGroupForm.range_selection_only_consecutive'
                  )
                "
                rounded="lg"
              />
              <v-radio value="list">
                <template #label>
                  <div class="chkText">
                    {{
                      $t('CollapsibleVisitGroupForm.list_visits', {
                        visits: `${visits.map((obj) => obj.text).join(', ')}`,
                      })
                    }}
                  </div>
                </template>
              </v-radio>
            </v-radio-group>
            <v-alert
              color="nnLightBlue200"
              icon="mdi-information-outline"
              class="my-4 text-nnTrueBlue"
              type="info"
              rounded="lg"
              :text="$t('CollapsibleVisitGroupForm.format_info')"
            />
            <v-alert
              v-if="areDifferentFootnotesApplied()"
              type="warning"
              rounded="lg"
              :text="
                $t(
                  'CollapsibleVisitGroupForm.collapsing_visits_with_different_footnotes'
                )
              "
            />
          </v-col>
        </v-row>
      </v-form>
    </template>
  </SimpleFormDialog>
  <CollapsibleVisitGroupForm
    :open="showCollapsibleGroupForm"
    :visits="visits"
    :format="format"
    @close="closeCollapsibleVisitGroupForm"
    @created="collapsibleVisitGroupCreated"
  />
</template>

<script setup>
import SimpleFormDialog from '@/components/tools/SimpleFormDialog.vue'
import studyEpochs from '@/api/studyEpochs'
import { useStudiesGeneralStore } from '@/stores/studies-general'
import CollapsibleVisitGroupForm from './CollapsibleVisitGroupForm.vue'
import { watch, inject, ref } from 'vue'

const formRules = inject('formRules')
const studiesGeneralStore = useStudiesGeneralStore()
const emit = defineEmits(['close', 'created'])

const props = defineProps({
  visits: {
    type: Array,
    default: () => [],
  },
  areConsecutiveVisitsSelected: {
    type: Boolean,
    default: true,
    required: false,
  },
  open: Boolean,
})
const observer = ref()

const format = ref('range')
const showCollapsibleGroupForm = ref(false)
const checkVisits = ref(true)

function collapsibleVisitGroupCreated() {
  showCollapsibleGroupForm.value = false
  emit('created')
  close()
}

function closeCollapsibleVisitGroupForm() {
  showCollapsibleGroupForm.value = false
  close()
}

function areDifferentFootnotesApplied() {
  const footnotes = JSON.stringify(props.visits[0].footnotes)
  for (const visit of props.visits) {
    if (JSON.stringify(visit.footnotes) !== footnotes) {
      return true
    }
  }
  return false
}

function close() {
  emit('close')
}
watch(
  () => props.areConsecutiveVisitsSelected,
  (value) => {
    if (value === false) format.value = 'list'
    else {
      format.value = 'range'
    }
  }
)

async function submit() {
  const visitUids = props.visits.map((item) => item.refs[0].uid)
  const data = {
    visits_to_assign: visitUids,
    format: format.value,
    validate_only: false,
  }
  await studyEpochs
    .createCollapsibleVisitGroup(studiesGeneralStore.selectedStudy.uid, data)
    .then(() => {
      emit('created')
      close()
    })
    .catch((err) => {
      if (err.response.status === 400) {
        if (err.response.data.type !== 'BusinessLogicException') {
          showCollapsibleGroupForm.value = true
        }
      }
    })
}
</script>
<style scoped>
.label {
  font-weight: 700;
  font-size: 18px;
  line-height: 24px;
  letter-spacing: -0.02em;
  color: var(--semantic-system-brand, #001965);
  min-height: 24px;
}
.chkText {
  color: var(--semantic-system-brand, #001965);
}
</style>
