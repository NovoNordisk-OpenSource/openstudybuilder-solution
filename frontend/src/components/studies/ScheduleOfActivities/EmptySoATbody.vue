<template>
  <tbody>
    <tr>
      <td colspan="100%">
        <v-empty-state>
          <template #media>
            <div class="d-flex justify-center">
              <img
                :src="sbLogoUrl"
                style="width: 200px; height: auto"
                class="mb-6 mt-12"
                alt="StudyBuilder"
              />
            </div>
          </template>
          <template #title>
            <div class="text-label-large mt-8">
              {{ props.messages.title }}
            </div>
          </template>

          <template #text>
            <div class="text-body-small">
              {{ props.messages.text }}
            </div>
          </template>

          <template #actions>
            <v-btn
              v-if="props.visitsRedirect"
              class="secondary-btn"
              variant="outlined"
              rounded="xl"
              :text="$t('DetailedFlowchart.add_visit')"
              @click="redirectToVisits()"
            ></v-btn>

            <v-btn
              class="secondary-btn"
              variant="outlined"
              rounded="xl"
              :text="$t('DetailedFlowchart.add_study_activity')"
              @click="redirectToActivities()"
            ></v-btn>
          </template>
        </v-empty-state>
      </td>
    </tr>
  </tbody>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const sbLogoUrl = new URL(
  '../../../assets/soa_empty_state.png',
  import.meta.url
).href

const props = defineProps({
  messages: {
    type: Object,
    default: null,
  },
  visitsRedirect: {
    type: Boolean,
    default: false,
  },
})

function redirectToVisits() {
  router.push({
    name: 'StudyStructure',
    params: {
      tab: 'visits',
    },
  })
}

function redirectToActivities() {
  localStorage.setItem('open-form', true)
  router.push({
    name: 'StudyActivities',
    params: {
      tab: 'list',
    },
  })
}
</script>
