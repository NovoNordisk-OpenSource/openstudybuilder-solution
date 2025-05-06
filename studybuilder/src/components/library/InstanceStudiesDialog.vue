<template>
  <v-card elevation="0" rounded="xl">
    <v-card-title>
      <span class="dialog-title">{{
        $t('InstanceStudiesDialog.title', { type })
      }}</span>
    </v-card-title>
    <v-card-text>
      <v-row class="mt-4">
        <v-col cols="2">
          <strong>{{
            $t('InstanceStudiesDialog.template', { type: capitalizedType })
          }}</strong>
        </v-col>
        <v-col cols="10">
          <NNParameterHighlighter
            :name="template"
            :show-prefix-and-postfix="false"
          />
        </v-col>
        <v-col cols="2">
          <strong>{{
            $t('InstanceStudiesDialog.text', { type: capitalizedType })
          }}</strong>
        </v-col>
        <v-col cols="10">
          <NNParameterHighlighter
            :name="text"
            :show-prefix-and-postfix="false"
          />
        </v-col>
      </v-row>
      <v-data-table
        class="mt-4"
        :headers="headers"
        :items="studies"
        height="40vh"
      >
        <template #[`item.redirect`]="{ item }">
          <v-btn
            class="pb-3"
            size="small"
            color="primary"
            icon="mdi-eye-arrow-right-outline"
            variant="text"
            @click="goToStudy(item)"
          />
        </template>
      </v-data-table>
    </v-card-text>
    <v-divider />
    <v-card-actions>
      <v-spacer />
      <v-btn
        color="secondary"
        variant="outlined"
        elevation="0"
        rounded
        @click="close"
      >
        {{ $t('_global.close') }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script>
import NNParameterHighlighter from '@/components/tools/NNParameterHighlighter.vue'
import { useStudiesGeneralStore } from '@/stores/studies-general'

export default {
  components: {
    NNParameterHighlighter,
  },
  props: {
    template: {
      type: String,
      default: null,
    },
    text: {
      type: String,
      default: null,
    },
    type: {
      type: String,
      default: null,
    },
    studies: {
      type: Array,
      default: null,
    },
  },
  emits: ['close'],
  setup() {
    const studiesGeneralStore = useStudiesGeneralStore()

    return {
      selectStudy: studiesGeneralStore.selectStudy,
    }
  },
  data() {
    return {
      headers: [
        {
          title: this.$t('InstanceStudiesDialog.view'),
          key: 'redirect',
          width: '5%',
        },
        {
          title: this.$t('InstanceStudiesDialog.project_id'),
          key: 'current_metadata.identification_metadata.project_number',
        },
        {
          title: this.$t('InstanceStudiesDialog.project_name'),
          key: 'current_metadata.identification_metadata.project_name',
        },
        {
          title: this.$t('InstanceStudiesDialog.brand_name'),
          key: 'current_metadata.identification_metadata.brand_name',
        },
        {
          title: this.$t('InstanceStudiesDialog.study_number'),
          key: 'current_metadata.identification_metadata.study_number',
        },
        {
          title: this.$t('InstanceStudiesDialog.study_id'),
          key: 'current_metadata.identification_metadata.study_id',
        },
        {
          title: this.$t('InstanceStudiesDialog.study_acronym'),
          key: 'current_metadata.identification_metadata.study_acronym',
        },
        {
          title: this.$t('_global.status'),
          key: 'current_metadata.version_metadata.study_status',
        },
      ],
    }
  },
  computed: {
    capitalizedType() {
      return this.type.charAt(0).toUpperCase() + this.type.slice(1)
    },
  },
  methods: {
    close() {
      this.$emit('close')
    },
    goToStudy(study) {
      this.$router.push({
        name: 'StudyPurpose',
        params: { study_id: study.uid, tab: this.type + 's' },
      })
    },
  },
}
</script>
