<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('DictionaryTermTable.medrt_title') }}
      <HelpButton :help-text="$t('_help.MedRtTable.general')" />
    </div>
    <DictionaryTermTable
      :codelist-uid="codelistUid"
      :dictionary-name="dictionaryName"
      :headers="headers"
      column-data-resource="dictionaries/terms"
    />
  </div>
</template>

<script>
import dictionaries from '@/api/dictionaries'
import DictionaryTermTable from '@/components/library/DictionaryTermTable.vue'
import HelpButton from '@/components/tools/HelpButton.vue'

export default {
  components: {
    DictionaryTermTable,
    HelpButton,
  },
  data() {
    return {
      codelistUid: null,
      dictionaryName: 'MED-RT',
      headers: [
        { title: '', key: 'actions', width: '1%' },
        {
          title: this.$t('DictionaryTermTable.medrt_id'),
          key: 'dictionary_id',
        },
        { title: this.$t('DictionaryTermTable.class_name'), key: 'name' },
        {
          title: this.$t('DictionaryTermTable.class_name_lower_case'),
          key: 'name_sentence_case',
        },
        {
          title: this.$t('DictionaryTermTable.abbreviation'),
          key: 'abbreviation',
        },
        { title: this.$t('_global.definition'), key: 'definition' },
        { title: this.$t('_global.status'), key: 'status' },
        { title: this.$t('_global.version'), key: 'version' },
        { title: this.$t('_global.modified'), key: 'start_date' },
      ],
    }
  },
  mounted() {
    dictionaries.getCodelists(this.dictionaryName).then((resp) => {
      this.codelistUid = resp.data.items[0].codelist_uid
    })
  },
}
</script>
