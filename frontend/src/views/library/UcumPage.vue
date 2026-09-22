<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('DictionaryTermTable.ucum_title') }}
      <HelpButton :help-text="$t('_help.UcumTable.general')" />
    </div>
    <DictionaryTermTable
      :codelist-uid="codelistUid"
      :dictionary-name="dictionaryName"
      :headers="headers"
      column-data-resource="dictionaries/terms"
    >
      <template #termForm="{ closeForm, open, editedTerm }">
        <UcumCodeForm
          :open="open"
          :edited-term="editedTerm"
          :codelist-uid="codelistUid"
          @close="closeForm"
        />
      </template>
    </DictionaryTermTable>
  </div>
</template>

<script>
import dictionaries from '@/api/dictionaries'
import DictionaryTermTable from '@/components/library/DictionaryTermTable.vue'
import UcumCodeForm from '@/components/library/UCUMCodeForm.vue'
import HelpButton from '@/components/tools/HelpButton.vue'

export default {
  components: {
    DictionaryTermTable,
    UcumCodeForm,
    HelpButton,
  },
  data() {
    return {
      codelistUid: null,
      dictionaryName: 'UCUM',
      headers: [
        { title: '', key: 'actions', width: '1%' },
        { title: this.$t('UCUM.code'), key: 'name' },
        { title: this.$t('UCUM.description'), key: 'definition' },
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
